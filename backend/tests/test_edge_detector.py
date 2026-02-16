"""Tests for edge detection fallback service."""

import cv2
import numpy as np
import pytest

from app.services.edge_detector import (
    detect_lines,
    detect_joints,
    lines_to_model,
    detect_structure_from_edges,
    Point,
    Line,
    _cluster_points,
    _line_intersection,
)


def create_test_image_with_lines():
    """Create a test image with known lines."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    
    # Draw a simple triangle
    cv2.line(img, (100, 300), (300, 100), (0, 0, 0), 3)  # Left edge
    cv2.line(img, (300, 100), (500, 300), (0, 0, 0), 3)  # Right edge
    cv2.line(img, (100, 300), (500, 300), (0, 0, 0), 3)  # Base
    
    return img


def test_detect_lines_basic():
    """Test that lines are detected in a simple image."""
    img = create_test_image_with_lines()
    lines = detect_lines(img)
    
    # Should detect at least 3 lines (might detect more due to splitting)
    assert len(lines) >= 3
    
    # Check that Line objects are valid
    for line in lines:
        assert isinstance(line, Line)
        assert isinstance(line.start, Point)
        assert isinstance(line.end, Point)


def test_detect_lines_empty_image():
    """Test line detection on empty image."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    lines = detect_lines(img)
    
    # Should detect no lines or very few
    assert len(lines) < 5


def test_detect_joints_basic():
    """Test joint detection at known intersections."""
    # Create lines that intersect at known points
    lines = [
        Line(start=Point(x=100, y=300), end=Point(x=300, y=100)),
        Line(start=Point(x=300, y=100), end=Point(x=500, y=300)),
        Line(start=Point(x=100, y=300), end=Point(x=500, y=300)),
    ]
    
    joints = detect_joints(lines, distance_threshold=10.0)
    
    # Should detect at least 3 joints (the vertices)
    assert len(joints) >= 3
    
    # Check that joints are Point objects
    for joint in joints:
        assert isinstance(joint, Point)


def test_detect_joints_empty():
    """Test joint detection with no lines."""
    joints = detect_joints([], distance_threshold=10.0)
    assert len(joints) == 0


def test_line_intersection_basic():
    """Test line intersection calculation."""
    # Two lines that intersect at (150, 150)
    line1 = Line(start=Point(x=100, y=100), end=Point(x=200, y=200))
    line2 = Line(start=Point(x=100, y=200), end=Point(x=200, y=100))
    
    intersection = _line_intersection(line1, line2)
    
    assert intersection is not None
    assert abs(intersection.x - 150) < 1
    assert abs(intersection.y - 150) < 1


def test_line_intersection_parallel():
    """Test that parallel lines return None."""
    line1 = Line(start=Point(x=0, y=0), end=Point(x=100, y=0))
    line2 = Line(start=Point(x=0, y=10), end=Point(x=100, y=10))
    
    intersection = _line_intersection(line1, line2)
    assert intersection is None


def test_line_intersection_no_overlap():
    """Test lines that don't intersect within segments."""
    # Lines that would intersect if extended, but not within segments
    line1 = Line(start=Point(x=0, y=0), end=Point(x=10, y=10))
    line2 = Line(start=Point(x=20, y=0), end=Point(x=30, y=10))
    
    intersection = _line_intersection(line1, line2)
    # May or may not intersect depending on extension
    # This is just checking it doesn't crash


def test_cluster_points_basic():
    """Test point clustering."""
    points = [
        Point(x=100, y=100),
        Point(x=102, y=101),  # Close to first
        Point(x=200, y=200),  # Far away
        Point(x=199, y=201),  # Close to third
    ]
    
    clusters = _cluster_points(points, threshold=5.0)
    
    # Should cluster into 2 groups
    assert len(clusters) == 2


def test_cluster_points_empty():
    """Test clustering with no points."""
    clusters = _cluster_points([], threshold=10.0)
    assert len(clusters) == 0


def test_lines_to_model_basic():
    """Test converting lines and joints to structural model."""
    lines = [
        Line(start=Point(x=100, y=300), end=Point(x=300, y=100)),
        Line(start=Point(x=300, y=100), end=Point(x=500, y=300)),
        Line(start=Point(x=100, y=300), end=Point(x=500, y=300)),
    ]
    
    joints = [
        Point(x=100, y=300),
        Point(x=300, y=100),
        Point(x=500, y=300),
    ]
    
    model = lines_to_model(lines, joints, scale_factor=1.0)
    
    # Should have 3 nodes
    assert len(model.nodes) == 3
    
    # Should have members
    assert len(model.members) >= 1
    
    # Should have supports (heuristic-based)
    assert len(model.supports) >= 1


def test_lines_to_model_empty():
    """Test converting empty lines and joints."""
    model = lines_to_model([], [], scale_factor=1.0)
    
    assert len(model.nodes) == 0
    assert len(model.members) == 0


def test_lines_to_model_scale_factor():
    """Test that scale factor is applied."""
    lines = [
        Line(start=Point(x=100, y=200), end=Point(x=200, y=200)),
    ]
    
    joints = [
        Point(x=100, y=200),
        Point(x=200, y=200),
    ]
    
    # With scale factor 1.0
    model1 = lines_to_model(lines, joints, scale_factor=1.0)
    
    # With scale factor 2.0
    model2 = lines_to_model(lines, joints, scale_factor=2.0)
    
    # Coordinates should be halved with scale factor 2.0
    assert abs(model2.nodes[0].x - model1.nodes[0].x / 2) < 0.1


def test_detect_structure_from_edges():
    """Test full edge-based detection pipeline."""
    img = create_test_image_with_lines()
    
    model = detect_structure_from_edges(img, scale_factor=1.0)
    
    # Should detect some structure
    assert len(model.nodes) >= 2
    
    # Nodes should have valid coordinates
    for node in model.nodes:
        assert node.x >= 0
        assert node.y >= 0


def test_detect_structure_from_edges_empty():
    """Test edge detection on empty image."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    
    model = detect_structure_from_edges(img, scale_factor=1.0)
    
    # May have very few or no elements
    # Just checking it doesn't crash
    assert isinstance(model.nodes, list)
    assert isinstance(model.members, list)
