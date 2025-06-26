class BridgeGeometryBuilder:
    def create_box_girder(self, length: float, width: float, height: float,
                        wall_thickness: float) -> dict:
        """
        Creates geometric parameters for a box girder.
        For simplicity, this will represent the outer and inner boxes.
        A more detailed model would define vertices and faces.
        """
        outer_box = {"type": "BoxGeometry", "args": [width, height, length]}
        inner_width = width - 2 * wall_thickness
        inner_height = height - 2 * wall_thickness
        # Ensure inner dimensions are positive
        if inner_width <= 0 or inner_height <= 0:
            # This would be a solid box or invalid parameters
            inner_box = None
        else:
            inner_box = {"type": "BoxGeometry", "args": [inner_width, inner_height, length]}

        return {
            "name": "boxGirder",
            "outer": outer_box,
            "inner": inner_box, # This would be subtracted in a CSG operation or handled by creating faces
            "length": length,
            "width": width,
            "height": height,
            "wall_thickness": wall_thickness
        }

    def create_t_girder(self, length: float, flange_width: float,
                      web_height: float, thickness: dict) -> dict:
        """
        Creates geometric parameters for a T-girder.
        'thickness' is a dict with 'flange' and 'web' keys.
        Represents the T-shape as two connected boxes (flange and web).
        """
        flange_thickness = thickness.get("flange", 0.1) # Default if not provided
        web_thickness = thickness.get("web", 0.1)       # Default if not provided

        flange = {
            "type": "BoxGeometry",
            "args": [flange_width, flange_thickness, length],
            "position": [0, web_height/2 + flange_thickness/2, 0] # Position flange on top of web
        }
        web = {
            "type": "BoxGeometry",
            "args": [web_thickness, web_height, length],
            "position": [0, 0, 0] # Web centered at origin (y-axis)
        }

        return {
            "name": "tGirder",
            "flange": flange,
            "web": web,
            "length": length,
            "flange_width": flange_width,
            "web_height": web_height,
            "flange_thickness": flange_thickness,
            "web_thickness": web_thickness
        }

    def create_pier(self, pier_type: str, height: float,
                   cross_section: dict) -> dict:
        """
        Creates geometric parameters for a bridge pier.
        'pier_type' can be 'cylindrical', 'rectangular', etc.
        'cross_section' contains dimensions like 'radius' or 'width'/'depth'.
        """
        pier_geometry = {"name": "pier", "pier_type": pier_type, "height": height}

        if pier_type == "cylindrical":
            radius = cross_section.get("radius", 1.0) # Default radius
            pier_geometry["shape"] = {
                "type": "CylinderGeometry",
                "args": [radius, radius, height, 32] # radiusTop, radiusBottom, height, radialSegments
            }
            pier_geometry["radius"] = radius
        elif pier_type == "rectangular":
            width = cross_section.get("width", 1.0)   # Default width
            depth = cross_section.get("depth", 1.0)   # Default depth
            pier_geometry["shape"] = {
                "type": "BoxGeometry",
                "args": [width, height, depth] # Three.js BoxGeometry is width, height, depth
            }
            pier_geometry["width"] = width
            pier_geometry["depth"] = depth
        else:
            # Placeholder for other pier types or a default
            pier_geometry["shape"] = {
                "type": "BoxGeometry",
                "args": [1, height, 1] # Default fallback shape
            }
            pier_geometry["error"] = f"Unsupported pier type: {pier_type}. Using default box."

        return pier_geometry

    def create_foundation(self, foundation_type: str, dimensions: dict) -> dict:
        """
        Creates geometric parameters for a bridge foundation.
        'foundation_type' can be 'pile_cap', 'spread_footing', etc.
        'dimensions' contains relevant sizes like 'length', 'width', 'height', 'pile_radius', 'pile_count'.
        """
        foundation_geometry = {"name": "foundation", "foundation_type": foundation_type}

        if foundation_type == "pile_cap":
            length = dimensions.get("length", 5)
            width = dimensions.get("width", 5)
            height = dimensions.get("height", 1.5)
            foundation_geometry["cap"] = {
                "type": "BoxGeometry",
                "args": [length, height, width] # Assuming length is X, height is Y, width is Z
            }
            foundation_geometry["dimensions"] = dimensions
            # Piles would be separate geometries, potentially generated here too
            # For simplicity, we'll just define the cap for now.
        elif foundation_type == "spread_footing":
            length = dimensions.get("length", 6)
            width = dimensions.get("width", 6)
            height = dimensions.get("height", 1)
            foundation_geometry["footing"] = {
                "type": "BoxGeometry",
                "args": [length, height, width]
            }
            foundation_geometry["dimensions"] = dimensions
        else:
            foundation_geometry["shape"] = {
                "type": "BoxGeometry",
                "args": [dimensions.get("length", 3), dimensions.get("height", 1), dimensions.get("width", 3)]
            }
            foundation_geometry["error"] = f"Unsupported foundation type: {foundation_type}. Using default box."

        return foundation_geometry

# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    builder = BridgeGeometryBuilder()

    box_girder_params = builder.create_box_girder(length=50, width=5, height=3, wall_thickness=0.3)
    print("Box Girder:", box_girder_params)

    t_girder_params = builder.create_t_girder(length=30, flange_width=3, web_height=2, thickness={"flange": 0.4, "web": 0.25})
    print("\nT Girder:", t_girder_params)

    cylindrical_pier_params = builder.create_pier(pier_type="cylindrical", height=10, cross_section={"radius": 1.2})
    print("\nCylindrical Pier:", cylindrical_pier_params)

    rectangular_pier_params = builder.create_pier(pier_type="rectangular", height=8, cross_section={"width": 1.5, "depth": 2.5})
    print("\nRectangular Pier:", rectangular_pier_params)

    unknown_pier_params = builder.create_pier(pier_type="octagonal", height=9, cross_section={})
    print("\nUnknown Pier:", unknown_pier_params)

    pile_cap_foundation = builder.create_foundation(foundation_type="pile_cap", dimensions={"length": 6, "width": 6, "height": 2})
    print("\nPile Cap Foundation:", pile_cap_foundation)

    spread_footing_foundation = builder.create_foundation(foundation_type="spread_footing", dimensions={"length": 7, "width": 7, "height": 1.2})
    print("\nSpread Footing Foundation:", spread_footing_foundation)
