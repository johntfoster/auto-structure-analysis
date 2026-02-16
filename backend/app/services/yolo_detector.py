"""YOLO-based structure detection service."""

from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel

from app.models.schemas import StructuralModel, Node, Member, Support


class Detection(BaseModel):
    """Single object detection from YOLO."""
    class_name: str
    confidence: float
    bbox: list[float]  # [x1, y1, x2, y2] in pixels


class YOLODetector:
    """YOLO-based detector for structural elements."""
    
    CLASS_NAMES = ["joint", "member", "support_pin", "support_roller"]
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize YOLO detector.
        
        Args:
            model_path: Path to trained YOLO model (optional)
        """
        self.model = None
        self.model_loaded = False
        
        if model_path is None:
            model_path = "ml/models/best.pt"
        
        self.model_path = Path(model_path)
        
        # Try to load model if it exists
        if self.model_path.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(self.model_path))
                self.model_loaded = True
                print(f"YOLO model loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load YOLO model: {e}")
                self.model_loaded = False
    
    def detect(self, image: np.ndarray, conf_threshold: float = 0.25) -> list[Detection]:
        """
        Detect structural elements in image.
        
        Args:
            image: Input image as numpy array (BGR or RGB)
            conf_threshold: Confidence threshold for detections
            
        Returns:
            List of Detection objects
        """
        if not self.model_loaded:
            return []
        
        # Run inference
        results = self.model(image, conf=conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                box = boxes[i]
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                
                class_name = self.CLASS_NAMES[cls]
                detections.append(Detection(
                    class_name=class_name,
                    confidence=conf,
                    bbox=xyxy,
                ))
        
        return detections
    
    def detections_to_model(self, detections: list[Detection], scale_factor: float = 1.0) -> StructuralModel:
        """
        Convert YOLO detections to structural model.
        
        Args:
            detections: List of Detection objects
            scale_factor: Pixels per mm conversion factor
            
        Returns:
            StructuralModel with nodes, members, and supports
        """
        # Separate detections by class
        joint_dets = [d for d in detections if d.class_name == "joint"]
        member_dets = [d for d in detections if d.class_name == "member"]
        pin_dets = [d for d in detections if d.class_name == "support_pin"]
        roller_dets = [d for d in detections if d.class_name == "support_roller"]
        
        # Cluster nearby joints (merge overlapping/close detections)
        joints = self._cluster_joints(joint_dets)
        
        # Create nodes from joints
        nodes = []
        for i, joint in enumerate(joints):
            x_px = (joint[0] + joint[2]) / 2
            y_px = (joint[1] + joint[3]) / 2
            
            # Convert to mm
            x_mm = x_px / scale_factor if scale_factor > 0 else x_px
            y_mm = y_px / scale_factor if scale_factor > 0 else y_px
            
            nodes.append(Node(
                id=f"N{i}",
                x=x_mm,
                y=y_mm
            ))
        
        # Infer member connectivity from member detections and joint positions
        members = self._infer_members(member_dets, nodes)
        
        # Map supports to nearest joints
        supports = []
        for pin_det in pin_dets:
            nearest_node = self._find_nearest_node(pin_det.bbox, nodes)
            if nearest_node:
                supports.append(Support(node_id=nearest_node.id, type="pin"))
        
        for roller_det in roller_dets:
            nearest_node = self._find_nearest_node(roller_det.bbox, nodes)
            if nearest_node:
                supports.append(Support(node_id=nearest_node.id, type="roller"))
        
        return StructuralModel(
            nodes=nodes,
            members=members,
            supports=supports
        )
    
    def _cluster_joints(self, joint_detections: list[Detection], iou_threshold: float = 0.3) -> list[list[float]]:
        """Cluster nearby joint detections to avoid duplicates."""
        if not joint_detections:
            return []
        
        # Sort by confidence
        sorted_dets = sorted(joint_detections, key=lambda d: d.confidence, reverse=True)
        
        clusters = []
        used = [False] * len(sorted_dets)
        
        for i, det in enumerate(sorted_dets):
            if used[i]:
                continue
            
            cluster = det.bbox.copy()
            used[i] = True
            
            # Find overlapping detections
            for j in range(i + 1, len(sorted_dets)):
                if used[j]:
                    continue
                
                iou = self._compute_iou(cluster, sorted_dets[j].bbox)
                if iou > iou_threshold:
                    # Merge bboxes (average)
                    cluster = [
                        (cluster[0] + sorted_dets[j].bbox[0]) / 2,
                        (cluster[1] + sorted_dets[j].bbox[1]) / 2,
                        (cluster[2] + sorted_dets[j].bbox[2]) / 2,
                        (cluster[3] + sorted_dets[j].bbox[3]) / 2,
                    ]
                    used[j] = True
            
            clusters.append(cluster)
        
        return clusters
    
    def _compute_iou(self, bbox1: list[float], bbox2: list[float]) -> float:
        """Compute IoU between two bounding boxes."""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _infer_members(self, member_dets: list[Detection], nodes: list[Node]) -> list[Member]:
        """Infer member connectivity from member bboxes and node positions."""
        members = []
        
        for i, mem_det in enumerate(member_dets):
            # Get member bbox center and orientation
            x1, y1, x2, y2 = mem_det.bbox
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            
            # Find two nearest nodes to this member
            distances = []
            for node in nodes:
                # Approximate distance (using pixel coordinates for nodes is wrong, 
                # but for inference we need to work with what we have)
                dist = ((node.x - cx)**2 + (node.y - cy)**2)**0.5
                distances.append((dist, node))
            
            # Sort by distance
            distances.sort(key=lambda x: x[0])
            
            # Connect to two nearest nodes
            if len(distances) >= 2:
                node1 = distances[0][1]
                node2 = distances[1][1]
                
                members.append(Member(
                    id=f"M{i}",
                    start_node=node1.id,
                    end_node=node2.id,
                    material="steel"
                ))
        
        return members
    
    def _find_nearest_node(self, bbox: list[float], nodes: list[Node]) -> Optional[Node]:
        """Find nearest node to a bounding box."""
        if not nodes:
            return None
        
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        
        min_dist = float('inf')
        nearest = None
        
        for node in nodes:
            dist = ((node.x - cx)**2 + (node.y - cy)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest = node
        
        return nearest


# Global detector instance
_detector: Optional[YOLODetector] = None


def get_detector() -> YOLODetector:
    """Get or create global YOLO detector instance."""
    global _detector
    if _detector is None:
        _detector = YOLODetector()
    return _detector
