import json
from models.geometry_builder import BridgeGeometryBuilder # Ensure this is importable

class ThreeJSGenerator:
    def __init__(self):
        self.builder = BridgeGeometryBuilder()

    def _get_component_geometry(self, component_data: dict) -> dict:
        """Extracts the primary geometry dict from component data from BridgeGeometryBuilder."""
        if not component_data: # Handle None case
            return None

        if component_data.get("name") == "boxGirder":
            return component_data.get("outer") # Use outer shell for simplicity
        elif component_data.get("name") == "tGirder":
             # T-Girder is complex, return as is, to be handled as multiple components
            return component_data # The caller will need to iterate through flange and web
        elif "shape" in component_data: # For piers
            return component_data["shape"]
        elif "cap" in component_data: # For pile_cap foundation
            return component_data["cap"]
        elif "footing" in component_data: # For spread_footing foundation
            return component_data["footing"]
        elif component_data.get("type") and component_data.get("args"): # Already a simple geometry dict
            return component_data
        return None


    def generate_scene_data(self, bridge_design_data: dict) -> dict:
        """
        Generates a JSON-serializable dictionary describing the 3D scene.
        'bridge_design_data' is a dictionary from BridgeDesign.model_dump().
        """
        scene_data = {
            "scene_setup": {
                "backgroundColor": "0xf0f0f0",
                "camera_fov": 60,
                "camera_position": [0,0,0], # Will be calculated later
                "camera_lookAt": [0, 0, 0],
                "ambient_light": {"color": "0x606060", "intensity": 1.0},
                "directional_light": {"color": "0xffffff", "intensity": 1.5, "position": [1, 0.75, 0.5]}
            },
            "materials": { # Define common materials once
                "concrete": {"type": "MeshStandardMaterial", "parameters": {"color": "0xcccccc", "roughness": 0.85, "metalness": 0.1}},
                "steel": {"type": "MeshStandardMaterial", "parameters": {"color": "0xa0a0a5", "roughness": 0.4, "metalness": 0.7}},
                "girderDefault": {"type": "MeshStandardMaterial", "parameters": {"color": "0xB0B0B0", "roughness": 0.7}},
                "pierDefault": {"type": "MeshStandardMaterial", "parameters": {"color": "0xA0A0A0", "roughness": 0.75}},
                "foundationDefault": {"type": "MeshStandardMaterial", "parameters": {"color": "0x888888", "roughness": 0.8}},
            },
            "components": []
        }

        # Determine primary material based on bridge type or materials spec
        primary_material_ref = "concrete" # Default
        bridge_type_lower = bridge_design_data.get("bridge_type", "").lower()
        materials_spec = bridge_design_data.get("materials", {})
        if "steel" in bridge_type_lower or \
           any("steel" in str(v).lower() for v in materials_spec.values()) or \
           materials_spec.get("structural_steel_grade"):
            primary_material_ref = "steel"

        # --- GIRDERS / DECK ---
        span = bridge_design_data.get("span_lengths", [50.0])[0]
        girder_depth = bridge_design_data.get("main_girder", {}).get("depth_m", 2.0)
        deck_width = bridge_design_data.get("bridge_width", 10.0)
        main_girder_spec = bridge_design_data.get("main_girder", {})
        girder_type_name = main_girder_spec.get("type", "box").lower() # Default to box if not specified

        # Position of the main superstructure (Y=0 is bottom of girder)
        superstructure_base_y = 0

        if "t-girder" in girder_type_name or "i-girder" in girder_type_name: # Assuming I-girder is similar to T for this basic model
            num_girders = main_girder_spec.get("number_of_girders", 1)
            if not isinstance(num_girders, int) or num_girders <= 0 : num_girders = 1

            girder_spacing = deck_width / num_girders if num_girders > 1 else 0
            # For a single girder, place it at z=0. For multiple, offset them.
            start_z_offset = - ( (num_girders - 1) * girder_spacing ) / 2.0


            for i in range(num_girders):
                z_pos = start_z_offset + i * girder_spacing
                t_girder_flange_w = main_girder_spec.get("flange_width_per_girder", (deck_width / num_girders) * 0.8 if num_girders > 0 else deck_width*0.8)
                t_girder_web_h = girder_depth * 0.8
                t_girder_thickness = {"flange": girder_depth * 0.2, "web": t_girder_flange_w * 0.15}

                t_girder_params = self.builder.create_t_girder(
                    length=span, flange_width=t_girder_flange_w,
                    web_height=t_girder_web_h, thickness=t_girder_thickness
                )

                # Flange geometry and position
                flange_geom_data = t_girder_params["flange"]
                scene_data["components"].append({
                    "name": f"tGirder_{i+1}_flange", "type": "girder_flange",
                    "geometry": {"type": flange_geom_data["type"], "args": flange_geom_data["args"]},
                    "material_ref": primary_material_ref,
                    # position is relative to the T-girder's own origin, then add superstructure_base_y and z_pos
                    "position": [0, superstructure_base_y + flange_geom_data["position"][1], z_pos + flange_geom_data["position"][2]],
                })
                # Web geometry and position
                web_geom_data = t_girder_params["web"]
                scene_data["components"].append({
                    "name": f"tGirder_{i+1}_web", "type": "girder_web",
                    "geometry": {"type": web_geom_data["type"], "args": web_geom_data["args"]},
                    "material_ref": primary_material_ref,
                    "position": [0, superstructure_base_y + web_geom_data["position"][1], z_pos + web_geom_data["position"][2]],
                })

        else: # Default to Box Girder or solid deck representation
            deck_geometry_params = self.builder.create_box_girder(length=span, width=deck_width, height=girder_depth, wall_thickness=girder_depth*0.15)
            deck_geom = self._get_component_geometry(deck_geometry_params)
            if deck_geom:
                scene_data["components"].append({
                    "name": "mainDeckSuperstructure", "type": "deck_box",
                    "geometry": deck_geom,
                    "material_ref": primary_material_ref,
                    "position": [0, superstructure_base_y, 0],
                })

        # --- PIERS ---
        num_piers_to_model = main_girder_spec.get("num_piers_visualize", 2 if span > 25 else 0) # Heuristic: 2 supports for spans > 25m
        pier_height = main_girder_spec.get("pier_height_below_girder", span * 0.15 if span * 0.15 > 5 else 8.0)
        pier_design_spec = bridge_design_data.get("pier_design", {})
        pier_type = pier_design_spec.get("shape", "cylindrical").lower()
        pier_dims = pier_design_spec.get("dimensions", {"radius": max(0.5, span/40)})

        if num_piers_to_model > 0:
            pier_positions_x = []
            # Simple placement for supports at ends or near ends for visualization
            if num_piers_to_model == 1: # e.g. a central pier for a specific design, or a single support for a cantilever. For now, assume it means one support point.
                 pier_positions_x = [0] # A single central pier, adjust Y position if it's a tower.
            elif num_piers_to_model >= 2: # Typical end supports or multiple supports
                 # Place them near the ends of the span
                 pier_positions_x = [-span * 0.45, span * 0.45] # Slightly inset from true ends
                 if num_piers_to_model > 2: # Add intermediate piers if more than 2
                     for k in range(1, num_piers_to_model -1):
                         pier_positions_x.append(-span*0.45 + k * (span*0.9 / (num_piers_to_model-1)))


            for i, x_pos in enumerate(pier_positions_x):
                pier_geom_params = self.builder.create_pier(pier_type, pier_height, pier_dims)
                pier_geom = self._get_component_geometry(pier_geom_params)
                if pier_geom and not pier_geom.get("error"):
                    scene_data["components"].append({
                        "name": f"pier_{i+1}", "type": "pier",
                        "geometry": pier_geom,
                        "material_ref": "pierDefault",
                        # Position pier center such that its top is at superstructure_base_y - girder_depth/2
                        "position": [x_pos, superstructure_base_y - girder_depth/2 - pier_height/2, 0],
                    })

        # --- FOUNDATIONS ---
        foundation_spec = bridge_design_data.get("foundation", {})
        foundation_type = foundation_spec.get("type", "spread_footing").lower().replace(" ", "_")

        piers_in_scene = [comp for comp in scene_data["components"] if comp["type"] == "pier"]
        for pier_comp in piers_in_scene:
            foundation_height = foundation_spec.get("depth_m", pier_height * 0.2 if pier_height > 0 else 1.5)

            pier_geom_args = pier_comp["geometry"]["args"]
            f_len = pier_geom_args[0] * 1.5 # Width of pier for Box, Radius for Cylinder
            f_width = pier_geom_args[0] * 1.5 # Default to square based on radius/first arg
            if pier_comp["geometry"]["type"] == "BoxGeometry":
                 f_width = pier_geom_args[2] * 1.5 # Use depth for width if Box

            foundation_dims = {"length": max(2.0, f_len), "width": max(2.0, f_width), "height": max(1.0, foundation_height)}

            foundation_geom_params = self.builder.create_foundation(foundation_type, foundation_dims)
            foundation_geom = self._get_component_geometry(foundation_geom_params)

            if foundation_geom and not foundation_geom.get("error"):
                # Position foundation bottom of pier
                pier_base_y = pier_comp["position"][1] - pier_height/2
                scene_data["components"].append({
                    "name": f"foundation_for_{pier_comp['name']}", "type": "foundation",
                    "geometry": foundation_geom,
                    "material_ref": "foundationDefault",
                    "position": [pier_comp["position"][0], pier_base_y - foundation_height/2, pier_comp["position"][2]],
                })

        # Adjust camera position based on overall bridge size for a good initial view
        all_x = [0, span]
        all_y = [superstructure_base_y - girder_depth/2, superstructure_base_y + girder_depth/2]
        all_z = [-deck_width/2, deck_width/2]

        for comp in scene_data["components"]: # Recalculate bounds based on actual components
            pos = comp["position"]
            args = comp["geometry"].get("args", [1,1,1])
            geom_type = comp["geometry"].get("type")

            if geom_type == "BoxGeometry":
                all_x.extend([pos[0] - args[0]/2, pos[0] + args[0]/2])
                all_y.extend([pos[1] - args[1]/2, pos[1] + args[1]/2])
                all_z.extend([pos[2] - args[2]/2, pos[2] + args[2]/2])
            elif geom_type == "CylinderGeometry":
                all_x.extend([pos[0] - args[0], pos[0] + args[0]])
                all_y.extend([pos[1] - args[2]/2, pos[1] + args[2]/2])
                all_z.extend([pos[2] - args[0], pos[2] + args[0]])

        min_x, max_x = (min(all_x), max(all_x)) if all_x else (0,0)
        min_y, max_y = (min(all_y), max(all_y)) if all_y else (0,0)
        min_z, max_z = (min(all_z), max(all_z)) if all_z else (0,0)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2

        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z

        max_overall_dim = max(size_x, size_y, size_z, 1.0)

        cam_dist_factor = 1.5
        scene_data["scene_setup"]["camera_position"] = [
            center_x + max_overall_dim * 0.5 * cam_dist_factor,
            center_y + max_overall_dim * 0.3 * cam_dist_factor,
            center_z + max_overall_dim * 0.8 * cam_dist_factor  # More Z distance
        ]
        scene_data["scene_setup"]["camera_lookAt"] = [center_x, center_y, center_z]

        return scene_data


# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    generator = ThreeJSGenerator()

    sample_bridge_design_data = {
        "design_id": "test_design_001",
        "bridge_type": "Prestressed Concrete Continuous Girder",
        "span_lengths": [100.0],
        "bridge_width": 15.0,
        "design_load": "Highway Class A",
        "main_girder": {
            "type": "Prestressed Concrete Box Girder",
            "depth_m": 5.0,
            "pier_height_below_girder": 12.0,
            "num_piers_visualize": 2
        },
        "pier_design": {
            "type": "Reinforced Concrete Column",
            "shape": "rectangular",
            "dimensions": {"width": 2.5, "depth": 2.0}
        },
        "foundation": {
            "type": "Pile Cap",
            "depth_m": 2.0
        },
        "materials": {
            "concrete_grade": "C50/60",
            "prestressing_steel": "High-tensile strands"
        }
    }

    print("--- Generating Scene Data (Concrete Box Girder) ---")
    scene_output_data = generator.generate_scene_data(sample_bridge_design_data)
    print(json.dumps(scene_output_data, indent=2))
    with open("test_scene_data_concrete_box.json", "w") as f:
        json.dump(scene_output_data, f, indent=2)
    print("\nSaved concrete box girder scene data to test_scene_data_concrete_box.json")

    steel_bridge_data = {
        "design_id": "steel_bridge_002",
        "bridge_type": "Steel I-Girder Bridge",
        "span_lengths": [80.0],
        "bridge_width": 10.0,
        "main_girder": {"type": "Steel I-Girder", "depth_m": 4.0, "pier_height_below_girder": 10.0, "number_of_girders": 4, "flange_width_per_girder": 0.6},
        "pier_design": {"shape": "cylindrical", "dimensions": {"radius": 1.0}},
        "foundation": {"type": "Spread Footing", "depth_m": 1.5},
        "materials": {"structural_steel_grade": "Q355"}
    }
    print("\n--- Generating Scene Data (Steel I-Girder) ---")
    scene_output_steel = generator.generate_scene_data(steel_bridge_data)
    print(json.dumps(scene_output_steel, indent=2))
    with open("test_scene_data_steel_i_girder.json", "w") as f:
        json.dump(scene_output_steel, f, indent=2)
    print("\nSaved steel I-girder scene data to test_scene_data_steel_i_girder.json")
