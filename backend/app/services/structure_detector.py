"""Structure detection service (placeholder for YOLO-based detection)."""

import numpy as np
from app.models.schemas import StructuralModel, Node, Member, Support


def detect_structure(image: np.ndarray, scale_factor: float) -> StructuralModel:
    """
    Detect structural elements from image.
    
    Currently returns a mock truss model for testing.
    Future: Will use YOLO to detect beams, columns, joints from image.
    
    Args:
        image: Input image as numpy array
        scale_factor: Scale factor (pixels per mm)
        
    Returns:
        StructuralModel with detected nodes, members, and supports
    """
    # Mock simple truss model - Warren truss style
    # Creates a 3-panel truss with supports at ends
    
    # Panel dimensions in mm
    panel_width = 1000.0  # mm
    height = 600.0  # mm
    num_panels = 3
    
    # Bottom chord nodes
    nodes = []
    for i in range(num_panels + 1):
        nodes.append(Node(
            id=f"B{i}",
            x=i * panel_width,
            y=0.0
        ))
    
    # Top chord nodes
    for i in range(num_panels + 1):
        nodes.append(Node(
            id=f"T{i}",
            x=i * panel_width,
            y=height
        ))
    
    # Members
    members = []
    
    # Bottom chord
    for i in range(num_panels):
        members.append(Member(
            id=f"BC{i}",
            start_node=f"B{i}",
            end_node=f"B{i+1}",
            material="steel"
        ))
    
    # Top chord
    for i in range(num_panels):
        members.append(Member(
            id=f"TC{i}",
            start_node=f"T{i}",
            end_node=f"T{i+1}",
            material="steel"
        ))
    
    # Verticals
    for i in range(num_panels + 1):
        members.append(Member(
            id=f"V{i}",
            start_node=f"B{i}",
            end_node=f"T{i}",
            material="steel"
        ))
    
    # Diagonals (alternating)
    for i in range(num_panels):
        if i % 2 == 0:
            # Diagonal up-right
            members.append(Member(
                id=f"D{i}",
                start_node=f"B{i}",
                end_node=f"T{i+1}",
                material="steel"
            ))
        else:
            # Diagonal down-right
            members.append(Member(
                id=f"D{i}",
                start_node=f"T{i}",
                end_node=f"B{i+1}",
                material="steel"
            ))
    
    # Supports
    supports = [
        Support(node_id="B0", type="pin"),      # Left support (pin)
        Support(node_id=f"B{num_panels}", type="roller")  # Right support (roller)
    ]
    
    return StructuralModel(
        nodes=nodes,
        members=members,
        supports=supports
    )
