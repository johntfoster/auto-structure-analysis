"""Classical computer vision fallback for structure detection."""

from typing import Optional

import cv2
import numpy as np
from pydantic import BaseModel

from app.models.schemas import StructuralModel, Node, Member, Support


class Point(BaseModel):
    """2D point."""
    x: float
    y: float


class Line(BaseModel):
    """Line segment."""
    start: Point
    end: Point


def detect_lines(image: np.ndarray, 
                min_line_length: int = 50,
                max_line_gap: int = 10) -> list[Line]:
    """
    Detect lines in image using Hough transform.
    
    Args:
        image: Input image (BGR or grayscale)
        min_line_length: Minimum line length in pixels
        max_line_gap: Maximum gap between line segments
        
    Returns:
        List of detected lines
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
    
    # Detect lines using probabilistic Hough transform
    lines_raw = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=50,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )
    
    if lines_raw is None:
        return []
    
    # Convert to Line objects
    lines = []
    for line in lines_raw:
        x1, y1, x2, y2 = line[0]
        lines.append(Line(
            start=Point(x=float(x1), y=float(y1)),
            end=Point(x=float(x2), y=float(y2))
        ))
    
    return lines


def detect_joints(lines: list[Line], distance_threshold: float = 10.0) -> list[Point]:
    """
    Detect joints as line intersections.
    
    Args:
        lines: List of detected lines
        distance_threshold: Maximum distance to consider points as same joint
        
    Returns:
        List of joint positions
    """
    if not lines:
        return []
    
    # Find all line intersections
    intersections = []
    
    for i, line1 in enumerate(lines):
        for line2 in lines[i+1:]:
            intersection = _line_intersection(line1, line2)
            if intersection is not None:
                intersections.append(intersection)
    
    # Also add line endpoints as potential joints
    for line in lines:
        intersections.append(line.start)
        intersections.append(line.end)
    
    # Cluster nearby points
    joints = _cluster_points(intersections, distance_threshold)
    
    return joints


def _line_intersection(line1: Line, line2: Line) -> Optional[Point]:
    """Compute intersection point of two lines (if exists)."""
    x1, y1 = line1.start.x, line1.start.y
    x2, y2 = line1.end.x, line1.end.y
    x3, y3 = line2.start.x, line2.start.y
    x4, y4 = line2.end.x, line2.end.y
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    if abs(denom) < 1e-6:
        return None  # Lines are parallel
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    # Check if intersection is within both line segments
    if 0 <= t <= 1 and 0 <= u <= 1:
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return Point(x=x, y=y)
    
    return None


def _cluster_points(points: list[Point], threshold: float) -> list[Point]:
    """Cluster nearby points and return cluster centers."""
    if not points:
        return []
    
    clusters = []
    used = [False] * len(points)
    
    for i, point in enumerate(points):
        if used[i]:
            continue
        
        # Start new cluster
        cluster_points = [point]
        used[i] = True
        
        # Find nearby points
        for j in range(i + 1, len(points)):
            if used[j]:
                continue
            
            dist = ((point.x - points[j].x)**2 + (point.y - points[j].y)**2)**0.5
            if dist < threshold:
                cluster_points.append(points[j])
                used[j] = True
        
        # Compute cluster center
        avg_x = sum(p.x for p in cluster_points) / len(cluster_points)
        avg_y = sum(p.y for p in cluster_points) / len(cluster_points)
        clusters.append(Point(x=avg_x, y=avg_y))
    
    return clusters


def lines_to_model(lines: list[Line], joints: list[Point], scale_factor: float = 1.0) -> StructuralModel:
    """
    Convert detected lines and joints to structural model.
    
    Args:
        lines: Detected lines (members)
        joints: Detected joints (nodes)
        scale_factor: Pixels per mm conversion factor
        
    Returns:
        StructuralModel with nodes and members
    """
    # Create nodes from joints
    nodes = []
    for i, joint in enumerate(joints):
        x_mm = joint.x / scale_factor if scale_factor > 0 else joint.x
        y_mm = joint.y / scale_factor if scale_factor > 0 else joint.y
        
        nodes.append(Node(
            id=f"N{i}",
            x=x_mm,
            y=y_mm
        ))
    
    # Create members from lines by finding nearest joints
    members = []
    for i, line in enumerate(lines):
        # Find nearest joint to line start
        start_node = _find_nearest_node_to_point(line.start, nodes, scale_factor)
        # Find nearest joint to line end
        end_node = _find_nearest_node_to_point(line.end, nodes, scale_factor)
        
        if start_node and end_node and start_node.id != end_node.id:
            members.append(Member(
                id=f"M{i}",
                start_node=start_node.id,
                end_node=end_node.id,
                material="steel"
            ))
    
    # Heuristic: assume bottom-left and bottom-right joints are supports
    # Sort nodes by y-coordinate (descending, since y increases downward)
    sorted_nodes = sorted(nodes, key=lambda n: n.y, reverse=True)
    
    supports = []
    if len(sorted_nodes) >= 2:
        # Get bottom nodes
        bottom_nodes = sorted_nodes[:min(3, len(sorted_nodes))]
        
        # Leftmost bottom node is pin
        leftmost = min(bottom_nodes, key=lambda n: n.x)
        supports.append(Support(node_id=leftmost.id, type="pin"))
        
        # Rightmost bottom node is roller
        rightmost = max(bottom_nodes, key=lambda n: n.x)
        if rightmost.id != leftmost.id:
            supports.append(Support(node_id=rightmost.id, type="roller"))
    
    return StructuralModel(
        nodes=nodes,
        members=members,
        supports=supports
    )


def _find_nearest_node_to_point(point: Point, nodes: list[Node], scale_factor: float) -> Optional[Node]:
    """Find nearest node to a point."""
    if not nodes:
        return None
    
    min_dist = float('inf')
    nearest = None
    
    for node in nodes:
        # Convert node coordinates back to pixels for comparison
        node_x_px = node.x * scale_factor if scale_factor > 0 else node.x
        node_y_px = node.y * scale_factor if scale_factor > 0 else node.y
        
        dist = ((point.x - node_x_px)**2 + (point.y - node_y_px)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest = node
    
    return nearest


def detect_structure_from_edges(image: np.ndarray, scale_factor: float = 1.0) -> StructuralModel:
    """
    Detect structure using edge detection and line finding.
    
    Args:
        image: Input image
        scale_factor: Pixels per mm conversion
        
    Returns:
        StructuralModel
    """
    # Detect lines
    lines = detect_lines(image)
    
    # Detect joints
    joints = detect_joints(lines)
    
    # Convert to model
    model = lines_to_model(lines, joints, scale_factor)
    
    return model
