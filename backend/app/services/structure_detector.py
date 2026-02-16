"""Structure detection service with YOLO and fallback options."""

from typing import Literal

import numpy as np
from app.models.schemas import StructuralModel, Node, Member, Support
from app.services.yolo_detector import get_detector


DetectionMethod = Literal["yolo", "mock"]


def detect_structure(image: np.ndarray, scale_factor: float) -> tuple[StructuralModel, DetectionMethod]:
    """
    Detect structural elements from image using YOLO or fallback methods.
    
    Tries YOLO detection first if model is available, otherwise returns mock model.
    
    Args:
        image: Input image as numpy array
        scale_factor: Scale factor (pixels per mm)
        
    Returns:
        Tuple of (StructuralModel, detection_method)
    """
    # Try YOLO detection first
    detector = get_detector()
    
    if detector.model_loaded:
        try:
            detections = detector.detect(image)
            
            # Only use YOLO results if we got meaningful detections
            if len(detections) >= 3:  # At least some joints detected
                model = detector.detections_to_model(detections, scale_factor)
                
                # Validate model has minimum required elements
                if len(model.nodes) >= 2 and len(model.members) >= 1:
                    return model, "yolo"
        except Exception as e:
            print(f"YOLO detection failed: {e}")
    
    # Fall back to mock model
    return _generate_mock_truss(), "mock"


def _generate_mock_truss() -> StructuralModel:
    """
    Generate mock Warren truss for testing when YOLO is unavailable.
    
    Returns:
        StructuralModel with mock Warren truss
    """
    
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
