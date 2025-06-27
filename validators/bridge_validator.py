# Ensure project root is in sys.path for standalone execution
import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from typing import Dict, Any, List, Tuple, Optional
import logging

# Configure basic logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Attempt to import from knowledge base
try:
    from knowledge import bridge_knowledge
except ImportError:
    logger.warning("Direct import of 'knowledge' failed in BridgeDesignValidator. Attempting to adjust sys.path. "
                   "This might indicate a project structure or PYTHONPATH issue if not running in a managed environment.")
    _validator_project_root = Path(__file__).resolve().parent.parent
    if str(_validator_project_root) not in sys.path:
        sys.path.insert(0, str(_validator_project_root))
    try:
        from knowledge import bridge_knowledge
    except ImportError as e_inner:
        logger.error(f"CRITICAL: Failed to import 'knowledge.bridge_knowledge' even after sys.path modification: {e_inner}. Validator may not function correctly.")
        bridge_knowledge = None


class BridgeDesignValidator:
    """
    Validates various aspects of a bridge design.
    """

    def __init__(self):
        logger.info("BridgeDesignValidator initialized.")
        if bridge_knowledge is None:
            logger.error("Knowledge base (bridge_knowledge) could not be imported. Validation capabilities will be limited.")

    def validate_span_to_depth_ratio(self, span: float, depth: float, bridge_type: str) -> Tuple[bool, str]:
        """
        Validates the span-to-depth ratio for the main girders.
        Ratio is typically L/depth.
        Returns a tuple (is_valid, message).
        """
        if bridge_knowledge is None:
            return True, "Span-to-depth ratio check skipped: Knowledge base unavailable."
        if not span > 0 or not depth > 0:
            return False, "Span and depth must be positive values."

        ratio = span / depth
        type_key = None
        bridge_type_lower = bridge_type.lower()

        if "prestressed" in bridge_type_lower and ("concrete" in bridge_type_lower or "pc" in bridge_type_lower):
            if "beam" in bridge_type_lower or "girder" in bridge_type_lower:
                type_key = "prestressed_concrete_beam"
        elif "steel" in bridge_type_lower:
            if "beam" in bridge_type_lower or "girder" in bridge_type_lower: type_key = "steel_beam"
            elif "truss" in bridge_type_lower: type_key = "steel_truss"
        elif "concrete" in bridge_type_lower:
            if "beam" in bridge_type_lower or "girder" in bridge_type_lower: type_key = "concrete_beam"
            elif "arch" in bridge_type_lower: type_key = "concrete_arch"
        elif "truss" in bridge_type_lower: type_key = "truss"

        if not type_key:
            return True, f"Span-to-depth ratio check skipped: No specific range for bridge type '{bridge_type}'. Ratio is {ratio:.2f}."

        # Ensure bridge_knowledge and its attributes are accessible
        if not hasattr(bridge_knowledge, 'get_design_parameter_range'):
             return True, "Span-to-depth ratio check skipped: bridge_knowledge.get_design_parameter_range not available."

        ranges = bridge_knowledge.get_design_parameter_range("span_to_depth_ratio", type_key)

        if isinstance(ranges, dict) and "error" in ranges: # Error from get_design_parameter_range
            return True, f"Span-to-depth ratio check skipped: Could not find range for '{type_key}'. Ratio is {ratio:.2f}. Details: {ranges['error']}"

        if not isinstance(ranges, tuple) or len(ranges) != 2:
            logger.warning(f"Invalid range format for {type_key} in bridge_knowledge: {ranges}")
            return True, f"Span-to-depth ratio check skipped: Invalid range configured for '{type_key}'. Ratio is {ratio:.2f}."

        min_ratio, max_ratio = ranges

        if min_ratio <= ratio <= max_ratio:
            return True, f"Span-to-depth ratio {ratio:.2f} is within the typical range ({min_ratio}-{max_ratio}) for {type_key}."
        else:
            return False, f"Warning: Span-to-depth ratio {ratio:.2f} is outside the typical range ({min_ratio}-{max_ratio}) for {type_key}."

    def validate_material_compatibility(self, materials: Dict[str, Any], bridge_type: str, span: float) -> Tuple[bool, str]:
        bridge_type_lower = bridge_type.lower()
        notes = []
        valid = True

        main_beam_material = str(materials.get("main_beams_material", "")).lower() or \
                             str(materials.get("main_beams", "")).lower() or \
                             str(materials.get("concrete_grade", "")).lower()

        if "prestressed" in bridge_type_lower or "psc" in bridge_type_lower:
            if not ("prestressed" in main_beam_material or "psc" in main_beam_material or "预应力" in main_beam_material): # "预应力" is Chinese for prestressed
                notes.append(f"Warning: Bridge type '{bridge_type}' suggests prestressed concrete, but main beam material '{materials.get('main_beams_material', 'N/A')}' does not clearly state it.")
                valid = False
            prestressing_steel = str(materials.get("prestressing_steel_type", "")).lower() or \
                                 str(materials.get("prestressing_steel", "")).lower()
            if not prestressing_steel:
                notes.append(f"Warning: Prestressed concrete bridge type specified, but no prestressing steel type defined in materials.")
                valid = False

        if "concrete" in bridge_type_lower:
            if not ("concrete" in main_beam_material or "混凝土" in main_beam_material or (main_beam_material.startswith("c") and main_beam_material[1:].isdigit())): # "混凝土" is Chinese for concrete
                 notes.append(f"Warning: Bridge type '{bridge_type}' suggests concrete, but main beam material '{materials.get('main_beams_material', 'N/A')}' does not clearly state it.")
                 valid = False

        if "steel" in bridge_type_lower and "bridge" in bridge_type_lower:
             if not "steel" in main_beam_material:
                 notes.append(f"Warning: Bridge type '{bridge_type}' suggests steel, but main beam material '{materials.get('main_beams_material', 'N/A')}' does not clearly state it.")
                 valid = False

        if span > 300 and "concrete_beam" == bridge_type_lower and not ("prestressed" in bridge_type_lower or "psc" in bridge_type_lower):
            notes.append(f"Warning: Span of {span}m is very large for a non-prestressed concrete beam bridge.")
            valid = False

        if not notes:
            return True, "Material compatibility checks passed (basic)."
        else:
            return valid, " ".join(notes)

    def validate_seismic_requirements(self, design_params: Dict[str, Any], design_materials: Dict[str, Any], seismic_intensity_str: Optional[str]) -> Tuple[bool, str]:
        if not seismic_intensity_str:
            return True, "Seismic requirements check skipped: No seismic intensity level provided."

        seismic_level = 0
        try:
            numerical_part = ''.join(filter(str.isdigit, seismic_intensity_str))
            if numerical_part:
                seismic_level = int(numerical_part)
        except ValueError:
            logger.warning(f"Could not parse numerical seismic level from '{seismic_intensity_str}'. Text-based checks will proceed.")

        notes = []
        mentioned_seismic_design = False

        if "seismic_design_intensity" in design_params and design_params["seismic_design_intensity"]:
            notes.append(f"Seismic design intensity noted in parameters: '{design_params['seismic_design_intensity']}'.")
            mentioned_seismic_design = True

        if "seismic_considerations_foundation" in design_params and design_params["seismic_considerations_foundation"]:
            notes.append(f"Seismic considerations in foundation: '{design_params['seismic_considerations_foundation']}'.")
            mentioned_seismic_design = True

        key_nodes = design_params
        if "other_seismic_details" in key_nodes and key_nodes["other_seismic_details"]:
            notes.append(f"Other seismic details in key nodes: '{key_nodes['other_seismic_details']}'.")
            mentioned_seismic_design = True
        if "beam_to_pier_connection" in key_nodes:
            connection_info = str(key_nodes.get("beam_to_pier_connection","")).lower() # Ensure it's a string
            if any(term in connection_info for term in ["seismic", "抗震", "damper", "isolation", "限位"]): # "抗震" is seismic in Chinese, "限位" is limit/restraint
                notes.append(f"Seismic considerations in beam-to-pier connection: '{key_nodes['beam_to_pier_connection']}'.")
                mentioned_seismic_design = True

        if seismic_level >= 7:
            if not mentioned_seismic_design:
                return False, f"Warning: Seismic intensity is high ({seismic_intensity_str}), but no explicit seismic design parameters or details were found in the design output."

            reinforcement_grade = str(design_materials.get("reinforcement_steel_grade", "")).upper()
            if not any(ductile_char in reinforcement_grade for ductile_char in ["D", "E", "SD"]):
                 notes.append(f"Note: For seismic level {seismic_intensity_str}, consider using reinforcement steel with enhanced ductility (e.g., Grade D or E, or SD grades). Current: '{reinforcement_grade}'.")

            notes.append(f"Seismic design requirements for intensity '{seismic_intensity_str}' appear to be addressed at a high level.")
            return True, " ".join(notes)
        elif mentioned_seismic_design:
             return True, f"Seismic considerations mentioned for intensity '{seismic_intensity_str}'. " + " ".join(notes)

        return True, f"Basic seismic check passed for intensity '{seismic_intensity_str}'. No major red flags found in high-level review, but detailed engineering verification is essential. " + " ".join(notes)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    validator = BridgeDesignValidator()

    print("\n--- Span-to-Depth Ratio Tests ---")
    if bridge_knowledge:
        if not hasattr(bridge_knowledge, 'DESIGN_PARAMETER_RANGES'): bridge_knowledge.DESIGN_PARAMETER_RANGES = {}
        if not "span_to_depth_ratio" in bridge_knowledge.DESIGN_PARAMETER_RANGES:
            bridge_knowledge.DESIGN_PARAMETER_RANGES["span_to_depth_ratio"] = {}

        sdr_ranges = bridge_knowledge.DESIGN_PARAMETER_RANGES["span_to_depth_ratio"]
        if "prestressed_concrete_beam" not in sdr_ranges: sdr_ranges['prestressed_concrete_beam'] = (18, 28)
        if "concrete_beam" not in sdr_ranges: sdr_ranges['concrete_beam'] = (12, 20)
        if "steel_beam" not in sdr_ranges: sdr_ranges['steel_beam'] = (15, 30)
        if "truss" not in sdr_ranges: sdr_ranges['truss'] = (8, 15)
        if "steel_truss" not in sdr_ranges: sdr_ranges['steel_truss'] = (10, 18)

        print(validator.validate_span_to_depth_ratio(span=60, depth=3, bridge_type="Prestressed Concrete Continuous Beam Bridge"))
        print(validator.validate_span_to_depth_ratio(span=60, depth=1.5, bridge_type="Prestressed Concrete Beam"))
        print(validator.validate_span_to_depth_ratio(span=20, depth=1.5, bridge_type="Reinforced Concrete Beam"))
        print(validator.validate_span_to_depth_ratio(span=100, depth=5, bridge_type="Steel Truss Bridge"))
    else:
        print("Skipping span-to-depth tests as bridge_knowledge.py could not be loaded.")

    print("\n--- Material Compatibility Tests ---")
    materials1 = {"main_beams_material": "C50 Prestressed Concrete", "prestressing_steel_type": "ASTM A416 Grade 270"}
    print(validator.validate_material_compatibility(materials1, "Prestressed Concrete Continuous Girder Bridge", span=60))

    materials2 = {"main_beams_material": "C30 Concrete"}
    print(validator.validate_material_compatibility(materials2, "PSC Box Girder", span=50))

    materials3 = {"main_beams_material": "Timber"}
    print(validator.validate_material_compatibility(materials3, "Prestressed Concrete Beam", span=30))

    materials4 = {"main_beams_material": "S355 Steel"}
    print(validator.validate_material_compatibility(materials4, "Steel Truss Bridge", span=100))

    print("\n--- Seismic Requirements Tests ---")
    design_params_test1 = {
        "seismic_design_intensity": "8度",
        "other_seismic_details": "采用减隔震支座",
        "beam_to_pier_connection": "抗震盆式橡胶支座",
        "seismic_considerations_foundation": "桩长增加，提高抗液化能力"
    }
    design_materials_test1 = {"reinforcement_steel_grade": "HRB500D"}
    print(validator.validate_seismic_requirements(design_params_test1, design_materials_test1, seismic_intensity_str="8度"))

    design_params_test2 = {"seismic_design_intensity": "7度", "beam_to_pier_connection": "普通板式橡胶支座，设限位"}
    design_materials_test2 = {"reinforcement_steel_grade": "HRB400"}
    print(validator.validate_seismic_requirements(design_params_test2, design_materials_test2, seismic_intensity_str="7度"))

    design_params_test3 = {}
    design_materials_test3 = {}
    print(validator.validate_seismic_requirements(design_params_test3, design_materials_test3, seismic_intensity_str="9度"))

    print(validator.validate_seismic_requirements(design_params_test1, design_materials_test1, seismic_intensity_str=None))
    print(validator.validate_seismic_requirements(design_params_test3, design_materials_test3, seismic_intensity_str="6度"))

# Final check: remove any problematic comments if they were re-introduced.
# The main content is above.
