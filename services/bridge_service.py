# Ensure project root is in sys.path for standalone execution
import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import asyncio
import json
from models.data_models import BridgeRequest, BridgeDesign
from services.llm_service import LLMService
from knowledge import bridge_knowledge
from typing import Dict, Any, Optional
import uuid
import logging
import time
import re # For more robust parsing

# Configure basic logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers: # Ensure logger is not configured multiple times
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
        try:
            extracted_params, provider = await self.llm_service.analyze_text_with_failover(
                text_to_analyze=user_requirements_text,
                prompt_template_name="extract_bridge_parameters"
            )

            if extracted_params and not extracted_params.get("error"):
                logger.info(f"Parameters successfully extracted by {provider}: {json.dumps(extracted_params, indent=2, ensure_ascii=False)}")
                return extracted_params
            else:
                # Error logging already done in LLMService, but good to log context here too
                logger.error(f"LLM analysis failed or returned error. Provider: {provider}. Details from LLM: {extracted_params}")
                return {"error": "Failed to extract parameters using LLM.", "details": extracted_params, "provider": provider}
        except Exception as e:
            logger.error(f"Unexpected error during user requirement analysis: {e}", exc_info=True)
            return {"error": "Unexpected error during analysis.", "details": str(e)}

    def refine_parameters_with_knowledge(self, llm_extracted_params: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Refining LLM extracted parameters: {llm_extracted_params}")
        refined = llm_extracted_params.copy() # Ensure we are working with a mutable copy

        bt_pref = refined.get("bridge_type_preference", "").lower()
        specific_materials = refined.get("specific_materials", "").lower()
        standardized_type = ""

        if "beam" in bt_pref or "girder" in bt_pref:
            standardized_type = "Beam Bridge"
            if "continuous" in bt_pref:
                standardized_type = "Continuous " + standardized_type
        elif "arch" in bt_pref:
            standardized_type = "Arch Bridge"
        elif "cable-stayed" in bt_pref or "cable stayed" in bt_pref:
            standardized_type = "Cable-Stayed Bridge"
        elif "suspension" in bt_pref:
            standardized_type = "Suspension Bridge"
        else:
            standardized_type = "Beam Bridge" # Default if no clear preference
            logger.info(f"No specific bridge type keyword found in '{bt_pref}', defaulting to {standardized_type}")

        if "prestressed" in bt_pref or "psc" in bt_pref or "prestressed" in specific_materials:
            if "concrete" in bt_pref or "concrete" in specific_materials:
                standardized_type = "Prestressed Concrete " + standardized_type.replace("Beam Bridge", "Girder Bridge") # More specific
            else: # Prestressed, but not specified as concrete (e.g. could be steel with PSC deck)
                 standardized_type = "Prestressed " + standardized_type
            refined["material_is_prestressed_concrete"] = True # Add a flag

        refined["standardized_bridge_type"] = standardized_type.strip()

        # Span description parsing (example, can be more sophisticated)
        span_desc = refined.get("span_length_description", "").lower()
        if not refined.get("estimated_span_meters") and span_desc: # If LLM did not provide estimated_span_meters
            match = re.search(r"(\d+\.?\d*)\s*m", span_desc) # find numbers like 100m, 100.5m
            if match:
                try:
                    refined["estimated_span_meters"] = float(match.group(1))
                    logger.info(f"Extracted estimated_span_meters '{refined['estimated_span_meters']}' from span_description '{span_desc}'")
                except ValueError:
                    logger.warning(f"Could not convert extracted span '{match.group(1)}' to float.")
            else: # Try to find just a number if "m" is not present but it's in span_length_description
                match_num_only = re.search(r"(\d+\.?\d*)", span_desc)
                if match_num_only:
                    try:
                        refined["estimated_span_meters_raw_extract"] = float(match_num_only.group(1)) # Store separately if unit is uncertain
                        logger.info(f"Extracted raw numeric span '{refined['estimated_span_meters_raw_extract']}' from span_description '{span_desc}' (unit uncertain).")
                    except ValueError:
                        pass # Ignore if not a valid number


        if refined.get("standardized_bridge_type") and bridge_knowledge.COMMON_BRIDGE_TYPES.get(refined["standardized_bridge_type"]):
            refined["knowledge_base_info"] = bridge_knowledge.COMMON_BRIDGE_TYPES[refined["standardized_bridge_type"]]

        logger.info(f"Refined parameters output: {json.dumps(refined, indent=2, ensure_ascii=False)}")
        return refined

    async def generate_preliminary_design(self, request: BridgeRequest) -> BridgeDesign:
        self.design_gen_stats["total_requests"] += 1
        start_time = time.perf_counter()

        logger.info(f"Generating preliminary design for request: UserReq='{request.user_requirements[:70]}...', Conditions='{request.project_conditions}', Constraints='{request.design_constraints}'")
        default_span_length = 50.0 # Default span if parsing fails
        default_bridge_width = 12.0 # Default width

        try:
            analyzed_params = await self.analyze_user_requirements(request.user_requirements)

            if analyzed_params.get("error"):
                logger.error(f"Analysis failed, cannot generate design. LLM Details: {analyzed_params.get('details')}")
                # Log and update stats before returning error design
                self.design_gen_stats["failed_designs"] += 1
                duration = time.perf_counter() - start_time
                self.design_gen_stats["total_design_time_s"] += duration
                logger.info(f"Preliminary design generation failed (analysis error) in {duration:.2f}s.")
                return BridgeDesign(
                    design_id=str(uuid.uuid4()), bridge_type="Error - Analysis Failed", span_lengths=[0],
                    bridge_width=0, design_load="N/A", main_girder={"error": "Analysis failed", "details": analyzed_params.get('details')},
                    pier_design={"error": "Analysis failed"}, foundation={"error": "Analysis failed"}, materials={"error": "Analysis failed"}
                )

            refined_params = self.refine_parameters_with_knowledge(analyzed_params)

            # Determine Bridge Type
            bridge_type_suggestion = request.design_constraints.get("bridge_type_preference") if request.design_constraints else None
            if not bridge_type_suggestion: # If not in constraints, use refined from LLM
                bridge_type_suggestion = refined_params.get("standardized_bridge_type", "Beam Bridge") # Default to Beam Bridge

            # Determine Span Length
            span_length = default_span_length
            span_source_text = None
            if request.design_constraints and request.design_constraints.get("span_preference_meters"):
                span_source_text = str(request.design_constraints.get("span_preference_meters"))
            elif refined_params.get("estimated_span_meters"): # Check specific LLM field first
                 span_source_text = str(refined_params.get("estimated_span_meters"))
            elif refined_params.get("span_length_description"): # Then check general description
                 span_source_text = refined_params.get("span_length_description")

            if span_source_text:
                match = re.search(r"(\d+\.?\d*)", span_source_text) # Extract first number found
                if match:
                    try:
                        parsed_span = float(match.group(1))
                        if parsed_span > 0: # Ensure positive span
                            span_length = parsed_span
                        else:
                            logger.warning(f"Parsed non-positive span '{parsed_span}' from '{span_source_text}'. Using default {default_span_length}m.")
                    except ValueError:
                        logger.warning(f"Could not parse span_length from '{span_source_text}'. Using default {default_span_length}m.")
                else:
                    logger.warning(f"No numeric span found in '{span_source_text}'. Using default {default_span_length}m.")
            else:
                logger.info(f"No span information provided or extracted. Using default span {default_span_length}m.")

            logger.info(f"Using bridge_type='{bridge_type_suggestion}', span_length='{span_length}m' for design.")

            # Determine Bridge Width
            estimated_bridge_width = default_bridge_width
            num_lanes = 0
            road_lanes_info = None
            if request.project_conditions and request.project_conditions.get("road_lanes"):
                road_lanes_info = str(request.project_conditions.get("road_lanes", "")).lower()
            elif refined_params.get("road_lanes_description"):
                road_lanes_info = str(refined_params.get("road_lanes_description", "")).lower()

            if road_lanes_info:
                logger.debug(f"Attempting to parse road lanes info: '{road_lanes_info}'")
                if "四" in road_lanes_info or "4" in road_lanes_info or "four" in road_lanes_info : num_lanes = 4
                elif "六" in road_lanes_info or "6" in road_lanes_info or "six" in road_lanes_info: num_lanes = 6
                elif "八" in road_lanes_info or "8" in road_lanes_info or "eight" in road_lanes_info: num_lanes = 8
                elif "双" in road_lanes_info or "两" in road_lanes_info or "2" in road_lanes_info or "two" in road_lanes_info: num_lanes = 2
                # Add more checks if needed, e.g., single lane

                if num_lanes > 0:
                    lane_width_m = 3.5  # Standard lane width
                    shoulder_median_width_m = 3.0 if num_lanes >= 4 else 1.5 # Simplified additional width
                    estimated_bridge_width = (num_lanes * lane_width_m) + shoulder_median_width_m
                    logger.info(f"Estimated bridge width for {num_lanes} lanes: {estimated_bridge_width}m")
                else:
                    logger.info(f"Could not parse specific number of lanes from '{road_lanes_info}'. Using default or LLM assumed width.")
                    # Fallback to LLM assumed width or default
                    estimated_bridge_width = refined_params.get("assumed_bridge_width", default_bridge_width) # LLM might provide this
            else:
                logger.info(f"No road lanes information provided. Using default width {default_bridge_width}m or LLM assumed.")
                estimated_bridge_width = refined_params.get("assumed_bridge_width", default_bridge_width)

            logger.info(f"Using estimated_bridge_width: {estimated_bridge_width}m")

            # Main Girder Type and Materials
            main_girder_type = "I-Girder" # Default
            materials_dict = {
                "concrete_grade": "C40/50",
                "steel_reinforcement": "Fe500D",
            }
            if refined_params.get("material_is_prestressed_concrete"):
                main_girder_type = "Prestressed Concrete I-Girder" # Could be Box Girder too for PSC
                materials_dict["prestressing_steel"] = "High-tensile strands Y1860S7"
                if "continuous" in bridge_type_suggestion.lower():
                     main_girder_type = "Prestressed Concrete Continuous Girder" # Example refinement
            elif "steel" in bridge_type_suggestion.lower() or "steel" in refined_params.get("specific_materials","").lower():
                main_girder_type = "Steel I-Girder" # or Steel Box Girder
                materials_dict["structural_steel_grade"] = "Q355"
                # Remove concrete specific if it's primarily steel
                if "concrete_grade" in materials_dict and "deck" not in refined_params.get("specific_materials","").lower() :
                    del materials_dict["concrete_grade"]


            design_id = str(uuid.uuid4())
            design = BridgeDesign(
                design_id=design_id,
                bridge_type=bridge_type_suggestion,
                span_lengths=[span_length], # Assuming single span for now from parsed length
                bridge_width=estimated_bridge_width,
                design_load=refined_params.get("load_requirements", "Standard Highway Load"),
                main_girder={"type": main_girder_type, "depth_m": round(span_length / 18, 2) if span_length > 0 else 2.0}, # Adjusted L/18-L/20
                pier_design={"type": "Reinforced Concrete Column", "shape": "Circular"}, # Default, can be refined
                foundation={"type": "Spread Footing or Piles (site dependent)"}, # Default
                materials=materials_dict
            )

            if request.project_conditions:
                design.main_girder["project_notes"] = f"Consider project conditions: {request.project_conditions}"
            if request.design_constraints:
                design.pier_design["constraints_notes"] = f"Adhere to design constraints: {request.design_constraints}"

            logger.info(f"Preliminary design generated successfully: ID {design.design_id}, Type {design.bridge_type}, Span {design.span_lengths[0]}m, Width {design.bridge_width}m")
            logger.debug(f"Full design details: {design.model_dump_json(indent=2)}")

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
            return BridgeDesign(
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
    # Ensure .env is loaded for standalone testing
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("--- Running Bridge Service Standalone Test ---")
    bridge_service = BridgeService()
    llm_service_stats_ref = bridge_service.llm_service

    test_cases = [
        "I need a bridge to cross a 150m wide river for heavy truck traffic. It should be a modern looking steel arch bridge.",
        "Design a 100m prestressed concrete continuous beam bridge for a highway.",
        "Short pedestrian bridge, about 20 meters, simple wood construction.",
        "Urban flyover, two lanes, concrete girder, 35m span, consider aesthetics.",
        "No idea what I want, just make something for a 60m crossing." # Test vague input
    ]

    for i, test_req_text in enumerate(test_cases):
        logger.info(f"\n--- Test Case {i+1}: Requirement Analysis for: '{test_req_text}' ---")

        # Simulate specific LLM availability for some tests if needed
        # Example: Force Ollama for one test by "breaking" DeepSeek config temporarily
        # original_deepseek_key = bridge_service.llm_service.deepseek_config.get("api_key")
        # if i == 1: # For the second test case
        #     logger.info("Simulating DeepSeek API key not configured for this specific test case.")
        #     bridge_service.llm_service.deepseek_config["api_key"] = "YOUR_DEEPSEEK_API_KEY" # Simulate placeholder

        analyzed = await bridge_service.analyze_user_requirements(test_req_text)
        logger.info(f"Analyzed Requirements Output for Test Case {i+1}:\n{json.dumps(analyzed, indent=2, ensure_ascii=False)}")

        # if i == 1: # Restore config if changed
        #    bridge_service.llm_service.deepseek_config["api_key"] = original_deepseek_key

        if not analyzed.get("error"):
            refined = bridge_service.refine_parameters_with_knowledge(analyzed)
            logger.info(f"\nRefined Parameters with Knowledge for Test Case {i+1}:\n{json.dumps(refined, indent=2, ensure_ascii=False)}")

            logger.info(f"\n--- Test Case {i+1}: Preliminary Design Generation ---")
            # Create a BridgeRequest. For simplicity, project_conditions and design_constraints are minimal here.
            # In a real scenario, these might also be derived or explicitly provided.
            sample_request = BridgeRequest(
                user_requirements=test_req_text,
                project_conditions={"example_condition": "test value"},
                design_constraints={} # LLM extracted params will primarily drive this test
            )
            if "100m" in test_req_text: # Add specific constraint for this case
                sample_request.design_constraints["span_preference_meters"] = 100
            if "prestressed concrete" in test_req_text:
                sample_request.design_constraints["bridge_type_preference"] = "Prestressed Concrete Continuous Beam Bridge"


            preliminary_design = await bridge_service.generate_preliminary_design(sample_request)
            logger.info(f"\nPreliminary Design Output for Test Case {i+1}:\n{preliminary_design.model_dump_json(indent=2)}")
        else:
            logger.warning(f"Skipping design generation for Test Case {i+1} due to analysis error.")


    # Log overall statistics
    llm_service_stats_ref.log_call_statistics()
    bridge_service.log_design_generation_stats()

    logger.info("--- Bridge Service Standalone Test Finished ---")

if __name__ == "__main__":
    # Add project root to sys.path for standalone execution
    # Already handled at the top of the file.
    asyncio.run(main_test())
