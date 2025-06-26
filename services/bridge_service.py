from models import BridgeRequest, BridgeDesign
from services.llm_service import LLMService # Assuming LLMService is in the same directory
from knowledge import bridge_knowledge # Assuming bridge_knowledge.py is in knowledge directory
from typing import Dict, Any, Optional
import uuid

class BridgeService:
    def __init__(self):
        self.llm_service = LLMService() # For more complex interpretations or suggestions
        # self.knowledge_base = bridge_knowledge.load_knowledge() # If knowledge is loaded from a file or DB

    async def analyze_user_requirements(self, user_requirements_text: str) -> Dict[str, Any]:
        """
        Uses LLMService to parse user's natural language requirements into structured parameters.
        """
        print(f"BridgeService: Analyzing user requirements: '{user_requirements_text[:100]}...'")

        # Use the specific prompt template for parameter extraction
        extracted_params, provider = await self.llm_service.analyze_text_with_failover(
            text_to_analyze=user_requirements_text,
            prompt_template_name="extract_bridge_parameters"
        )

        if extracted_params and not extracted_params.get("error"):
            print(f"BridgeService: Parameters extracted by {provider}: {extracted_params}")
            # Further validation or refinement using bridge_knowledge could happen here
            # For example, if LLM suggests a span_length_description, try to convert to numeric range
            # refined_params = self.refine_parameters_with_knowledge(extracted_params)
            # return refined_params
            return extracted_params
        else:
            print(f"BridgeService: LLM analysis failed or returned error. Details: {extracted_params}")
            return {"error": "Failed to extract parameters using LLM.", "details": extracted_params, "provider": provider}

    def refine_parameters_with_knowledge(self, llm_extracted_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refines parameters extracted by LLM using the professional knowledge base.
        Example: Convert textual descriptions to quantitative values, validate constraints.
        """
        refined = llm_extracted_params.copy()

        # Example: Standardize bridge type
        bt_pref = refined.get("bridge_type_preference", "").lower()
        if "beam" in bt_pref or "girder" in bt_pref:
            refined["standardized_bridge_type"] = "Beam Bridge"
        elif "arch" in bt_pref:
            refined["standardized_bridge_type"] = "Arch Bridge"
        elif "suspension" in bt_pref:
            refined["standardized_bridge_type"] = "Suspension Bridge"
        elif "cable-stayed" in bt_pref or "cable stayed" in bt_pref:
            refined["standardized_bridge_type"] = "Cable-Stayed Bridge"

        # Example: Infer span category from description
        span_desc = refined.get("span_length_description", "").lower()
        if "short" in span_desc or "pedestrian" in span_desc or "small" in span_desc:
            if "50m" in span_desc or "fifty meters" in span_desc:
                 refined["estimated_span_meters"] = "~50m"
                 refined["span_category"] = "Short"
            elif "100m" in span_desc:
                refined["estimated_span_meters"] = "~100m"
                refined["span_category"] = "Short to Medium"
            else:
                refined["span_category"] = "Short"

        elif "long" in span_desc or "river" in span_desc or "wide" in span_desc:
            if "500m" in span_desc:
                refined["estimated_span_meters"] = "~500m"
                refined["span_category"] = "Long"
            else:
                refined["span_category"] = "Long"

        # Accessing knowledge from bridge_knowledge.py
        # This is a simplified example. Real knowledge base would be more structured.
        if refined.get("standardized_bridge_type") and bridge_knowledge.COMMON_BRIDGE_TYPES.get(refined["standardized_bridge_type"]):
            refined["knowledge_base_info"] = bridge_knowledge.COMMON_BRIDGE_TYPES[refined["standardized_bridge_type"]]

        return refined

    async def generate_preliminary_design(self, request: BridgeRequest) -> BridgeDesign:
        """
        Generates a preliminary bridge design based on the analyzed requirements.
        This is a high-level placeholder. A real implementation would involve
        complex engineering logic, calculations, and iterative refinement.
        """
        print(f"BridgeService: Generating preliminary design for request: {request.user_requirements[:50]}...")

        # 1. Analyze requirements using LLM (if not already done or to re-confirm)
        analyzed_params = await self.analyze_user_requirements(request.user_requirements)
        if analyzed_params.get("error"):
            # Handle error, maybe return a default/error BridgeDesign or raise exception
            print(f"Error in analysis, cannot generate design: {analyzed_params.get('details')}")
            # Fallback to a very basic design or raise an error
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
        print(f"BridgeService: Refined parameters for design: {refined_params}")

        # 2. Use refined_params and bridge_knowledge to determine design specifics
        # This is highly simplified.
        bridge_type_suggestion = refined_params.get("standardized_bridge_type", "Beam Bridge")
        span_suggestion_text = refined_params.get("estimated_span_meters", "100m") # e.g. "~100m"

        # Basic parsing of span length
        try:
            # Attempt to extract a number from span_suggestion_text
            span_length = float(''.join(filter(str.isdigit, span_suggestion_text.split('m')[0]))) if 'm' in span_suggestion_text else 100.0
        except ValueError:
            span_length = 100.0 # Default if parsing fails


        # Mock design generation based on simplified logic
        design = BridgeDesign(
            design_id=str(uuid.uuid4()),
            bridge_type=bridge_type_suggestion,
            span_lengths=[span_length], # Example, could be more complex based on analysis
            bridge_width=refined_params.get("assumed_bridge_width", 12.0), # Default or from params
            design_load=refined_params.get("load_requirements", "Standard Highway Load"),
            main_girder={"type": "Prestressed Concrete I-Girder", "depth_m": span_length / 20}, # Rule of thumb
            pier_design={"type": "Reinforced Concrete Column", "shape": "Circular"},
            foundation={"type": "Spread Footing or Piles (site dependent)"},
            materials={
                "concrete_grade": "C40/50",
                "steel_reinforcement": "Fe500D",
                "prestressing_steel": "High-tensile strands"
            }
        )

        # Augment with project conditions and constraints if provided
        if request.project_conditions:
            design.main_girder["project_notes"] = f"Consider conditions: {request.project_conditions}"
        if request.design_constraints:
            design.pier_design["constraints_notes"] = f"Adhere to constraints: {request.design_constraints}"

        print(f"BridgeService: Preliminary design generated: ID {design.design_id}, Type {design.bridge_type}")
        return design

# Example Usage (async context needed)
async def main_test():
    bridge_service = BridgeService()

    # Test requirement analysis
    test_requirements = "I need a bridge to cross a 150m wide river for heavy truck traffic. It should be a modern looking steel arch bridge."
    print(f"\n--- Testing Requirement Analysis for: '{test_requirements}' ---")
    analyzed = await bridge_service.analyze_user_requirements(test_requirements)
    print("Analyzed Requirements Output:")
    import json
    print(json.dumps(analyzed, indent=2))

    if not analyzed.get("error"):
        refined = bridge_service.refine_parameters_with_knowledge(analyzed)
        print("\nRefined Parameters with Knowledge:")
        print(json.dumps(refined, indent=2))


    # Test preliminary design generation
    print(f"\n--- Testing Preliminary Design Generation ---")
    sample_request = BridgeRequest(
        user_requirements="Design a pedestrian bridge over a small creek, about 25 meters long. Keep it simple and low cost. Maybe a beam bridge.",
        project_conditions={"soil_type": "good bearing capacity", "access": "easy"},
        design_constraints={"max_construction_time_weeks": 12}
    )

    # Temporarily disable DeepSeek for local testing if key is not set
    # original_deepseek_key = bridge_service.llm_service.deepseek_config.get("api_key")
    # if bridge_service.llm_service.deepseek_config.get("api_key") == "YOUR_DEEPSEEK_API_KEY":
    #    bridge_service.llm_service.deepseek_config["api_key"] = None # Disable DeepSeek for this test

    preliminary_design = await bridge_service.generate_preliminary_design(sample_request)

    # if bridge_service.llm_service.deepseek_config.get("api_key") is None: # Restore if changed
    #    bridge_service.llm_service.deepseek_config["api_key"] = original_deepseek_key

    print("\nPreliminary Design Output:")
    print(preliminary_design.model_dump_json(indent=2))

if __name__ == "__main__":
    import asyncio
    # To run this test:
    # Make sure config.py is set up and Ollama is running if DeepSeek key is not available.
    # Run `python -m services.bridge_service` from the project root.
    # (You might need to adjust PYTHONPATH: `export PYTHONPATH=.`)
    print("Running Bridge Service standalone test...")
    asyncio.run(main_test())
