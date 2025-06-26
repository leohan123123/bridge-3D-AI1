from fastapi import FastAPI
from models import BridgeRequest # Assuming models.py is in the same directory or accessible via PYTHONPATH
from services.design_generator import DesignGenerator, BridgeDesign
from typing import List, Dict, Any # Ensure List is imported
import uvicorn

app = FastAPI(
    title="Bridge Intelligent Design System API",
    description="API for analyzing bridge design requirements and generating design proposals and schemes.",
    version="0.2.0" # Updated version
)

# Initialize services that might be reused
design_generator_service = DesignGenerator()

@app.get("/")
async def root():
    return {"message": "Welcome to the Bridge Intelligent Design System API! Version 0.2.0"}

@app.post("/api/analyze_requirements")
async def analyze_requirements(request: BridgeRequest):
    """
    Analyzes user requirements for bridge design, extracts key parameters,
    and returns a structured representation.

    This endpoint will eventually use LLM services to understand natural language
    requirements and the knowledge base for validation and suggestions.
    """
    # Placeholder for LLM-based requirement analysis and parameter extraction
    # In a real scenario, this would involve:
    # 1. Sending `request.user_requirements` (and potentially other fields) to an LLM service.
    # 2. Parsing the LLM's response to extract structured design parameters.
    # 3. Validating/augmenting these parameters using `knowledge/bridge_knowledge.py`.

    # Mock response for now
    analyzed_requirements = {
        "original_user_query": request.user_requirements,
        "parsed_intent": "Request for a new bridge design.",
        "key_elements_identified": ["river crossing", "highway traffic"], # Example
    }

    design_parameters = {
        "preliminary_bridge_type_suggestion": "Beam Bridge", # Based on mock analysis
        "estimated_span_range_meters": [50, 150], # Example
        "potential_load_class": "Standard Highway Load", # Example
        "site_conditions_summary": request.project_conditions,
        "constraints_summary": request.design_constraints
    }

    if "river" in request.user_requirements.lower():
        analyzed_requirements["key_elements_identified"].append("river")
        design_parameters["environmental_considerations"] = ["Hydrology study recommended"]
    if request.project_conditions and request.project_conditions.get("soil_type") == "soft clay":
        design_parameters["foundation_alert"] = "Soft clay may require deep foundations."


    return {"analyzed_requirements": analyzed_requirements, "design_parameters": design_parameters}

# Define a model for the generate_design endpoint request body
# This would typically be a Pydantic model for validation, similar to BridgeRequest
# For now, we'll accept a dictionary.
class DesignRequirements(BridgeRequest): # Inheriting for simplicity, can be a separate model
    span_m: float # Adding a specific field that design_generator might use
    # Add other specific fields that are crucial for design generation
    # e.g., traffic_load: str, site_geology: str etc.

@app.post("/api/generate_design", response_model=BridgeDesign)
async def generate_design(requirements: DesignRequirements) -> BridgeDesign:
    """
    Generates a detailed bridge design scheme based on the provided requirements.
    Utilizes the DesignGenerator service, which incorporates knowledge base lookups
    and simulated LLM interaction.
    """
    # The 'requirements' dict should conform to what DesignGenerator expects.
    # This might involve some transformation from the API model to the service layer model.
    # For now, we pass it as a dictionary.
    # The DesignRequirements model should ideally be structured to provide all necessary inputs.

    # Convert Pydantic model to dict for the service, or ensure service handles Pydantic.
    # The DesignGenerator's generate_design_scheme expects a Dict[str, Any].
    # requirements.dict() can convert a Pydantic model instance to a dictionary.
    requirements_dict = requirements.dict()

    # Add any other fields from BridgeRequest that might be needed if not directly in DesignRequirements
    # For example, if project_conditions and design_constraints are still separate in BridgeRequest:
    # requirements_dict["project_conditions"] = requirements.project_conditions
    # requirements_dict["design_constraints"] = requirements.design_constraints
    # However, by inheriting DesignRequirements from BridgeRequest, these are already included.

    design_scheme = design_generator_service.generate_design_scheme(requirements_dict)
    return design_scheme

# Initialize DrawingService
from services.drawing_service import DrawingService
drawing_service = DrawingService()

