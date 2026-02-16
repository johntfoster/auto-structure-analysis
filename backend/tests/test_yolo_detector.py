"""Tests for YOLO detector service."""

import numpy as np
import pytest

from app.services.yolo_detector import Detection, YOLODetector


def test_detection_model_validation():
    """Test that Detection model validates correctly."""
    # Valid detection
    det = Detection(
        class_name="joint",
        confidence=0.95,
        bbox=[100.0, 200.0, 120.0, 220.0]
    )
    assert det.class_name == "joint"
    assert det.confidence == 0.95
    assert len(det.bbox) == 4
    
    # Invalid confidence (should still work, pydantic doesn't enforce range)
    det2 = Detection(
        class_name="member",
        confidence=1.5,  # Over 1.0
        bbox=[0, 0, 10, 10]
    )
    assert det2.confidence == 1.5


def test_yolo_detector_initialization():
    """Test YOLODetector can be initialized."""
    detector = YOLODetector(model_path="nonexistent.pt")
    assert detector.model_loaded is False
    assert detector.model is None


def test_detect_without_model():
    """Test detection returns empty list when model not loaded."""
    detector = YOLODetector(model_path="nonexistent.pt")
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    detections = detector.detect(image)
    assert detections == []


def test_cluster_joints_basic():
    """Test joint clustering removes duplicates."""
    detector = YOLODetector()
    
    # Create overlapping detections
    dets = [
        Detection(class_name="joint", confidence=0.9, bbox=[100, 100, 120, 120]),
        Detection(class_name="joint", confidence=0.85, bbox=[105, 105, 125, 125]),  # Overlaps
        Detection(class_name="joint", confidence=0.8, bbox=[200, 200, 220, 220]),  # Different
    ]
    
    clusters = detector._cluster_joints(dets)
    
    # Should have 2 clusters (first two merged, third separate)
    assert len(clusters) == 2


def test_cluster_joints_empty():
    """Test clustering with no detections."""
    detector = YOLODetector()
    clusters = detector._cluster_joints([])
    assert clusters == []


def test_compute_iou():
    """Test IoU computation."""
    detector = YOLODetector()
    
    # Identical boxes
    bbox1 = [0, 0, 10, 10]
    bbox2 = [0, 0, 10, 10]
    iou = detector._compute_iou(bbox1, bbox2)
    assert iou == 1.0
    
    # No overlap
    bbox1 = [0, 0, 10, 10]
    bbox2 = [20, 20, 30, 30]
    iou = detector._compute_iou(bbox1, bbox2)
    assert iou == 0.0
    
    # Partial overlap
    bbox1 = [0, 0, 10, 10]
    bbox2 = [5, 5, 15, 15]
    iou = detector._compute_iou(bbox1, bbox2)
    assert 0 < iou < 1


def test_detections_to_model_basic():
    """Test converting detections to structural model."""
    detector = YOLODetector()
    
    # Create mock detections
    detections = [
        Detection(class_name="joint", confidence=0.9, bbox=[100, 100, 120, 120]),
        Detection(class_name="joint", confidence=0.9, bbox=[200, 100, 220, 120]),
        Detection(class_name="joint", confidence=0.9, bbox=[150, 200, 170, 220]),
        Detection(class_name="member", confidence=0.85, bbox=[100, 100, 200, 100]),
        Detection(class_name="member", confidence=0.85, bbox=[100, 100, 150, 200]),
        Detection(class_name="support_pin", confidence=0.8, bbox=[95, 95, 115, 115]),
        Detection(class_name="support_roller", confidence=0.8, bbox=[195, 95, 215, 115]),
    ]
    
    model = detector.detections_to_model(detections, scale_factor=1.0)
    
    # Check that we got nodes, members, and supports
    assert len(model.nodes) >= 2
    assert len(model.members) >= 1
    assert len(model.supports) >= 1
    
    # Check node IDs are unique
    node_ids = [n.id for n in model.nodes]
    assert len(node_ids) == len(set(node_ids))
    
    # Check supports reference existing nodes
    support_node_ids = [s.node_id for s in model.supports]
    for support_id in support_node_ids:
        assert support_id in node_ids


def test_detections_to_model_empty():
    """Test converting empty detections."""
    detector = YOLODetector()
    
    model = detector.detections_to_model([], scale_factor=1.0)
    
    assert len(model.nodes) == 0
    assert len(model.members) == 0
    assert len(model.supports) == 0


def test_detections_to_model_scale_factor():
    """Test that scale factor is applied correctly."""
    detector = YOLODetector()
    
    detections = [
        Detection(class_name="joint", confidence=0.9, bbox=[100, 200, 120, 220]),
    ]
    
    # With scale factor 1.0
    model1 = detector.detections_to_model(detections, scale_factor=1.0)
    node1 = model1.nodes[0]
    
    # With scale factor 2.0 (2 pixels per mm)
    model2 = detector.detections_to_model(detections, scale_factor=2.0)
    node2 = model2.nodes[0]
    
    # Coordinates should be halved with scale factor 2.0
    assert abs(node2.x - node1.x / 2) < 0.1
    assert abs(node2.y - node1.y / 2) < 0.1


def test_find_nearest_node():
    """Test finding nearest node to a bbox."""
    from app.models.schemas import Node
    
    detector = YOLODetector()
    
    nodes = [
        Node(id="N0", x=100, y=100),
        Node(id="N1", x=200, y=200),
        Node(id="N2", x=300, y=100),
    ]
    
    # Bbox near first node
    bbox = [95, 95, 105, 105]
    nearest = detector._find_nearest_node(bbox, nodes)
    assert nearest.id == "N0"
    
    # Bbox near second node
    bbox = [195, 195, 205, 205]
    nearest = detector._find_nearest_node(bbox, nodes)
    assert nearest.id == "N1"


def test_find_nearest_node_empty():
    """Test finding nearest node with no nodes."""
    detector = YOLODetector()
    
    bbox = [100, 100, 120, 120]
    nearest = detector._find_nearest_node(bbox, [])
    assert nearest is None


def test_infer_members():
    """Test member inference from detections."""
    from app.models.schemas import Node
    
    detector = YOLODetector()
    
    nodes = [
        Node(id="N0", x=100, y=100),
        Node(id="N1", x=200, y=100),
        Node(id="N2", x=150, y=200),
    ]
    
    member_dets = [
        Detection(class_name="member", confidence=0.85, bbox=[100, 100, 200, 100]),
        Detection(class_name="member", confidence=0.85, bbox=[100, 100, 150, 200]),
    ]
    
    members = detector._infer_members(member_dets, nodes)
    
    # Should have created members
    assert len(members) == 2
    
    # Check member IDs are unique
    member_ids = [m.id for m in members]
    assert len(member_ids) == len(set(member_ids))
    
    # Check members reference existing nodes
    for member in members:
        assert any(n.id == member.start_node for n in nodes)
        assert any(n.id == member.end_node for n in nodes)
