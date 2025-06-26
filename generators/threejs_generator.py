import json

class ThreeJSGenerator:
    def _format_args(self, args_list):
        """Helper to format arguments for JavaScript code."""
        return ", ".join(map(str, args_list))

    def generate_geometry_code(self, geometry_data: dict) -> str:
        """
        Generates Three.js code for a single geometry component.
        geometry_data is expected to be a dictionary like those produced by BridgeGeometryBuilder.
        Example: {"type": "BoxGeometry", "args": [10, 2, 3]}
                 {"type": "CylinderGeometry", "args": [1, 1, 5, 32]}
        """
        geom_type = geometry_data.get("type", "BoxGeometry")
        geom_args = self._format_args(geometry_data.get("args", [1, 1, 1]))

        # Variable name for the geometry, e.g., "boxGeometry" from "BoxGeometry"
        var_name = geom_type[0].lower() + geom_type[1:]

        return f"const {var_name} = new THREE.{geom_type}({geom_args});"

    def generate_mesh_code(self, geometry_var_name: str, material_var_name: str, mesh_name: str, position: list = None, rotation: list = None) -> str:
        """
        Generates Three.js code for a mesh.
        """
        code = f"const {mesh_name} = new THREE.Mesh({geometry_var_name}, {material_var_name});\n"
        if position:
            code += f"{mesh_name}.position.set({position[0]}, {position[1]}, {position[2]});\n"
        if rotation:
            code += f"{mesh_name}.rotation.set({rotation[0]}, {rotation[1]}, {rotation[2]});\n"
        code += f"scene.add({mesh_name});\n"
        return code

    def generate_material_code(self, material_data: dict) -> str:
        """
        Generates Three.js code for a material.
        Example: {"type": "MeshStandardMaterial", "parameters": {"color": "0x808080", "roughness": 0.5}}
        """
        mat_type = material_data.get("type", "MeshStandardMaterial")
        # Correctly format parameters for JavaScript object
        mat_params_list = []
        for key, value in material_data.get("parameters", {}).items():
            if isinstance(value, str) and not value.startswith("0x"): # if it's a string but not a hex color
                mat_params_list.append(f'{key}: "{value}"')
            else:
                mat_params_list.append(f'{key}: {value}')
        mat_params_str = "{" + ", ".join(mat_params_list) + "}"

        var_name = material_data.get("name", mat_type[0].lower() + mat_type[1:])

        return f"const {var_name} = new THREE.{mat_type}({mat_params_str});"

    def generate_bridge_scene(self, bridge_data: dict) -> str:
        """
        Generates a complete Three.js scene code string for a bridge.
        'bridge_data' should be a dictionary containing lists of components like
        'girders', 'piers', 'foundations', each with their geometry and material info.

        Example bridge_data structure:
        {
            "girders": [
                {
                    "name": "mainGirder",
                    "geometry_params": {"type": "BoxGeometry", "args": [50, 3, 2]}, // from BridgeGeometryBuilder
                    "material_params": {"type": "MeshStandardMaterial", "parameters": {"color": "0xcccccc"}},
                    "position": [0, 10, 0]
                }
            ],
            "piers": [
                {
                    "name": "pier1",
                    "geometry_params": {"type": "CylinderGeometry", "args": [1, 1, 10, 32]},
                    "material_params": {"type": "MeshStandardMaterial", "parameters": {"color": "0x888888"}},
                    "position": [-20, 0, 0]
                },
                {
                    "name": "pier2",
                    "geometry_params": {"type": "CylinderGeometry", "args": [1, 1, 10, 32]},
                    "material_params": {"type": "MeshStandardMaterial", "parameters": {"color": "0x888888"}},
                    "position": [20, 0, 0]
                }
            ],
            "foundations": [ ... ],
            "scene_setup": { ... } // Optional: camera, lights, controls
        }
        """

        scene_setup = bridge_data.get("scene_setup", {})

        # Scene, Camera, Renderer (Basic Setup)
        js_code = f"""
// Scene, Camera, Renderer
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x{scene_setup.get("backgroundColor", "f0f0f0")});

const camera = new THREE.PerspectiveCamera(
    {scene_setup.get("camera_fov", 75)},
    window.innerWidth / window.innerHeight,
    {scene_setup.get("camera_near", 0.1)},
    {scene_setup.get("camera_far", 1000)}
);
camera.position.set({', '.join(map(str, scene_setup.get("camera_position", [0, 20, 50])))});
camera.lookAt(0,0,0);

const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0x{scene_setup.get("ambient_light_color", "404040")}, {scene_setup.get("ambient_light_intensity", 1.0)});
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0x{scene_setup.get("directional_light_color", "ffffff")}, {scene_setup.get("directional_light_intensity", 0.8)});
directionalLight.position.set({', '.join(map(str, scene_setup.get("directional_light_position", [50, 50, 50])))});
scene.add(directionalLight);

// Controls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.25;
controls.screenSpacePanning = false;
controls.maxPolarAngle = Math.PI / 2;

// Materials (common or default)
{self.generate_material_code({"name": "defaultMaterial", "type": "MeshStandardMaterial", "parameters": {"color": "0x007bff", "roughness": 0.6, "metalness": 0.2}})}
{self.generate_material_code({"name": "girderMaterial", "type": "MeshStandardMaterial", "parameters": {"color": "0xcccccc", "roughness": 0.5}})}
{self.generate_material_code({"name": "pierMaterial", "type": "MeshStandardMaterial", "parameters": {"color": "0x888888", "roughness": 0.7}})}
{self.generate_material_code({"name": "foundationMaterial", "type": "MeshStandardMaterial", "parameters": {"color": "0x666666", "roughness": 0.8}})}

"""
        # Process Girders
        for i, girder_comp in enumerate(bridge_data.get("girders", [])):
            comp_name = girder_comp.get("name", f"girder{i+1}")
            geom_data = girder_comp.get("geometry_params")
            mat_data = girder_comp.get("material_params") # Specific material for this component

            if geom_data:
                geom_var = f"{comp_name}Geom"
                js_code += f"// --- {comp_name} Geometry ---\n"

                if geom_data.get("name") == "boxGirder": # Handle complex geometries from builder
                    # Outer box
                    outer_geom_var = f"{comp_name}OuterGeom"
                    js_code += f"const {outer_geom_var} = new THREE.BoxGeometry({self._format_args(geom_data['outer']['args'])});\n"
                    # Inner box (if exists, for CSG or separate mesh)
                    # For now, we'll just create the outer shell. CSG is more complex for direct Three.js code gen.
                    # A true box girder would require custom geometry or CSG.
                    # We'll represent it as a solid box for now if 'inner' is not used to subtract.
                    active_geom_var = outer_geom_var

                elif geom_data.get("name") == "tGirder":
                    flange_geom_var = f"{comp_name}FlangeGeom"
                    web_geom_var = f"{comp_name}WebGeom"
                    js_code += f"const {flange_geom_var} = new THREE.BoxGeometry({self._format_args(geom_data['flange']['args'])});\n"
                    js_code += f"const {web_geom_var} = new THREE.BoxGeometry({self._format_args(geom_data['web']['args'])});\n"

                    # Create meshes for flange and web, then group them or add separately
                    # For simplicity, we'll add them as separate meshes with relative positioning handled by mesh creation.

                    mat_var = f"{comp_name}Mat"
                    if mat_data:
                        js_code += self.generate_material_code({**mat_data, "name": mat_var}) + "\n"
                    else: # Use default girder material
                        mat_var = "girderMaterial"

                    flange_pos = geom_data['flange'].get('position', [0,0,0])
                    web_pos = geom_data['web'].get('position', [0,0,0])

                    # Adjust positions if the whole T-girder has a main position
                    main_pos = girder_comp.get("position", [0,0,0])
                    main_rot = girder_comp.get("rotation")

                    actual_flange_pos = [main_pos[0] + flange_pos[0], main_pos[1] + flange_pos[1], main_pos[2] + flange_pos[2]]
                    actual_web_pos = [main_pos[0] + web_pos[0], main_pos[1] + web_pos[1], main_pos[2] + web_pos[2]]

                    js_code += self.generate_mesh_code(flange_geom_var, mat_var, f"{comp_name}FlangeMesh", actual_flange_pos, main_rot)
                    js_code += self.generate_mesh_code(web_geom_var, mat_var, f"{comp_name}WebMesh", actual_web_pos, main_rot)
                    continue # Skip default mesh generation for T-girder parts

                else: # Simple geometry
                    js_code += f"const {geom_var} = new THREE.{geom_data['type']}({self._format_args(geom_data['args'])});\n"
                    active_geom_var = geom_var

                mat_var = f"{comp_name}Mat"
                if mat_data:
                    js_code += self.generate_material_code({**mat_data, "name": mat_var}) + "\n"
                else: # Use default girder material
                    mat_var = "girderMaterial"

                pos = girder_comp.get("position")
                rot = girder_comp.get("rotation")
                js_code += self.generate_mesh_code(active_geom_var, mat_var, comp_name, pos, rot)
            js_code += "\n"

        # Process Piers
        for i, pier_comp in enumerate(bridge_data.get("piers", [])):
            comp_name = pier_comp.get("name", f"pier{i+1}")
            geom_data = pier_comp.get("geometry_params") # This is the output from builder.create_pier
            mat_data = pier_comp.get("material_params")

            if geom_data and "shape" in geom_data:
                pier_shape_data = geom_data["shape"]
                geom_var = f"{comp_name}Geom"
                js_code += f"// --- {comp_name} Geometry ---\n"
                js_code += f"const {geom_var} = new THREE.{pier_shape_data['type']}({self._format_args(pier_shape_data['args'])});\n"

                mat_var = f"{comp_name}Mat"
                if mat_data:
                    js_code += self.generate_material_code({**mat_data, "name": mat_var}) + "\n"
                else: # Use default pier material
                    mat_var = "pierMaterial"

                pos = pier_comp.get("position")
                rot = pier_comp.get("rotation")
                js_code += self.generate_mesh_code(geom_var, mat_var, comp_name, pos, rot)
            js_code += "\n"

        # Process Foundations
        for i, found_comp in enumerate(bridge_data.get("foundations", [])):
            comp_name = found_comp.get("name", f"foundation{i+1}")
            geom_data = found_comp.get("geometry_params") # Output from builder.create_foundation
            mat_data = found_comp.get("material_params")

            if geom_data:
                js_code += f"// --- {comp_name} Geometry ---\n"
                # Foundation might be simple (shape directly) or complex (cap, footing)
                # For now, assume 'cap' or 'footing' key holds the primary geometry data
                # or a generic 'shape' key.

                primary_geom_key = None
                if "cap" in geom_data: # From pile_cap
                    primary_geom_key = "cap"
                elif "footing" in geom_data: # From spread_footing
                    primary_geom_key = "footing"
                elif "shape" in geom_data: # Fallback or simple foundation
                     primary_geom_key = "shape"

                if primary_geom_key and primary_geom_key in geom_data:
                    foundation_shape_data = geom_data[primary_geom_key]
                    geom_var = f"{comp_name}Geom"
                    js_code += f"const {geom_var} = new THREE.{foundation_shape_data['type']}({self._format_args(foundation_shape_data['args'])});\n"

                    mat_var = f"{comp_name}Mat"
                    if mat_data:
                        js_code += self.generate_material_code({**mat_data, "name": mat_var}) + "\n"
                    else: # Use default foundation material
                        mat_var = "foundationMaterial"

                    pos = found_comp.get("position")
                    rot = found_comp.get("rotation")
                    js_code += self.generate_mesh_code(geom_var, mat_var, comp_name, pos, rot)
            js_code += "\n"

        # Animation Loop
        js_code += """
// Animation Loop
function animate() {
    requestAnimationFrame(animate);
    controls.update(); // Only required if controls.enableDamping or controls.autoRotate are set to true
    renderer.render(scene, camera);
}

// Handle window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}, false);

animate();
"""
        return js_code

# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    from models.geometry_builder import BridgeGeometryBuilder # For testing with actual builder output
    builder = BridgeGeometryBuilder()
    generator = ThreeJSGenerator()

    # 1. Test generate_geometry_code
    box_geom_data = {"type": "BoxGeometry", "args": [10, 2, 3]}
    print("--- Geometry Code ---")
    print(generator.generate_geometry_code(box_geom_data))

    cyl_geom_data = {"type": "CylinderGeometry", "args": [1, 1.5, 5, 16]}
    print(generator.generate_geometry_code(cyl_geom_data))
    print("\n")

    # 2. Test generate_material_code
    material1_data = {"type": "MeshBasicMaterial", "parameters": {"color": "0xff0000", "wireframe": True}, "name": "redWireframe"}
    print("--- Material Code ---")
    print(generator.generate_material_code(material1_data))

    material2_data = {"type": "MeshStandardMaterial", "parameters": {"color": "0x00ff00", "roughness": 0.2, "metalness": 0.8}, "name": "shinyGreen"}
    print(generator.generate_material_code(material2_data))
    print("\n")

    # 3. Test generate_bridge_scene
    sample_bridge_data = {
        "scene_setup": {
            "camera_position": [10, 30, 70],
            "ambient_light_intensity": 1.2,
        },
        "girders": [
            {
                "name": "mainBoxGirder",
                "geometry_params": builder.create_box_girder(length=60, width=6, height=3, wall_thickness=0.5),
                "material_params": {"type": "MeshStandardMaterial", "parameters": {"color": "0xaaaaaa"}},
                "position": [0, 15, 0]
            },
            {
                "name": "sideTGirder",
                "geometry_params": builder.create_t_girder(length=60, flange_width=2, web_height=2.5, thickness={"flange":0.3, "web":0.2}),
                # Material will use default "girderMaterial"
                "position": [0, 15, 5] # Position the entire T-girder assembly
            }
        ],
        "piers": [
            {
                "name": "pierLeft",
                "geometry_params": builder.create_pier(pier_type="cylindrical", height=12, cross_section={"radius": 1.5}),
                "material_params": {"type": "MeshPhongMaterial", "parameters": {"color": "0x777777", "shininess": 50}},
                "position": [-25, 6, 0] # Position is base of pier
            },
            {
                "name": "pierRight",
                "geometry_params": builder.create_pier(pier_type="rectangular", height=12, cross_section={"width":2, "depth": 1.5}),
                "material_params": {"type": "MeshLambertMaterial", "parameters": {"color": "0x777788"}},
                "position": [25, 6, 0]
            }
        ],
        "foundations": [
            {
                "name": "foundationLeft",
                "geometry_params": builder.create_foundation(foundation_type="pile_cap", dimensions={"length":4, "width":4, "height":1.5}),
                "position": [-25, -0.75, 0] # Position is center of foundation block
            },
            {
                "name": "foundationRight",
                "geometry_params": builder.create_foundation(foundation_type="spread_footing", dimensions={"length":5, "width":5, "height":1}),
                "position": [25, -0.5, 0]
            }
        ]
    }
    print("--- Bridge Scene Code ---")
    full_scene_code = generator.generate_bridge_scene(sample_bridge_data)
    print(full_scene_code)

    # Save to a file for easy testing in a browser
    with open("static/js/test_scene.js", "w") as f:
        f.write(full_scene_code)
    print("\nSaved example scene to static/js/test_scene.js")
    print("To test, create an index.html file that includes Three.js and this script.")

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Three.js Bridge Test</title>
    <style> body {{ margin: 0; }} canvas {{ display: block; }} </style>
</head>
<body>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="test_scene.js"></script>
</body>
</html>
    """
    with open("static/test_bridge.html", "w") as f:
        f.write(html_content)
    print("Created static/test_bridge.html to view the test_scene.js")
```
