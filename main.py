from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any

from services.model3d_service import Model3DService

app = FastAPI(
    title="Bridge 3D Model Generator API",
    description="API for generating Three.js 3D models of bridges based on design data.",
    version="0.1.0"
)

# Initialize services
model_service = Model3DService()

# Pydantic Models for API requests
class BridgeDesign(BaseModel):
    """
    Represents the textual description of the bridge design.
    This will be passed to the LLM (simulated).
    """
    design_description: str = Field(
        ...,
        example="A 60m long box girder bridge, 8m wide, 3m high, supported by two rectangular piers (1.5m x 2m section, 12m high) on pile cap foundations (4m x 4m x 1.5m)."
    )
    # Potentially, more structured data could be part of the design input in the future
    # e.g., specific_parameters: Dict[str, Any] = None

class ModelOptions(BaseModel):
    """
    Represents various options and requirements for the 3D model generation.
    This will also be passed to the LLM (simulated).
    """
    requirements_description: str = Field(
        ...,
        example="Generate a realistic model with concrete textures. Ensure accurate geometric representation. Include basic lighting and interactive controls."
    )
    # Example of more specific options:
    # output_format: str = Field("threejs", example="threejs")
    # detail_level: str = Field("medium", example="low|medium|high")


@app.post("/api/generate_3d_model", tags=["3D Model Generation"])
async def generate_3d_model_endpoint(design: BridgeDesign, model_options: ModelOptions):
    """
    Generates Three.js code for a 3D bridge model based on input design and options.

    - **design**: Contains the textual description of the bridge.
    - **model_options**: Contains requirements and options for the model.
    """

    # The service's generate_model_from_design method currently takes two strings:
    # 1. bridge_design_data (which is design.design_description)
    # 2. model_requirements (which is model_options.requirements_description)

    # In a more advanced setup, the `design` and `model_options` objects themselves
    # might be processed or serialized to form a more complex input for the LLM.
    # For now, we directly use the description fields.
    try:
        generated_data = model_service.generate_model_from_design(
            bridge_design_data=design.design_description,
            model_requirements=model_options.requirements_description
        )

        if "error" in generated_data:
            # Log the detailed error for server-side inspection
            # (Assuming Model3DService adds logging for its errors)
            print(f"Error generating 3D model: {generated_data.get('details')}") # Replace with logger.error if main.py gets one
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate 3D model: {generated_data.get('error', 'Unknown error from Model3DService')}"
            )

    except HTTPException as http_exc: # Re-raise HTTPException
        raise http_exc
    except Exception as e:
        # Log the unexpected error
        print(f"Unexpected error in /api/generate_3d_model: {e}") # Replace with logger.error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while generating the 3D model: {str(e)}"
        )

    return {
        "message": "3D model data generated successfully.",
        "threejs_code": generated_data.get("threejs_code"),
        "geometry_data": generated_data.get("geometry_data"),
        "material_data": generated_data.get("material_data"),
        "scene_config": generated_data.get("scene_config")
    }

@app.get("/", tags=["General"])
async def read_root():
    return {"message": "Welcome to the Bridge 3D Model Generator API. Visit /docs for API documentation."}

# To run this application:
# 1. Ensure FastAPI and Uvicorn are installed:
#    pip install fastapi uvicorn
# 2. Run Uvicorn:
#    uvicorn main:app --reload
#
# Then access the API at http://127.0.0.1:8000
# And the auto-generated docs at http://127.0.0.1:8000/docs

if __name__ == "__main__":
    import uvicorn
    # This is for direct execution, e.g. python main.py
    # However, 'uvicorn main:app --reload' is preferred for development
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
