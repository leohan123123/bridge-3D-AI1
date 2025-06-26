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
