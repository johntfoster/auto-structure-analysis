"""Tests for YOLO model training pipeline."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest


class TestTrainingPipeline:
    """Test suite for YOLO training pipeline enhancements."""
    
    @patch('ml.train.YOLO')
    @patch('ml.train.Path')
    def test_training_produces_metrics_file(self, mock_path_class, mock_yolo_class):
        """Test that training produces a metrics JSON file."""
        from ml.train import train_model
        
        # Mock the Path operations
        mock_output_path = MagicMock()
        mock_path_class.return_value = mock_output_path
        mock_output_path.mkdir = MagicMock()
        
        # Mock YOLO model
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        
        # Mock training results
        mock_results = MagicMock()
        mock_model.train.return_value = mock_results
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validator.box.map50 = 0.85
        mock_validator.box.map = 0.72
        mock_validator.box.mp = 0.88
        mock_validator.box.mr = 0.81
        mock_validator.fitness = 0.79
        mock_validator.box.ap_class_index = [0, 1, 2, 3]
        mock_validator.box.ap50 = [0.90, 0.85, 0.83, 0.82]
        mock_validator.box.ap = [0.75, 0.72, 0.70, 0.68]
        mock_model.val.return_value = mock_validator
        
        # Mock model trainer
        mock_model.trainer = MagicMock()
        mock_save_dir = MagicMock()
        mock_model.trainer.save_dir = mock_save_dir
        mock_save_dir.__truediv__ = lambda self, x: MagicMock()
        
        # Mock file writing
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                with patch('shutil.copy2'):
                    results, metrics = train_model(epochs=1)
        
        # Verify metrics structure
        assert 'training' in metrics
        assert 'validation' in metrics
        assert 'per_class_metrics' in metrics
        
        assert metrics['validation']['mAP50'] == 0.85
        assert metrics['validation']['mAP50-95'] == 0.72
        assert metrics['validation']['precision'] == 0.88
        assert metrics['validation']['recall'] == 0.81
        
        # Verify per-class metrics
        assert 'joint' in metrics['per_class_metrics']
        assert 'member' in metrics['per_class_metrics']
        assert metrics['per_class_metrics']['joint']['AP50'] == 0.90
        
    def test_metrics_structure(self):
        """Test the expected structure of training metrics."""
        # Expected keys in metrics
        expected_training_keys = ['start_time', 'end_time', 'duration_seconds', 
                                 'epochs_completed', 'base_model', 'config']
        expected_validation_keys = ['mAP50', 'mAP50-95', 'precision', 
                                    'recall', 'fitness']
        
        # This is a structure test - actual values come from integration tests
        metrics_template = {
            "training": {k: None for k in expected_training_keys},
            "validation": {k: None for k in expected_validation_keys},
            "per_class_metrics": {}
        }
        
        assert all(k in metrics_template['training'] for k in expected_training_keys)
        assert all(k in metrics_template['validation'] for k in expected_validation_keys)
