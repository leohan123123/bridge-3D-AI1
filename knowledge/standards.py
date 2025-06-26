# Design
# This file will store references to design codes and standards.

# Example:
# STANDARD_CONCRETE_DESIGN = "ACI 318"
# STANDARD_STEEL_DESIGN = "AISC 360"
# STANDARD_LOADS = "ASCE 7"

# Placeholder for actual design standards information
# In a real system, this might link to specific clauses or provide summaries.

DESIGN_STANDARDS_REFERENCES = {
    "General": "AASHTO LRFD Bridge Design Specifications",
    "Concrete": "GB 50010 - Code for design of concrete structures",
    "Steel": "GB 50017 - Standard for design of steel structures",
    "Seismic": "JTG B02-2013 - Specifications for seismic design of highway bridges",
    "Loads": "JTG D60-2015 - General specifications for design of highway bridges and culverts"
}

def get_standard_for_material(material_type):
    """
    Returns the relevant design standard for a given material.
    """
    if material_type.lower() == "concrete":
        return DESIGN_STANDARDS_REFERENCES.get("Concrete")
    elif material_type.lower() == "steel":
        return DESIGN_STANDARDS_REFERENCES.get("Steel")
    else:
        return DESIGN_STANDARDS_REFERENCES.get("General")

if __name__ == '__main__':
    print("Available standards references:")
    for key, value in DESIGN_STANDARDS_REFERENCES.items():
        print(f"- {key}: {value}")

    print(f"\nStandard for concrete: {get_standard_for_material('concrete')}")
    print(f"Standard for steel: {get_standard_for_material('steel')}")
