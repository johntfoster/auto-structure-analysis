"""YOLO model serving with singleton pattern."""

import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO


class ModelServer:
    """Singleton YOLO model server."""
    
    _instance: Optional['ModelServer'] = None
    _model: Optional[YOLO] = None
    _model_path: Optional[Path] = None
    _loaded: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model server (singleton pattern ensures this runs once)."""
        if not self._loaded:
            self._load_model()
    
    def _load_model(self):
        """Load YOLO model from configured path."""
        # Get model path from env or default
        model_path_str = os.getenv('MODEL_PATH', 'ml/models/best.pt')
        self._model_path = Path(model_path_str)
        
        if self._model_path.exists():
            try:
                self._model = YOLO(str(self._model_path))
                self._loaded = True
                print(f"Model loaded successfully from {self._model_path}")
            except Exception as e:
                print(f"Failed to load model from {self._model_path}: {e}")
                self._model = None
                self._loaded = False
        else:
            print(f"Model file not found: {self._model_path}")
            self._model = None
            self._loaded = False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded and self._model is not None
    
    def get_model_info(self) -> dict:
        """Get model information."""
        if not self.is_loaded():
            return {
                "loaded": False,
                "model_path": str(self._model_path) if self._model_path else None,
                "error": "Model not loaded"
            }
        
        try:
            return {
                "loaded": True,
                "model_path": str(self._model_path),
                "class_names": self._model.names,
                "num_classes": len(self._model.names),
                "input_size": getattr(self._model, 'imgsz', 640),
            }
        except Exception as e:
            return {
                "loaded": True,
                "model_path": str(self._model_path),
                "error": f"Failed to get model info: {e}"
            }
    
    def preprocess(self, image: np.ndarray, target_size: int = 640) -> np.ndarray:
        """
        Preprocess image for YOLO inference.
        
        Args:
            image: Input image (BGR format from OpenCV)
            target_size: Target size for model input
            
        Returns:
            Preprocessed image
        """
        # YOLO models handle preprocessing internally, but we can resize here
        h, w = image.shape[:2]
        
        # Calculate scaling to maintain aspect ratio
        scale = target_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize image
        if scale != 1.0:
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        return image
    
    def postprocess(self, results, conf_threshold: float = 0.25, 
                   iou_threshold: float = 0.45):
        """
        Postprocess YOLO results.
        
        Args:
            results: YOLO model results
            conf_threshold: Confidence threshold for filtering
            iou_threshold: IoU threshold for NMS
            
        Returns:
            Filtered and processed detections
        """
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            for i in range(len(boxes)):
                conf = float(boxes.conf[i])
                
                # Filter by confidence
                if conf < conf_threshold:
                    continue
                
                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                
                # Get class
                cls = int(boxes.cls[i])
                
                detections.append({
                    'class_id': cls,
                    'class_name': result.names[cls],
                    'confidence': conf,
                    'bbox': {
                        'x1': x1,
                        'y1': y1,
                        'x2': x2,
                        'y2': y2
                    }
                })
        
        return detections
    
    def predict(self, image: np.ndarray, conf_threshold: float = 0.25,
               iou_threshold: float = 0.45) -> dict:
        """
        Run inference on image.
        
        Args:
            image: Input image (BGR format)
            conf_threshold: Confidence threshold
            iou_threshold: IoU threshold for NMS
            
        Returns:
            Detection results
        """
        if not self.is_loaded():
            return {
                "success": False,
                "error": "Model not loaded",
                "detections": []
            }
        
        try:
            # Preprocess (optional, YOLO handles it internally)
            # image = self.preprocess(image)
            
            # Run inference
            results = self._model.predict(
                image,
                conf=conf_threshold,
                iou=iou_threshold,
                verbose=False
            )
            
            # Postprocess
            detections = self.postprocess(results, conf_threshold, iou_threshold)
            
            return {
                "success": True,
                "detections": detections,
                "num_detections": len(detections)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "detections": []
            }
    
    def reload_model(self, model_path: Optional[str] = None):
        """Reload model from path."""
        if model_path:
            os.environ['MODEL_PATH'] = model_path
        
        self._loaded = False
        self._model = None
        self._load_model()


# Global instance
model_server = ModelServer()


def get_model_server() -> ModelServer:
    """Get model server instance."""
    return model_server
