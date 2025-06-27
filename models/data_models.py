from pydantic import BaseModel
from typing import Optional, Dict, List

class BridgeRequest(BaseModel):
    user_requirements: str  # 用户需求描述
    project_conditions: Optional[Dict] = None  # 项目条件
    design_constraints: Optional[Dict] = None  # 设计约束

class BridgeDesign(BaseModel):
    design_id: str
    bridge_type: str  # 梁桥/拱桥/斜拉桥/悬索桥
    span_lengths: List[float]  # 跨径组合
    bridge_width: float
    design_load: str
    main_girder: Dict  # 主梁参数
    pier_design: Dict  # 桥墩设计
    foundation: Dict   # 基础设计
    materials: Dict    # 材料规格

if __name__ == "__main__":
    # Example Usage
    request_example = BridgeRequest(
        user_requirements="Design a bridge for a river crossing.",
        project_conditions={"location": "urban", "traffic_volume": "high"},
        design_constraints={"max_height": 50, "aesthetic_requirements": "modern"}
    )
    print("BridgeRequest Example:", request_example.model_dump_json(indent=2))

    design_example = BridgeDesign(
        design_id="BD001",
        bridge_type="斜拉桥",
        span_lengths=[150.0, 300.0, 150.0],
        bridge_width=25.0,
        design_load="Highway Class A",
        main_girder={"type": "steel box", "depth": 3.0},
        pier_design={"type": "concrete", "shape": "rectangular"},
        foundation={"type": "pile", "depth": 20.0},
        materials={"deck": "concrete C50", "cables": "high-strength steel"}
    )
    print("\nBridgeDesign Example:", design_example.model_dump_json(indent=2))
