import asyncio
from flask import Flask, render_template, jsonify, request, send_file
import logging
import uuid
import io # For sending file-like objects

# Project imports
from models.data_models import BridgeRequest, BridgeDesign
from services.bridge_service import BridgeService
from generators.svg_generator import SVGGenerator
from generators.threejs_generator import ThreeJSGenerator # Or your GLTFGenerator if created

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
bridge_service = BridgeService()
svg_generator = SVGGenerator()
# Assuming ThreeJSGenerator is used for JSON scene description as per plan (Option B)
model_generator = ThreeJSGenerator() # Replace with GLTFGenerator if that path is taken

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/v1/generate_design', methods=['POST'])
def generate_design_api(): # Changed to sync
    """
    Generates a preliminary bridge design based on user requirements.
    This endpoint now handles the initial analysis and design generation.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        user_requirements = data.get("user_requirements")
        project_conditions = data.get("project_conditions")
        design_constraints = data.get("design_constraints")

        if not user_requirements:
            return jsonify({"error": "Missing 'user_requirements' in request body"}), 400

        bridge_request_data = BridgeRequest(
            user_requirements=user_requirements,
            project_conditions=project_conditions if project_conditions else {},
            design_constraints=design_constraints if design_constraints else {}
        )

        logger.info(f"API: Received for design generation: {bridge_request_data.model_dump_json(indent=2)}")

        # BridgeService.generate_preliminary_design is an async function
        # Run the async function in a sync context
        design_data_model: BridgeDesign = asyncio.run(bridge_service.generate_preliminary_design(bridge_request_data))

        if "error" in design_data_model.bridge_type.lower() or (design_data_model.main_girder and "error" in design_data_model.main_girder):
             logger.error(f"Design generation failed: {design_data_model.model_dump_json(indent=2)}")
             return jsonify({"error": "Failed to generate design", "details": design_data_model.model_dump_json()}), 500

        logger.info(f"API: Preliminary design generated successfully: ID {design_data_model.design_id}")
        return jsonify({
            "design_id": design_data_model.design_id,
            "design_data": design_data_model.model_dump(), # Send the full design data back
            "message": "Preliminary design generated successfully."
        }), 200

    except Exception as e:
        logger.error(f"API Error in /generate_design: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred on the server.", "details": str(e)}), 500

@app.route('/api/v1/generate_2d_drawing', methods=['POST'])
def generate_2d_drawing_api():
    """
    Generates a 2D SVG drawing based on the provided design data.
    """
    try:
        data = request.json
        if not data or "design_data" not in data:
            return jsonify({"error": "Missing 'design_data' in request body"}), 400

        design_data_dict = data["design_data"]
        # Validate if design_data_dict can be parsed into BridgeDesign, or trust it for now
        # For robustness, one might do: BridgeDesign.model_validate(design_data_dict)

        logger.info(f"API: Received for 2D drawing generation with design_id: {design_data_dict.get('design_id')}")

        # Generate a simple elevation view for now
        # Assumes design_data_dict has necessary fields like span_lengths, bridge_type, etc.
        svg_content = svg_generator.generate_bridge_elevation(design_data_dict)
        # In a more complex scenario, you might generate multiple SVGs (elevation, section)
        # and return them, or a link to them.

        if not svg_content or "<svg" not in svg_content: # Basic check
            logger.error("SVG generation failed or produced empty content.")
            return jsonify({"error": "Failed to generate 2D drawing content"}), 500

        logger.info(f"API: 2D SVG drawing generated successfully for design_id: {design_data_dict.get('design_id')}")
        return jsonify({
            "drawing_id": str(uuid.uuid4()), # Generate a new ID for this drawing artifact
            "svg_content": svg_content,
            "format": "svg",
            "based_on_design_id": design_data_dict.get("design_id")
        }), 200

    except Exception as e:
        logger.error(f"API Error in /generate_2d_drawing: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while generating 2D drawing.", "details": str(e)}), 500

@app.route('/api/v1/generate_3d_model_data', methods=['POST'])
def generate_3d_model_data_api():
    """
    Generates 3D model data (JSON scene description for Three.js) based on design data.
    """
    try:
        data = request.json
        if not data or "design_data" not in data:
            return jsonify({"error": "Missing 'design_data' in request body"}), 400

        design_data_dict = data["design_data"]
        logger.info(f"API: Received for 3D model data generation with design_id: {design_data_dict.get('design_id')}")

        # model_generator is ThreeJSGenerator instance
        # It expects a dictionary structure that it can convert to JS scene code
        # For Option B (JSON scene description), we'll make it generate a JSON object.
        # This requires ThreeJSGenerator to have a method like `generate_scene_json`.
        # For now, let's assume `generate_bridge_scene` is adapted or a new method is added.
        # If `generate_bridge_scene` still returns JS code, we'd need to adjust the plan or the generator.
        # Let's assume `model_generator.generate_scene_json(design_data_dict)`

        # Quick adaptation: If ThreeJSGenerator still makes JS code, we can't directly use it as JSON.
        # model_generator is an instance of ThreeJSGenerator
        # Call the generate_scene_data method which returns a dictionary
        scene_json_data = model_generator.generate_scene_data(design_data_dict)

        if not scene_json_data: # Check if the data itself is None or empty (though get("error") is better for specific error reporting)
            logger.error(f"3D model data generation failed: {scene_json_data.get('error', 'Unknown reason')}")
            return jsonify({"error": "Failed to generate 3D model data", "details": scene_json_data.get("error")}), 500

        logger.info(f"API: 3D model data (JSON scene) generated for design_id: {design_data_dict.get('design_id')}")
        return jsonify({
            "model_id": str(uuid.uuid4()),
            "model_data": scene_json_data, # This should be the JSON scene description
            "format": "json_scene_description", # Or "gltf_buffer" if using GLTF
            "based_on_design_id": design_data_dict.get("design_id")
        }), 200

    except Exception as e:
        logger.error(f"API Error in /generate_3d_model_data: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while generating 3D model data.", "details": str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    # Load environment variables from .env file for local development
    # This is for Phase 3, but good to have the import structure early
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded .env file")
    except ImportError:
        logger.info(".env file not loaded (python-dotenv not installed or no .env file). Relying on system environment variables.")

    # Note: Flask's app.run() is not suitable for async routes if they are not handled correctly.
    # For `async def` routes with Flask, you typically need an ASGI server like Hypercorn or Uvicorn,
    # or to use `asyncio.run()` within the route if it's a simple case.
    # However, `bridge_service.generate_preliminary_design` is async.
    # A simple way to run this with Flask's dev server is to wrap the async call.
    # This is a common workaround for Flask dev server. Gunicorn in Docker will handle it.

    # Modifying the generate_design_api to be synchronous for Flask dev server compatibility
    # The `await` keyword was used, which means this needs to be run with an async server or handled.
    # For simplicity in this step, I will remove 'async' from 'generate_design_api'
    # and use `asyncio.run()` for the async call. This is okay for dev.

    # Re-defining the async endpoint to be sync for Flask dev server
    # This is a common pattern: the Flask route itself is sync, but it calls async code.
    original_generate_design_api = generate_design_api # save the async version

    @app.route('/api/v1/generate_design', methods=['POST']) # Overwrite the previous async one for Flask dev server
    def generate_design_api_sync():
        return asyncio.run(original_generate_design_api())

    # The original async definition of generate_design_api will be used by Gunicorn in Docker.
    # For Flask dev server, we use the sync wrapper.
    # This is a bit of a hack. Ideally, use an ASGI server like uvicorn for local dev too.
    # For now, this allows `python app.py` to run.
    # Gunicorn in the Dockerfile will correctly handle the `async def` route.
    # Let's ensure the app instance for Gunicorn points to the one with the async route.
    # The current structure should be fine as Gunicorn will import the module and see the async def.
    # The redefinition above is only for `if __name__ == '__main__':`

    app.run(debug=True, host="0.0.0.0", port=5000)
