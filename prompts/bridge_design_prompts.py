# Prompts for LLM-based bridge design generation

DESIGN_GENERATION_PROMPT = """
基于以下桥梁设计需求，生成详细的设计方案：

设计需求：{requirements}
项目条件：{conditions}
设计约束：{constraints}
相关规范：{standards}

请按照以下结构输出详细的设计方案，确保充分考虑抗震设计要求（如果适用）：
1. 桥梁类型选择及理由:
   - type: (e.g., "预应力混凝土连续梁桥")
   - reason: (说明选择理由，包括如何满足跨度、荷载、抗震<如果适用>等要求)
2. 主要结构参数:
   - main_span_m: (e.g., 60)
   - other_spans_m: (e.g., [45, 45] or null)
   - beam_height_m: (e.g., 3.0)
   - bridge_width_m: (根据车道数和人行道等需求确定, e.g., 17.0 for 双向四车道)
   - number_of_lanes: (e.g., 4)
   - seismic_design_intensity: (e.g., "8度" or null, 说明采取了哪些总体抗震措施或参数调整)
3. 材料规格选择:
   - main_beams_material: (e.g., "C50预应力混凝土")
   - deck_slab_material: (e.g., "C40混凝土")
   - reinforcement_steel_grade: (e.g., "HRB400/HRB500")
   - prestressing_steel_type: (e.g., "高强度低松弛钢绞线 ASTM A416 Grade 270")
4. 基础形式和尺寸:
   - type: (e.g., "钻孔灌注桩基础", "扩大基础")
   - dimensions: (e.g., {{ "pile_diameter_m": 1.5, "pile_length_m": 25, "pile_cap_thickness_m": 2.0 }})
   - seismic_considerations: (说明基础设计如何满足抗震要求, e.g., "采用大直径桩，增加桩长以穿越液化土层")
5. 关键节点构造:
   - beam_to_pier_connection: (e.g., "盆式橡胶支座，考虑多向位移和抗震限位装置")
   - expansion_joints_type: (e.g., "模数式伸缩缝")
   - other_seismic_details: (e.g., "桥墩塑性铰区设计", "防落梁装置")
6. 施工要点说明: (简述关键施工步骤和注意事项，例如预应力张拉顺序、连续梁合龙方案等)

确保设计符合输入的相关规范，所有参数专业且合理，构造详细可行。请为每个结构化的部分提供JSON兼容的字典格式。
"""

# Example of another prompt, perhaps for optimization or a specific component design
OPTIMIZATION_PROMPT_TEMPLATE = """
Given the following bridge design:
{current_design}

And the following optimization goals:
{optimization_goals}

Suggest modifications to optimize the design. Provide:
1. Optimized parameters (changes to the original design)
2. Reasons for changes
3. Potential trade-offs
"""

if __name__ == '__main__':
    # Example of how the prompt might be used (for testing purposes)
    sample_req = {
        "span_m": 75,
        "clearance_height_m": 6,
        "number_of_lanes": 4
    }
    sample_cond = "River crossing with moderate boat traffic."
    sample_constr = "Must use precast concrete elements due to site access limitations."
    sample_std = "AASHTO LRFD, JTG D60-2015"

    formatted_prompt = DESIGN_GENERATION_PROMPT.format(
        requirements=str(sample_req), # Convert dict to string for simple formatting
        conditions=sample_cond,
        constraints=sample_constr,
        standards=sample_std
    )
    print("--- Sample Design Generation Prompt ---")
    print(formatted_prompt)
    print("--- End of Sample Prompt ---")