@app.post("/api/generate_drawings")
async def generate_drawings(design: BridgeDesign, drawing_types: List[str], scale: float = 1.0):
    """
    Generates 2D engineering drawings in SVG format based on the bridge design and drawing types.
    Supported drawing_types:
    - "bridge_elevation_view"
    - "plan_view" (placeholder)
    - "girder_section_view"
    - "pier_section_view" (placeholder for pier specific section)
    - "foundation_plan_view" (placeholder)
    - "typical_node_detail" (placeholder)
    """
    # The DrawingService will take the BridgeDesign Pydantic model (or its dict representation)
    # and generate SVG strings for the requested drawing_types.
    # For now, design.dict() will be passed.

    # The prompt's example output implies specific keys for specific drawings.
    # The drawing_service.generate_drawings currently returns a dict where keys are drawing_types.
    # We might need to adapt this if the API contract is strict about output keys like
    # "elevation_view", "plan_view", "section_views", "detail_drawings".
    # For now, let's assume the service returns a dict that can be directly returned or easily mapped.

    generated_svgs = drawing_service.generate_drawings(design.model_dump(), drawing_types, scale)

    # Based on the example response structure:
    # {
    # "elevation_view": svg_content,
    # "plan_view": svg_content,
    # "section_views": [svg_content1, svg_content2],
    # "detail_drawings": [svg_content3, svg_content4]
    # }
    # We need to map the output from drawing_service to this structure.
    # This requires knowing which drawing_types from the input correspond to which keys in the output.

    response_payload = {
        "elevation_view": None,
        "plan_view": None,
        "section_views": [],
        "detail_drawings": []
    }

    # Example mapping based on typical drawing types from the prompt.
    # This mapping logic might need refinement based on exact drawing_types strings.
    if "bridge_elevation_view" in generated_svgs: # This matches a key used in drawing_service
        response_payload["elevation_view"] = generated_svgs["bridge_elevation_view"]

    if "plan_view" in generated_svgs: # Assuming "plan_view" is a type the service can generate
        response_payload["plan_view"] = generated_svgs["plan_view"]

    # For section views, we'd collect all relevant ones.
    # These type names are examples.
    section_type_keys = ["girder_section_view", "pier_section_view", "main_beam_section_view"]
    for sec_key in section_type_keys:
        if sec_key in generated_svgs:
            response_payload["section_views"].append(generated_svgs[sec_key])

    # For detail drawings
    detail_type_keys = ["typical_node_detail", "foundation_reinforcement_detail"]
    for det_key in detail_type_keys:
        if det_key in generated_svgs:
            response_payload["detail_drawings"].append(generated_svgs[det_key])

    # Add any drawings that weren't specifically mapped, perhaps in a generic key
    # This ensures all generated drawings are returned if they don't fit the specific keys.
    # response_payload["other_drawings"] = generated_svgs # Or handle as per requirements

    # If drawing_types contains items not matching the above, they will be in generated_svgs
    # but not explicitly in the structured response_payload unless handled by a generic key.
    # For now, only specifically named keys in the response_payload are populated.
    # If a drawing type like "bridge_general_arrangement_plan" was requested and generated,
    # it needs to be mapped to "plan_view" or another appropriate field.

    return response_payload


@app.post("/api/optimize_design")
async def optimize_design(current_design: BridgeDesign, optimization_goals: List[str]):
    """
    Optimizes an existing bridge design based on specified goals.
    This is a placeholder and would involve significant LLM interaction and engineering logic.
    """
    # In a real implementation:
    # 1. Format `current_design` and `optimization_goals` into a prompt (e.g., using OPTIMIZATION_PROMPT_TEMPLATE).
    # 2. Call an LLM service with the prompt.
    # 3. Parse the LLM response.
    # 4. Potentially perform calculations and verifications on the optimized design.

    # Placeholder response
    return {
        "optimized_design_summary": {
            "changes_proposed": f"Reduce material usage by 10% based on goals: {', '.join(optimization_goals)} (simulated).",
            "original_type": current_design.get("bridge_type_selection", {}).get("type", "N/A")
        },
        "optimization_notes": [
            "Further structural analysis required for optimized design.",
            "Cost savings estimated at 5% (simulated)."
        ],
        "original_design_received": current_design # Echoing back for confirmation
    }


if __name__ == "__main__":
    # This is for running the app directly using Uvicorn, for development.
    # For production, you might use a different command (e.g., via Gunicorn).
    uvicorn.run(app, host="0.0.0.0", port=8000)
