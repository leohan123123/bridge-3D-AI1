# Ensure project root is in sys.path for standalone execution
import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from typing import Dict, Any, TypedDict, List, Optional
from prompts.bridge_design_prompts import DESIGN_GENERATION_PROMPT
from knowledge.bridge_templates import BRIDGE_TEMPLATES
from knowledge.standards import DESIGN_STANDARDS_REFERENCES
from knowledge.design_rules import calculate_beam_height
from validators.bridge_validator import BridgeDesignValidator
import logging
import json # Added for the main test block

# Configure basic logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class BridgeDesign(TypedDict):
    bridge_type_selection: Dict[str, str]
    main_structural_parameters: Dict[str, Any]
    material_specifications: Dict[str, str]
    foundation_form_and_size: Dict[str, str]
    key_node_construction: Dict[str, str]
    construction_points: str
    design_notes: List[str]

class DesignGenerator:
    def __init__(self):
        logger.info("Initializing DesignGenerator.")
        self.validator = BridgeDesignValidator()
        # self.llm_service = LLMService() # Would be used if _call_llm_service was real

    def _query_knowledge_base(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Querying knowledge base with requirements: {requirements}")
        span = requirements.get("span_m", 0)
        suitable_template = None
        if 10 <= span <= 40:
            suitable_template = BRIDGE_TEMPLATES.get("简支梁桥")
        elif 30 <= span <= 200:
            suitable_template = BRIDGE_TEMPLATES.get("连续梁桥")

        result = {
            "template_found": suitable_template is not None,
            "template_details": suitable_template or {},
            "relevant_standards": [DESIGN_STANDARDS_REFERENCES.get("General"), DESIGN_STANDARDS_REFERENCES.get("Loads")]
        }
        logger.debug(f"Knowledge base query result: {result}")
        return result

    def _call_llm_service(self, prompt: str) -> Dict[str, Any]:
        logger.info(f"Simulating LLM call for design generation. Prompt snippet: '{prompt[:200]}...'")
        try:
            span_m = 30
            if "main_span_m:" in prompt:
                try:
                    val_str = prompt.split("main_span_m:")[1].split(",")[0].split("}")[0].strip()
                    span_m = int(val_str) # Crude parsing
                except ValueError: # Keep default if parsing fails
                    logger.warning(f"Could not parse span from prompt for mock LLM, using default {span_m}m.")
                    pass

            # Use the updated DESIGN_GENERATION_PROMPT structure for mock response
            mock_response = {
                "bridge_type_selection": {"type": "预应力混凝土连续梁桥", "reason": f"Mocked: Span {span_m}m and seismic conditions favor this."},
                "main_structural_parameters": {
                    "main_span_m": span_m,
                    "other_spans_m": [span_m * 0.75, span_m * 0.75] if span_m > 50 else None,
                    "beam_height_m": calculate_beam_height(span_m, "continuous"),
                    "bridge_width_m": 17.5, # Mocked for 4 lanes
                    "number_of_lanes": 4,
                    "seismic_design_intensity": "8度 (mocked from prompt)"
                },
                "material_specifications": {
                    "main_beams_material": f"C{50 if span_m >=50 else 40} 预应力混凝土",
                    "deck_slab_material": f"C{40 if span_m >=50 else 30} 混凝土",
                    "reinforcement_steel_grade": "HRB400D",
                    "prestressing_steel_type": "高强度低松弛钢绞线 ASTM A416 Grade 270"
                },
                "foundation_form_and_size": {
                    "type": "钻孔灌注桩基础",
                    "dimensions": { "pile_diameter_m": 1.5, "pile_length_m": max(20, span_m/2 + 5), "pile_cap_thickness_m": 2.0 },
                    "seismic_considerations": "Mocked: 桩基承台加厚，增加配筋以满足8度抗震。"
                },
                "key_node_construction": {
                    "beam_to_pier_connection": "盆式橡胶支座，设抗震挡块",
                    "expansion_joints_type": "模数式伸缩缝 D160",
                    "other_seismic_details": "桥墩顶部设置塑性铰区，加强配筋。"
                },
                "construction_points": "采用移动模架逐孔施工或悬臂浇筑法。注意预应力张拉控制和混凝土养护。严格执行抗震施工规范。"
            }
            logger.info("LLM service call simulation successful (mocked).")
            return mock_response
        except Exception as e:
            logger.error(f"Error in LLM service call simulation: {e}", exc_info=True)
            return {key: {"error": str(e)} for key in BridgeDesign.__annotations__ if key != "design_notes"}

    def _perform_parameter_calculation(self, llm_output: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Performing parameter calculation based on LLM output and requirements.")
        logger.debug(f"LLM output for calc: {llm_output}")
        logger.debug(f"Original requirements for calc: {requirements}")
        calculated_design = llm_output.copy()
        if "main_structural_parameters" in calculated_design and "main_span_m" in calculated_design["main_structural_parameters"]:
            span = calculated_design["main_structural_parameters"]["main_span_m"]
            calculated_design["main_structural_parameters"]["estimated_beam_height_from_rule_m"] = calculate_beam_height(span)
        logger.debug(f"Parameter calculation result: {calculated_design}")
        return calculated_design

    def _extract_seismic_intensity_from_requirements(self, requirements: Dict[str, Any]) -> Optional[str]:
        # Check project_conditions first (likely from BridgeRequest)
        if isinstance(requirements.get("project_conditions"), dict) and \
           requirements["project_conditions"].get("seismic_intensity"):
            return str(requirements["project_conditions"]["seismic_intensity"])

        # Check if requirements (potentially from LLM analysis) has environmental_factors
        env_factors = requirements.get("environmental_factors")
        if isinstance(env_factors, str):
            import re
            # Look for patterns like "8度", "intensity 7", "Zone IV", "seismic zone 8"
            match = re.search(r'(\d+\s*度|\b[Ii]ntensity\s*\d+|\bZone\s*[IVXLCDM]+|\bseismic zone\s*\d+)', env_factors, re.IGNORECASE)
            if match:
                return match.group(1)
            # Fallback if specific pattern not found but keyword exists
            search_terms = ["seismic", "earthquake", "抗震"]
            if any(term in env_factors.lower() for term in search_terms):
                return env_factors

        # Check other possible keys if BridgeService directly passed its refined_params
        if requirements.get("seismic_intensity"):
             return str(requirements.get("seismic_intensity"))
        if requirements.get("seismic_zone_description"):
             return str(requirements.get("seismic_zone_description"))

        logger.warning(f"Could not extract specific seismic intensity from requirements: {requirements}")
        return None # Return None if no specific intensity found

    def _verify_design(self, design_scheme: Dict[str, Any], original_requirements: Dict[str, Any]) -> List[str]:
        logger.info("Verifying design scheme...")
        notes = []

        bridge_type = design_scheme.get("bridge_type_selection", {}).get("type", "Unknown")
        main_params = design_scheme.get("main_structural_parameters", {})
        materials = design_scheme.get("material_specifications", {})
        foundation_params = design_scheme.get("foundation_form_and_size", {})

        span = main_params.get("main_span_m")
        depth = main_params.get("beam_height_m") or main_params.get("estimated_beam_height_from_rule_m")

        if span and depth:
            is_valid_sdr, sdr_message = self.validator.validate_span_to_depth_ratio(span, depth, bridge_type)
            notes.append(sdr_message)
            if not is_valid_sdr: logger.warning(f"Span-to-Depth Validation: {sdr_message}")
        else:
            notes.append("Span-to-depth ratio check skipped: Span or depth not available.")
            logger.debug("Skipping span-to-depth validation: span or depth missing.")

        if materials and bridge_type != "Unknown" and span:
            is_valid_mc, mc_message = self.validator.validate_material_compatibility(materials, bridge_type, span)
            notes.append(mc_message)
            if not is_valid_mc: logger.warning(f"Material Compatibility Validation: {mc_message}")
        else:
            notes.append("Material compatibility check skipped: Insufficient data.")
            logger.debug("Skipping material compatibility validation: insufficient data.")

        seismic_intensity_from_llm_output = main_params.get("seismic_design_intensity")
        seismic_intensity_from_original_req = self._extract_seismic_intensity_from_requirements(original_requirements)
        effective_seismic_str = seismic_intensity_from_llm_output or seismic_intensity_from_original_req
        logger.debug(f"Effective seismic intensity for validation: '{effective_seismic_str}' (LLM: '{seismic_intensity_from_llm_output}', OriginalReq: '{seismic_intensity_from_original_req}')")

        temp_seismic_check_params = main_params.copy()
        temp_seismic_check_params.update(design_scheme.get("key_node_construction", {}))
        if "seismic_considerations" in foundation_params: # Add foundation seismic considerations
            temp_seismic_check_params["seismic_considerations_foundation"] = foundation_params["seismic_considerations"]

        is_valid_sr, sr_message = self.validator.validate_seismic_requirements(
            design_params=temp_seismic_check_params,
            design_materials=materials,
            seismic_intensity_str=effective_seismic_str
        )
        notes.append(sr_message)
        if not is_valid_sr: logger.warning(f"Seismic Requirements Validation: {sr_message}")

        # Consolidate final note based on validation outcomes
        if all(("skipped" in note.lower() or "passed" in note.lower() or "is within the typical range" in note.lower() or "seem to be addressed" in note.lower() or "no specific range" in note.lower())
               and not ("Warning:" in note or "outside the typical range" in note or "does not clearly state" in note or "no prestressing steel type defined" in note) for note in notes if isinstance(note, str)):
            final_summary_note = "Design verification completed. All checks passed or were non-critical."
        else:
            final_summary_note = "Design verification completed with warnings or non-critical findings. Please review notes."

        notes.append(final_summary_note)
        logger.info(final_summary_note + f" Full notes: {notes}")
        return notes

    def generate_design_scheme(self, requirements: Dict[str, Any]) -> BridgeDesign:
        logger.info(f"Starting design scheme generation for requirements: {requirements}")
        try:
            project_conditions_str = str(requirements.get("project_conditions", "Standard urban environment."))
            design_constraints_str = str(requirements.get("design_constraints", "Minimize environmental impact."))

            requirements_for_prompt_str = "; ".join([f"{k}: {v}" for k,v in requirements.items()]) if isinstance(requirements, dict) else str(requirements)

            kb_results = self._query_knowledge_base(requirements)
            relevant_standards_str = ", ".join(kb_results.get("relevant_standards", ["AASHTO LRFD"]))

            prompt = DESIGN_GENERATION_PROMPT.format(
                requirements=requirements_for_prompt_str,
                conditions=project_conditions_str,
                constraints=design_constraints_str,
                standards=relevant_standards_str
            )
            logger.debug(f"Formatted LLM prompt for design generation (first 300 chars): {prompt[:300]}...")

            llm_generated_scheme = self._call_llm_service(prompt)
            if any(isinstance(val, dict) and "error" in str(val).lower() for val in llm_generated_scheme.values()):
                 logger.error(f"LLM service returned an error structure: {llm_generated_scheme}")
                 return {
                    "bridge_type_selection": {"type": "Error", "reason": "LLM service failed"},
                    "main_structural_parameters": {"error": "LLM service failed"},
                    "material_specifications": {"error": "LLM service failed"},
                    "foundation_form_and_size": {"error": "LLM service failed"},
                    "key_node_construction": {"error": "LLM service failed"},
                    "construction_points": "LLM service failed",
                    "design_notes": ["Critical error: LLM service failed to generate design."]
                } # type: ignore

            calculated_scheme = self._perform_parameter_calculation(llm_generated_scheme, requirements)
            verification_notes = self._verify_design(calculated_scheme, requirements)

            final_design: BridgeDesign = {
                "bridge_type_selection": calculated_scheme.get("bridge_type_selection", {"type": "Unknown", "reason": "N/A"}),
                "main_structural_parameters": calculated_scheme.get("main_structural_parameters", {}),
                "material_specifications": calculated_scheme.get("material_specifications", {}),
                "foundation_form_and_size": calculated_scheme.get("foundation_form_and_size", {}),
                "key_node_construction": calculated_scheme.get("key_node_construction", {}),
                "construction_points": calculated_scheme.get("construction_points", "N/A"),
                "design_notes": verification_notes
            }
            logger.info(f"Design scheme generated successfully. Bridge Type: {final_design['bridge_type_selection'].get('type')}")
            return final_design
        except Exception as e:
            logger.error(f"Unexpected error in generate_design_scheme: {e}", exc_info=True)
            return {
                "bridge_type_selection": {"type": "Error", "reason": str(e)},
                "main_structural_parameters": {"error": str(e)},
                "material_specifications": {"error": str(e)},
                "foundation_form_and_size": {"error": str(e)},
                "key_node_construction": {"error": str(e)},
                "construction_points": "Error in design generation.",
                "design_notes": [f"Critical error: {str(e)}"]
            } # type: ignore

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("--- Running DesignGenerator Standalone Test ---")

    # Ensure validator can find knowledge base by adjusting path if necessary for standalone run
    # This sys.path modification is at the top of the file now.

    generator = DesignGenerator()
    sample_requirements_for_generator = {
        "span_m": 60,
        "user_requirements_summary": "预应力混凝土连续梁桥, 60m跨, 双向四车道, 8度区 (This is a summary, actual LLM input would be more detailed)",
        "project_conditions": {"seismic_intensity": "8度", "road_lanes": "双向四车道", "site_geology": "Soft clay"},
        "design_constraints": {"aesthetic_requirements": "Modern look", "budget": "Medium"},
        "environmental_factors": "seismic zone 8度, urban area", # Example of how LLM might have extracted this
        # Adding other fields that might be present in 'requirements' if it's from BridgeService's refined_params
        "bridge_type_preference": "预应力混凝土连续梁桥",
        "span_length_description": "60m",
        "load_requirements": "Standard Highway Load (assumed for 4 lanes)",
        "specific_materials": "Prestressed Concrete"
    }

    design_output = generator.generate_design_scheme(sample_requirements_for_generator)

    logger.info("\n--- Generated Bridge Design Scheme (Standalone Test) ---")
    logger.info(json.dumps(design_output, indent=2, ensure_ascii=False))
    logger.info("--- End of DesignGenerator Standalone Test ---")
