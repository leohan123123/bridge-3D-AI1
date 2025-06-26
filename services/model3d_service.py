import json
from models.geometry_builder import BridgeGeometryBuilder
from generators.threejs_generator import ThreeJSGenerator

# LLM_PROMPT (as defined in the problem description)
MODEL3D_PROMPT = """
基于以下桥梁设计数据，生成完整的Three.js 3D模型代码：

设计数据：{bridge_design}
模型要求：{model_requirements}

请生成包含以下内容的Three.js代码：
1. 场景初始化和相机设置
2. 主梁几何体创建（根据截面形状和跨径）
3. 桥墩几何体创建（根据墩型和尺寸）
4. 基础几何体创建
5. 材质和纹理设置
6. 光照和渲染设置
7. 交互控制（旋转、缩放、平移）

确保几何尺寸准确，材质真实，支持基本交互操作。
"""

class Model3DService:
    def __init__(self):
        self.geometry_builder = BridgeGeometryBuilder()
        self.threejs_generator = ThreeJSGenerator()

    def _parse_llm_response_to_structured_data(self, llm_response_str: str) -> dict:
        """
        Parses the LLM's string response (expected to be JSON or convertible to JSON)
        into a structured dictionary that `generate_bridge_scene` can use.
        This is a placeholder and will need robust error handling and validation.

        The LLM is expected to return a JSON string that describes the bridge components,
        their types, dimensions, positions, and materials, guided by the MODEL3D_PROMPT.

        Example of expected LLM JSON output structure (simplified):
        {
            "scene_setup": {
                "camera_position": [10, 30, 70],
                "backgroundColor": "e0e0e0"
            },
            "girders": [
                {
                    "name": "mainGirder",
                    "type": "box", // "box", "t_girder", etc.
                    "dimensions": {"length": 50, "width": 5, "height": 3, "wall_thickness": 0.3},
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0xcccccc"}},
                    "position": [0, 10, 0]
                }
            ],
            "piers": [
                {
                    "name": "pier1",
                    "type": "cylindrical", // "cylindrical", "rectangular"
                    "dimensions": {"height": 10, "radius": 1.2}, // or {"height": 8, "width":1.5, "depth":2.0}
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0x888888"}},
                    "position": [-20, 0, 0]
                }
            ],
            "foundations": [
                {
                    "name": "foundation1",
                    "type": "pile_cap", // "pile_cap", "spread_footing"
                    "dimensions": {"length": 6, "width": 6, "height": 2},
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0x666666"}},
                    "position": [-20, -11, 0] // Position relative to pier or absolute
                }
            ]
        }
        """
        try:
            # For now, assume llm_response_str is a JSON string.
            # In a real scenario, this might involve more complex parsing if the LLM
            # doesn't strictly adhere to JSON output or if the prompt asks for code directly.
            # However, the prompt asks for Three.js code, but the architecture implies
            # the LLM provides structured data first, then our generator makes the code.
            # This function would be responsible for taking the LLM's understanding
            # of the bridge design and converting it into the structured `bridge_data`
            # that our `ThreeJSGenerator` expects.

            # If the LLM is *really* good, it might directly output the structure needed by generate_bridge_scene.
            # If the LLM is meant to output *parameters* for our geometry builder, this function is more complex.

            # Let's assume for now the LLM is tasked (via a more specific internal prompt perhaps)
            # to output the JSON structure that `generate_bridge_scene` uses, but with high-level
            # descriptions that our geometry_builder will turn into specific geometry_params.

            parsed_data = json.loads(llm_response_str)

            # --- Transformation Step ---
            # Convert LLM's conceptual components into geometry_params using BridgeGeometryBuilder
            # This is where the LLM's output (conceptual) meets our concrete geometry functions.

            final_bridge_data = {
                "scene_setup": parsed_data.get("scene_setup", {}),
                "girders": [],
                "piers": [],
                "foundations": []
            }

            for girder_desc in parsed_data.get("girders", []):
                dims = girder_desc.get("dimensions", {})
                geom_params = None
                if girder_desc.get("type") == "box":
                    geom_params = self.geometry_builder.create_box_girder(
                        length=dims.get("length", 50),
                        width=dims.get("width", 5),
                        height=dims.get("height", 3),
                        wall_thickness=dims.get("wall_thickness", 0.3)
                    )
                elif girder_desc.get("type") == "t_girder":
                    geom_params = self.geometry_builder.create_t_girder(
                        length=dims.get("length", 30),
                        flange_width=dims.get("flange_width", 3),
                        web_height=dims.get("web_height", 2),
                        thickness=dims.get("thickness", {"flange": 0.4, "web": 0.25})
                    )
                if geom_params:
                    final_bridge_data["girders"].append({
                        "name": girder_desc.get("name", "girder"),
                        "geometry_params": geom_params,
                        "material_params": girder_desc.get("material"),
                        "position": girder_desc.get("position")
                    })

            for pier_desc in parsed_data.get("piers", []):
                dims = pier_desc.get("dimensions", {})
                geom_params = self.geometry_builder.create_pier(
                    pier_type=pier_desc.get("type", "cylindrical"),
                    height=dims.get("height", 10),
                    cross_section=dims # Pass all dimensions as cross_section
                )
                if geom_params:
                     final_bridge_data["piers"].append({
                        "name": pier_desc.get("name", "pier"),
                        "geometry_params": geom_params,
                        "material_params": pier_desc.get("material"),
                        "position": pier_desc.get("position")
                    })

            for found_desc in parsed_data.get("foundations", []):
                dims = found_desc.get("dimensions", {})
                geom_params = self.geometry_builder.create_foundation(
                    foundation_type=found_desc.get("type", "pile_cap"),
                    dimensions=dims
                )
                if geom_params:
                    final_bridge_data["foundations"].append({
                        "name": found_desc.get("name", "foundation"),
                        "geometry_params": geom_params,
                        "material_params": found_desc.get("material"),
                        "position": found_desc.get("position")
                    })

            return final_bridge_data

        except json.JSONDecodeError as e:
            print(f"Error decoding LLM response: {e}")
            # Fallback or error structure
            return {"error": "Failed to parse LLM response", "details": str(e)}
        except Exception as e:
            print(f"Error processing LLM data: {e}")
            return {"error": "Failed to process LLM data", "details": str(e)}


    def generate_model_from_design(self, bridge_design_data: str, model_requirements: str) -> dict:
        """
        Orchestrates the 3D model generation.
        1. (Simulated) Call LLM with bridge_design_data and model_requirements.
        2. Parse LLM response to structured data.
        3. Use ThreeJSGenerator to generate code.
        """

        # --- 1. (Simulated) LLM Call ---
        # In a real application, this would involve an API call to an LLM.
        # For now, we'll use a placeholder response that mimics what an LLM might return
        # based on the MODEL3D_PROMPT and some example design data.
        # The LLM is prompted to produce a JSON that this service can then process.

        # This simulated response should be structured according to what
        # `_parse_llm_response_to_structured_data` expects as input.
        # This means the LLM's output should be a JSON string describing the bridge conceptually.

        # Example: If bridge_design_data was "A 50m long box girder bridge with two cylindrical piers."
        # and model_requirements was "Standard concrete material, basic lighting."
        # The LLM might (ideally) return something like this:

        simulated_llm_output_json = """
        {
            "scene_setup": {
                "camera_position": [15, 40, 80],
                "backgroundColor": "f0f0f0",
                "ambient_light_color": "404040",
                "directional_light_color": "ffffff"
            },
            "girders": [
                {
                    "name": "mainGirder",
                    "type": "box",
                    "dimensions": {"length": 50, "width": 6, "height": 3, "wall_thickness": 0.4},
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0x бетон"}},
                    "position": [0, 10, 0]
                }
            ],
            "piers": [
                {
                    "name": "pier1",
                    "type": "cylindrical",
                    "dimensions": {"height": 10, "radius": 1.0},
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0x888888"}},
                    "position": [-15, 0, 0]
                },
                {
                    "name": "pier2",
                    "type": "cylindrical",
                    "dimensions": {"height": 10, "radius": 1.0},
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0x888888"}},
                    "position": [15, 0, 0]
                }
            ],
            "foundations": [
                {
                    "name": "foundation1",
                    "type": "spread_footing",
                    "dimensions": {"length": 4, "width": 4, "height": 1.5},
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0x777777"}},
                    "position": [-15, -5.75, 0]
                },
                {
                    "name": "foundation2",
                    "type": "spread_footing",
                    "dimensions": {"length": 4, "width": 4, "height": 1.5},
                    "material": {"type": "MeshStandardMaterial", "parameters": {"color": "0x777777"}},
                    "position": [15, -5.75, 0]
                }
            ]
        }
        """
        # Replace "бетон" (concrete) with a hex color for material color.
        # This highlights a point: LLM might give semantic colors, need mapping or further processing.
        # For now, I'll assume the LLM (or a pre-processing step before this service) gives valid color codes.
        simulated_llm_output_json = simulated_llm_output_json.replace("0x бетон", "0xb0b0b0")


        # --- 2. Parse LLM response ---
        # This step converts the LLM's (simulated) JSON output into the detailed `bridge_data`
        # structure that `ThreeJSGenerator.generate_bridge_scene` expects, by calling
        # our `BridgeGeometryBuilder` methods.
        structured_bridge_data = self._parse_llm_response_to_structured_data(simulated_llm_output_json)

        if "error" in structured_bridge_data:
            return {"error": "Failed to process design data", "details": structured_bridge_data["error"]}

        # --- 3. Generate Three.js code ---
        threejs_code = self.threejs_generator.generate_bridge_scene(structured_bridge_data)

        # Prepare output (as per API spec in problem description)
        # geometry_data, material_data, scene_config would ideally be extracted
        # from structured_bridge_data or the generation process itself.
        # For now, let's pass parts of structured_bridge_data.

        # This is a simplified representation; a more detailed breakdown might be needed.
        geometry_data_summary = {
            "girders": [g.get("geometry_params") for g in structured_bridge_data.get("girders", [])],
            "piers": [p.get("geometry_params") for p in structured_bridge_data.get("piers", [])],
            "foundations": [f.get("geometry_params") for f in structured_bridge_data.get("foundations", [])]
        }
        material_data_summary = {
            "girders": [g.get("material_params") for g in structured_bridge_data.get("girders", [])],
            "piers": [p.get("material_params") for p in structured_bridge_data.get("piers", [])],
            "foundations": [f.get("material_params") for f in structured_bridge_data.get("foundations", [])]
        }
        scene_config_summary = structured_bridge_data.get("scene_setup", {})

        return {
            "threejs_code": threejs_code,
            "geometry_data": geometry_data_summary, # Or more detailed if needed
            "material_data": material_data_summary, # Or more detailed
            "scene_config": scene_config_summary
        }

# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    service = Model3DService()

    # These would typically come from an API request
    example_bridge_design = "A simple 50m box girder bridge with two cylindrical piers and spread footings."
    example_model_requirements = "Render with standard concrete materials and basic lighting. Ensure dimensions are accurate."

    output = service.generate_model_from_design(example_bridge_design, example_model_requirements)

    if "error" in output:
        print(f"Error generating model: {output['error']}")
        if "details" in output:
            print(f"Details: {output['details']}")
    else:
        print("--- Generated Three.js Code ---")
        print(output["threejs_code"])
        print("\n--- Geometry Data Summary ---")
        print(json.dumps(output["geometry_data"], indent=2))
        print("\n--- Material Data Summary ---")
        print(json.dumps(output["material_data"], indent=2))
        print("\n--- Scene Config ---")
        print(json.dumps(output["scene_config"], indent=2))

        # Save the code to a file to test with the HTML from ThreeJSGenerator test
        with open("static/js/service_test_scene.js", "w") as f:
            f.write(output["threejs_code"])
        print("\nSaved example scene to static/js/service_test_scene.js")
        print("Use static/test_bridge.html (adjust script src to 'service_test_scene.js') or create a new HTML to view.")

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Three.js Bridge Test (Service)</title>
    <style> body {{ margin: 0; }} canvas {{ display: block; }} </style>
</head>
<body>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="service_test_scene.js"></script>
</body>
</html>
        """
        with open("static/service_test_bridge.html", "w") as f:
            f.write(html_content)
        print("Created static/service_test_bridge.html to view the service_test_scene.js")
```
