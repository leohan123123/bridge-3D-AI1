# Ensure project root is in sys.path for standalone execution
import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import asyncio # Added for main_test
import json # Added for main_test json.dumps
from models import BridgeRequest, BridgeDesign
from services.llm_service import LLMService
from knowledge import bridge_knowledge
from typing import Dict, Any, Optional
import uuid
import logging
import time # Added for performance counter

# Configure basic logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class BridgeService:
    def __init__(self):
        logger.info("Initializing BridgeService.")
        self.llm_service = LLMService()
        self.design_gen_stats = {"total_requests": 0, "successful_designs": 0, "failed_designs": 0, "total_design_time_s": 0.0}
        # self.knowledge_base = bridge_knowledge.load_knowledge() # If needed

    async def analyze_user_requirements(self, user_requirements_text: str) -> Dict[str, Any]:
        logger.info(f"Analyzing user requirements: '{user_requirements_text[:100]}...'")
        # This method's timing is part of LLMService timing if it's the main consumer of time.
        # If there's significant pre/post processing here, it could be timed separately.
        try:
            extracted_params, provider = await self.llm_service.analyze_text_with_failover(
                text_to_analyze=user_requirements_text,
                prompt_template_name="extract_bridge_parameters"
            )

            if extracted_params and not extracted_params.get("error"):
                logger.info(f"Parameters successfully extracted by {provider}: {extracted_params}")
                return extracted_params
            else:
                logger.error(f"LLM analysis failed or returned error. Provider: {provider}. Details: {extracted_params}")
                return {"error": "Failed to extract parameters using LLM.", "details": extracted_params, "provider": provider}
        except Exception as e:
            logger.error(f"Unexpected error during user requirement analysis: {e}", exc_info=True)
            return {"error": "Unexpected error during analysis.", "details": str(e)}

    def refine_parameters_with_knowledge(self, llm_extracted_params: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Refining LLM extracted parameters: {llm_extracted_params}")
        refined = llm_extracted_params.copy()

        bt_pref = refined.get("bridge_type_preference", "").lower()
        if "beam" in bt_pref or "girder" in bt_pref:
            refined["standardized_bridge_type"] = "Beam Bridge"
        elif "arch" in bt_pref:
            refined["standardized_bridge_type"] = "Arch Bridge"
        # ... (other type standardizations) ...

        span_desc = refined.get("span_length_description", "").lower()
        # ... (span category logic) ...

        if refined.get("standardized_bridge_type") and bridge_knowledge.COMMON_BRIDGE_TYPES.get(refined["standardized_bridge_type"]):
            refined["knowledge_base_info"] = bridge_knowledge.COMMON_BRIDGE_TYPES[refined["standardized_bridge_type"]]

        logger.info(f"Refined parameters: {refined}")
        return refined

    async def generate_preliminary_design(self, request: BridgeRequest) -> BridgeDesign:
        self.design_gen_stats["total_requests"] += 1
        start_time = time.perf_counter() # For overall design generation time

        logger.info(f"Generating preliminary design for request: UserReq='{request.user_requirements[:50]}...', Conditions='{request.project_conditions}', Constraints='{request.design_constraints}'")

        try:
            analyzed_params = await self.analyze_user_requirements(request.user_requirements) # LLMService call is timed internally

            if analyzed_params.get("error"):
                logger.error(f"Analysis failed, cannot generate design. Details: {analyzed_params.get('details')}")
                self.design_gen_stats["failed_designs"] += 1
                duration = time.perf_counter() - start_time
                self.design_gen_stats["total_design_time_s"] += duration
                logger.info(f"Preliminary design generation failed (analysis error) in {duration:.2f}s.")
                return BridgeDesign(
                    design_id=str(uuid.uuid4()),
                    bridge_type="Error - Analysis Failed",
                    span_lengths=[0],
                    bridge_width=0,
                    design_load="N/A",
                    main_girder={"error": "Analysis failed"},
                    pier_design={"error": "Analysis failed"},
                    foundation={"error": "Analysis failed"},
                    materials={"error": "Analysis failed"}
                )

            refined_params = self.refine_parameters_with_knowledge(analyzed_params)
            logger.info(f"Refined parameters for design: {refined_params}")

            bridge_type_suggestion = request.design_constraints.get("bridge_type_preference") if request.design_constraints else None
            if not bridge_type_suggestion:
                bridge_type_suggestion = refined_params.get("standardized_bridge_type", "Beam Bridge")

            span_suggestion_text = refined_params.get("estimated_span_meters", "100m")
            if request.design_constraints and request.design_constraints.get("span_preference_meters"):
                span_suggestion_text = str(request.design_constraints.get("span_preference_meters")) + "m"

            try:
                span_length = float(''.join(filter(str.isdigit, span_suggestion_text.split('m')[0]))) if 'm' in span_suggestion_text else 100.0
            except ValueError:
                logger.warning(f"Could not parse span_length from '{span_suggestion_text}'. Defaulting to 100.0m.")
                span_length = 100.0

            logger.info(f"Using bridge_type='{bridge_type_suggestion}', span_length='{span_length}m' for design.")

            estimated_bridge_width = 12.0
            num_lanes = 0
            road_lanes_info = None
            if request.project_conditions and request.project_conditions.get("road_lanes"):
                road_lanes_info = request.project_conditions.get("road_lanes")
            elif refined_params.get("road_lanes_description"):
                road_lanes_info = refined_params.get("road_lanes_description")

            if road_lanes_info:
                logger.debug(f"Parsing road lanes info: '{road_lanes_info}'")
                if "四" in road_lanes_info or "4" in road_lanes_info or "four" in road_lanes_info.lower(): num_lanes = 4
                elif "双" in road_lanes_info or "两" in road_lanes_info or "2" in road_lanes_info or "two" in road_lanes_info.lower(): num_lanes = 2
                elif "六" in road_lanes_info or "6" in road_lanes_info or "six" in road_lanes_info.lower(): num_lanes = 6

            if num_lanes > 0:
                lane_width_m = 3.5
                additional_width_m = 3.0 if num_lanes >= 4 else 1.5
                estimated_bridge_width = (num_lanes * lane_width_m) + additional_width_m
                logger.info(f"Estimated bridge width for {num_lanes} lanes: {estimated_bridge_width}m")
            else:
                estimated_bridge_width = refined_params.get("assumed_bridge_width", 12.0)
                logger.info(f"Using default or LLM assumed bridge width: {estimated_bridge_width}m")

            design_id = str(uuid.uuid4())
            design = BridgeDesign(
                design_id=design_id,
                bridge_type=bridge_type_suggestion,
                span_lengths=[span_length],
                bridge_width=estimated_bridge_width,
                design_load=refined_params.get("load_requirements", "Standard Highway Load"),
                main_girder={"type": "Prestressed Concrete I-Girder", "depth_m": span_length / 20 if span_length > 0 else 1.0},
                pier_design={"type": "Reinforced Concrete Column", "shape": "Circular"},
                foundation={"type": "Spread Footing or Piles (site dependent)"},
                materials={
                    "concrete_grade": "C40/50",
                    "steel_reinforcement": "Fe500D",
                    "prestressing_steel": "High-tensile strands"
                }
            )

            if request.project_conditions:
                design.main_girder["project_notes"] = f"Consider conditions: {request.project_conditions}"
            if request.design_constraints:
                design.pier_design["constraints_notes"] = f"Adhere to constraints: {request.design_constraints}"

            logger.info(f"Preliminary design generated successfully: ID {design.design_id}, Type {design.bridge_type}, Span {design.span_lengths[0]}m, Width {design.bridge_width}m")

            self.design_gen_stats["successful_designs"] += 1
            duration = time.perf_counter() - start_time
            self.design_gen_stats["total_design_time_s"] += duration
            logger.info(f"Preliminary design generation successful in {duration:.2f}s.")
            return design

        except Exception as e:
            logger.error(f"Unexpected error during preliminary design generation: {e}", exc_info=True)
            self.design_gen_stats["failed_designs"] += 1
            duration = time.perf_counter() - start_time
            self.design_gen_stats["total_design_time_s"] += duration
            logger.info(f"Preliminary design generation failed (unexpected error) in {duration:.2f}s.")
            return BridgeDesign( # Fallback to error design
                design_id=str(uuid.uuid4()), bridge_type="Error - Unexpected Failure", span_lengths=[0], bridge_width=0,
                design_load="N/A", main_girder={"error": str(e)}, pier_design={"error": str(e)},
                foundation={"error": str(e)}, materials={"error": str(e)}
            )

    def log_design_generation_stats(self):
        logger.info("Bridge Design Generation Statistics:")
        logger.info(f"  Total Requests: {self.design_gen_stats['total_requests']}")
        logger.info(f"  Successful Designs: {self.design_gen_stats['successful_designs']}")
        logger.info(f"  Failed Designs: {self.design_gen_stats['failed_designs']}")
        avg_time = (self.design_gen_stats['total_design_time_s'] / self.design_gen_stats['total_requests']) if self.design_gen_stats['total_requests'] > 0 else 0
        logger.info(f"  Total Design Time: {self.design_gen_stats['total_design_time_s']:.2f}s")
        logger.info(f"  Average Time Per Request: {avg_time:.2f}s")


async def main_test():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("--- Running Bridge Service Standalone Test ---")
    bridge_service = BridgeService()
    # Access LLMService stats through bridge_service instance for consolidated logging
    llm_service_stats_ref = bridge_service.llm_service

    test_requirements_text = "I need a bridge to cross a 150m wide river for heavy truck traffic. It should be a modern looking steel arch bridge."
    logger.info(f"\n--- Testing Requirement Analysis for: '{test_requirements_text}' ---")

    # Temporarily disable DeepSeek for testing if key is not set
    original_deepseek_key = bridge_service.llm_service.deepseek_config.get("api_key")
    original_ollama_url = bridge_service.llm_service.ollama_config.get("base_url")
    if bridge_service.llm_service.deepseek_config.get("api_key") == "YOUR_DEEPSEEK_API_KEY":
       logger.info("Simulating DeepSeek API key not configured for test.")
       bridge_service.llm_service.deepseek_config["api_key"] = None
    # Simulate Ollama down
    logger.info("Simulating Ollama server down for test.")
    bridge_service.llm_service.ollama_config["base_url"] = "http://localhost:1111"


    analyzed = await bridge_service.analyze_user_requirements(test_requirements_text)
    logger.info(f"Analyzed Requirements Output:\n{json.dumps(analyzed, indent=2, ensure_ascii=False)}")

    if not analyzed.get("error"):
        refined = bridge_service.refine_parameters_with_knowledge(analyzed)
        logger.info(f"\nRefined Parameters with Knowledge:\n{json.dumps(refined, indent=2, ensure_ascii=False)}")

    logger.info(f"\n--- Testing Preliminary Design Generation ---")
    sample_request = BridgeRequest(
        user_requirements="Design a pedestrian bridge over a small creek, about 25 meters long. Keep it simple and low cost. Maybe a beam bridge. It's in seismic zone 7.",
        project_conditions={"soil_type": "good bearing capacity", "access": "easy", "seismic_intensity": "7度", "road_lanes": "pedestrian only"},
        design_constraints={"max_construction_time_weeks": 12, "bridge_type_preference": "Simple Beam Bridge", "span_preference_meters": 25}
    )

    preliminary_design = await bridge_service.generate_preliminary_design(sample_request)
    logger.info(f"\nPreliminary Design Output:\n{preliminary_design.model_dump_json(indent=2)}")

    # Restore LLMService config
    bridge_service.llm_service.deepseek_config["api_key"] = original_deepseek_key
    bridge_service.llm_service.ollama_config["base_url"] = original_ollama_url

    # Log statistics
    llm_service_stats_ref.log_call_statistics()
    bridge_service.log_design_generation_stats()

    logger.info("--- Bridge Service Standalone Test Finished ---")

if __name__ == "__main__":
    # Add project root to sys.path for standalone execution
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    try:
        from config import LLM_CONFIG # Test if other root-level imports now work
        from models import BridgeRequest # Test if sibling package imports work
    except ImportError:
        print("Failed to re-import config/models. Ensure PYTHONPATH or execution context is correct.")

    asyncio.run(main_test())
