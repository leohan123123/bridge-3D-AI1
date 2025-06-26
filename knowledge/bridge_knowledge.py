# Bridge professional knowledge base

# 1. Common Bridge Types: Characteristics and Applicability
COMMON_BRIDGE_TYPES = {
    "Beam Bridge": {
        "description": "Consists of horizontal beams supported at each end by abutments or piers. Can be simple span or continuous.",
        "typical_spans_m": "Up to 80m (simple), up to 250m (continuous with steel girders)",
        "materials": ["Reinforced Concrete", "Prestressed Concrete", "Steel", "Timber"],
        "advantages": ["Simple design and construction", "Cost-effective for short to medium spans"],
        "disadvantages": ["Limited span capability", "Can be aesthetically plain"],
        "suitable_for": ["Highway overpasses", "Railway bridges (shorter spans)", "Pedestrian bridges"]
    },
    "Arch Bridge": {
        "description": "Has abutments at each end shaped as a curved arch. The arch design transfers weight from the bridge deck to the abutments.",
        "typical_spans_m": "50m to 500m+",
        "materials": ["Stone", "Concrete", "Steel"],
        "advantages": ["Aesthetically pleasing", "Can span long distances", "Strong under compression"],
        "disadvantages": ["Requires strong foundations/abutments", "Construction can be complex"],
        "suitable_for": ["River crossings", "Valleys", "Areas where aesthetics are important"]
    },
    "Truss Bridge": {
        "description": "Uses a truss, a structure of connected elements (usually straight) forming triangular units.",
        "typical_spans_m": "30m to 500m+",
        "materials": ["Steel", "Timber", "Wrought Iron (historic)"],
        "advantages": ["High strength-to-weight ratio", "Can span significant distances", "Relatively efficient material use"],
        "disadvantages": ["Can be complex to design and fabricate", "Maintenance of many connections"],
        "suitable_for": ["Railway bridges", "Highway bridges", "Pedestrian bridges (longer spans)"]
    },
    "Suspension Bridge": {
        "description": "The deck is hung below suspension cables on vertical suspenders. Main cables are anchored at each end of the bridge and run between towers.",
        "typical_spans_m": "200m to 2000m+",
        "materials": ["Steel (cables, deck, towers)", "Concrete (towers, anchorages)"],
        "advantages": ["Can span very long distances", "Flexible, can withstand some movement (e.g., earthquakes if designed for)"],
        "disadvantages": ["Expensive", "Complex to design and construct", "Susceptible to aerodynamic instability (wind) if not properly designed"],
        "suitable_for": ["Very long river/strait crossings", "Iconic structures"]
    },
    "Cable-Stayed Bridge": {
        "description": "Similar to suspension bridges, but cables are directly connected from the tower(s) to the deck in a fan-like or harp-like pattern.",
        "typical_spans_m": "100m to 1000m+",
        "materials": ["Steel (cables, deck, towers)", "Concrete (deck, towers)"],
        "advantages": ["Good for medium to long spans", "Stiffer than suspension bridges", "Aesthetically modern"],
        "disadvantages": ["Complex analysis and construction", "Can be more expensive than beam bridges for shorter spans in its range"],
        "suitable_for": ["River crossings", "Harbor entrances", "Visually prominent locations"]
    }
}

# 2. Basic Design Parameters and Ranges (Highly Simplified Examples)
DESIGN_PARAMETER_RANGES = {
    "span_to_depth_ratio": { # For main girders
        "steel_beam": (15, 25), # L/15 to L/25
        "concrete_beam": (10, 20), # L/10 to L/20
        "prestressed_concrete_beam": (18, 30),
        "truss": (8, 12) # For overall truss depth
    },
    "typical_road_lane_width_m": (3.0, 3.75),
    "typical_pedestrian_walkway_width_m": (1.5, 3.0),
    "live_loads": {
        "pedestrian_kPa": (3.0, 5.0), # Kilopascals
        "highway_standard": "Refer to local codes (e.g., AASHTO, Eurocode)",
        "railway_standard": "Refer to specific railway loading standards (e.g., Cooper E-loading, UIC)"
    }
}

# 3. Material Properties (Example Snippets)
MATERIAL_PROPERTIES = {
    "concrete": {
        "C25/30": {"compressive_strength_MPa": 25, "density_kg_m3": 2400},
        "C30/37": {"compressive_strength_MPa": 30, "density_kg_m3": 2400},
        "C40/50": {"compressive_strength_MPa": 40, "density_kg_m3": 2500},
    },
    "steel_structural": {
        "S275": {"yield_strength_MPa": 275, "tensile_strength_MPa": (410, 560), "density_kg_m3": 7850},
        "S355": {"yield_strength_MPa": 355, "tensile_strength_MPa": (470, 630), "density_kg_m3": 7850},
    },
    "steel_prestressing_strands": {
        "Y1860S7": {"tensile_strength_MPa": 1860, "elastic_modulus_GPa": 195}
    }
}

# 4. Construction Details and Connections (Conceptual - too complex for simple dict)
# This section would typically involve diagrams, standard details, and design guides.
# For this system, it might involve rules like:
# - "Steel girder to concrete deck connection: Shear studs recommended."
# - "Segmental construction suitable for long span concrete bridges."

# Placeholder functions to access knowledge
def get_bridge_type_info(bridge_type_name: str) -> dict:
    return COMMON_BRIDGE_TYPES.get(bridge_type_name, {"error": "Bridge type not found"})

def get_material_property(material_category: str, material_grade: str) -> dict:
    category = MATERIAL_PROPERTIES.get(material_category)
    if category:
        return category.get(material_grade, {"error": "Material grade not found"})
    return {"error": "Material category not found"}

def get_design_parameter_range(parameter_name: str, sub_type: str = None) -> tuple or dict:
    param = DESIGN_PARAMETER_RANGES.get(parameter_name)
    if param:
        if sub_type and isinstance(param, dict):
            return param.get(sub_type, {"error": f"Sub-type {sub_type} not found for {parameter_name}"})
        return param
    return {"error": f"Design parameter {parameter_name} not found"}

if __name__ == "__main__":
    print("Bridge Knowledge Base - Examples:")

    print("\n--- Common Bridge Types ---")
    for name, details in COMMON_BRIDGE_TYPES.items():
        print(f"{name}: Suitable for spans like {details['typical_spans_m']}")

    print("\n--- Accessing Specific Info ---")
    print("Cable-Stayed Bridge Info:", get_bridge_type_info("Cable-Stayed Bridge"))
    print("Titanium Alloy Info:", get_bridge_type_info("Titanium Alloy Bridge")) # Example of not found

    print("\n--- Material Properties ---")
    print("Concrete C40/50:", get_material_property("concrete", "C40/50"))
    print("Steel S355:", get_material_property("steel_structural", "S355"))

    print("\n--- Design Parameter Ranges ---")
    print("Span-to-depth for steel beam:", get_design_parameter_range("span_to_depth_ratio", "steel_beam"))
    print("Typical road lane width:", get_design_parameter_range("typical_road_lane_width_m"))
    print("Non-existent parameter:", get_design_parameter_range("magic_ratio"))
