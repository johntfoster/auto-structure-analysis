"""Tests for model server."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np
import pytest

from app.services.model_server import ModelServer, get_model_server


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200
    cv2.rectangle(img, (100, 100), (200, 200), (50, 50, 50), -1)
    cv2.circle(img, (400, 300), 50, (100, 100, 100), -1)
    return img


@pytest.fixture
def reset_singleton():
    """Reset ModelServer singleton between tests."""
    ModelServer._instance = None
    ModelServer._model = None
    ModelServer._model_path = None
    ModelServer._loaded = False
    yield
    ModelServer._instance = None
    ModelServer._model = None
    ModelServer._model_path = None
    ModelServer._loaded = False


class TestModelServer:
    """Test model server."""
    
    def test_singleton_pattern(self, reset_singleton):
        """Test that ModelServer follows singleton pattern."""
        server1 = ModelServer()
        server2 = ModelServer()
        
        assert server1 is server2, "ModelServer should be a singleton"
    
    def test_get_model_server(self, reset_singleton):
        """Test get_model_server function."""
        server1 = get_model_server()
        server2 = get_model_server()
        
        assert server1 is server2, "get_model_server should return same instance"
    
    def test_initialization_without_model(self, reset_singleton):
        """Test server initializes gracefully without model file."""
        # Set non-existent model path
        os.environ['MODEL_PATH'] = '/nonexistent/model.pt'
        
        server = ModelServer()
        
        assert not server.is_loaded(), "Should not be loaded with missing model"
        
        # Clean up
        if 'MODEL_PATH' in os.environ:
            del os.environ['MODEL_PATH']
    
    def test_is_loaded_without_model(self, reset_singleton):
        """Test is_loaded returns False when no model."""
        os.environ['MODEL_PATH'] = '/nonexistent/model.pt'
        
        server = ModelServer()
        
        assert not server.is_loaded()
        
        # Clean up
        if 'MODEL_PATH' in os.environ:
            del os.environ['MODEL_PATH']
    
    def test_get_model_info_without_model(self, reset_singleton):
        """Test get_model_info when model not loaded."""
        os.environ['MODEL_PATH'] = '/nonexistent/model.pt'
        
        server = ModelServer()
        info = server.get_model_info()
        
        assert info['loaded'] is False
        assert 'error' in info
        
        # Clean up
        if 'MODEL_PATH' in os.environ:
            del os.environ['MODEL_PATH']
    
    def test_preprocess_maintains_aspect_ratio(self, reset_singleton, sample_image):
        """Test preprocessing maintains aspect ratio."""
        server = ModelServer()
        
        processed = server.preprocess(sample_image, target_size=640)
        
        # Check that image was processed
        assert processed is not None
        assert processed.shape[2] == 3  # RGB channels preserved
        
        # Check aspect ratio maintained (within rounding)
        orig_aspect = sample_image.shape[1] / sample_image.shape[0]
        proc_aspect = processed.shape[1] / processed.shape[0]
        
        assert abs(orig_aspect - proc_aspect) < 0.01
    
    def test_preprocess_resizes_large_image(self, reset_singleton):
        """Test preprocessing resizes large images."""
        server = ModelServer()
        
        # Create large image
        large_img = np.ones((2000, 3000, 3), dtype=np.uint8) * 200
        
        processed = server.preprocess(large_img, target_size=640)
        
        # Check that image was resized
        assert max(processed.shape[:2]) <= 640
    
    def test_predict_without_model(self, reset_singleton, sample_image):
        """Test predict fails gracefully without model."""
        os.environ['MODEL_PATH'] = '/nonexistent/model.pt'
        
        server = ModelServer()
        result = server.predict(sample_image)
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error'] == "Model not loaded"
        assert result['detections'] == []
        
        # Clean up
        if 'MODEL_PATH' in os.environ:
            del os.environ['MODEL_PATH']
    
    @patch('app.services.model_server.YOLO')
    def test_predict_with_mock_model(self, mock_yolo_class, reset_singleton, sample_image):
        """Test predict with mocked YOLO model."""
        # Create mock model
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model
        
        # Create mock results
        mock_boxes = Mock()
        mock_boxes.conf = [np.array([0.9]), np.array([0.8])]
        mock_boxes.xyxy = [
            np.array([[100, 100, 200, 200]]),
            np.array([[300, 300, 400, 400]])
        ]
        mock_boxes.cls = [np.array([0]), np.array([1])]
        mock_boxes.__len__ = lambda self: 2
        
        mock_result = Mock()
        mock_result.boxes = mock_boxes
        mock_result.names = {0: "joint", 1: "member"}
        
        mock_model.predict.return_value = [mock_result]
        mock_model.names = {0: "joint", 1: "member"}
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            model_path = f.name
        
        try:
            os.environ['MODEL_PATH'] = model_path
            
            server = ModelServer()
            result = server.predict(sample_image, conf_threshold=0.5)
            
            assert result['success'] is True
            assert 'detections' in result
            assert len(result['detections']) == 2
            
            # Check detection format
            det = result['detections'][0]
            assert 'class_id' in det
            assert 'class_name' in det
            assert 'confidence' in det
            assert 'bbox' in det
            
        finally:
            # Clean up
            if os.path.exists(model_path):
                os.unlink(model_path)
            if 'MODEL_PATH' in os.environ:
                del os.environ['MODEL_PATH']
    
    @patch('app.services.model_server.YOLO')
    def test_postprocess_filters_confidence(self, mock_yolo_class, reset_singleton):
        """Test postprocessing filters by confidence threshold."""
        # Create mock model
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model
        
        # Create mock results with varying confidence
        mock_boxes = Mock()
        mock_boxes.conf = [np.array([0.9]), np.array([0.2]), np.array([0.8])]
        mock_boxes.xyxy = [
            np.array([[100, 100, 200, 200]]),
            np.array([[200, 200, 300, 300]]),
            np.array([[300, 300, 400, 400]])
        ]
        mock_boxes.cls = [np.array([0]), np.array([1]), np.array([0])]
        mock_boxes.__len__ = lambda self: 3
        
        mock_result = Mock()
        mock_result.boxes = mock_boxes
        mock_result.names = {0: "joint", 1: "member"}
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            model_path = f.name
        
        try:
            os.environ['MODEL_PATH'] = model_path
            
            server = ModelServer()
            detections = server.postprocess([mock_result], conf_threshold=0.5)
            
            # Should filter out the 0.2 confidence detection
            assert len(detections) == 2
            
            # Check that all returned detections have conf >= 0.5
            for det in detections:
                assert det['confidence'] >= 0.5
            
        finally:
            # Clean up
            if os.path.exists(model_path):
                os.unlink(model_path)
            if 'MODEL_PATH' in os.environ:
                del os.environ['MODEL_PATH']
    
    def test_default_model_path(self, reset_singleton):
        """Test that default model path is used when env var not set."""
        # Ensure MODEL_PATH is not set
        if 'MODEL_PATH' in os.environ:
            del os.environ['MODEL_PATH']
        
        server = ModelServer()
        
        # Should use default path
        assert server._model_path == Path('ml/models/best.pt')
    
    @patch('app.services.model_server.YOLO')
    def test_health_check_returns_correct_status(self, mock_yolo_class, reset_singleton):
        """Test health check returns correct status."""
        # Create mock model
        mock_model = Mock()
        mock_model.names = {0: "joint", 1: "member", 2: "support_pin", 3: "support_roller"}
        mock_model.imgsz = 640
        mock_yolo_class.return_value = mock_model
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
            model_path = f.name
        
        try:
            os.environ['MODEL_PATH'] = model_path
            
            server = ModelServer()
            info = server.get_model_info()
            
            assert info['loaded'] is True
            assert 'class_names' in info
            assert 'num_classes' in info
            assert info['num_classes'] == 4
            assert 'input_size' in info
            assert info['input_size'] == 640
            
        finally:
            # Clean up
            if os.path.exists(model_path):
                os.unlink(model_path)
            if 'MODEL_PATH' in os.environ:
                del os.environ['MODEL_PATH']
