# Prompts for LLM-based bridge design generation

DESIGN_GENERATION_PROMPT = """
基于以下桥梁设计需求，生成详细的设计方案：

设计需求：{requirements}
项目条件：{conditions}
设计约束：{constraints}
相关规范：{standards}

请按照以下结构输出设计方案：
1. 桥梁类型选择及理由 (e.g., {{ "type": "简支梁桥", "reason": "..." }})
2. 主要结构参数 (e.g., {{ "main_span_m": 30, "beam_height_m": 1.8, "bridge_width_m": 12 }})
3. 材料规格选择 (e.g., {{ "main_beams": "C50 Concrete", "deck_slab": "C40 Concrete" }})
4. 基础形式和尺寸 (e.g., {{ "type": "Pile Foundation", "pile_diameter_m": 1.5 }})
5. 关键节点构造 (e.g., {{ "beam_to_pier_connection": "Elastomeric bearings" }})
6. 施工要点说明 (as a string)

确保设计符合相关规范，参数合理，构造可行。请提供JSON-like structures for each section where appropriate, as indicated in the examples.
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
