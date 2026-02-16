"""Tests for dataset validation."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from ml.validate_dataset import YOLODatasetValidator


@pytest.fixture
def temp_dataset():
    """Create a temporary test dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create directories
        images_dir = tmpdir / "images"
        labels_dir = tmpdir / "labels"
        images_dir.mkdir()
        labels_dir.mkdir()
        
        yield tmpdir, images_dir, labels_dir


def create_test_image(path: Path, width: int = 640, height: int = 480):
    """Create a test image."""
    img = np.ones((height, width, 3), dtype=np.uint8) * 200
    cv2.imwrite(str(path), img)


def create_test_label(path: Path, content: str):
    """Create a test label file."""
    with open(path, 'w') as f:
        f.write(content)


class TestYOLODatasetValidator:
    """Test dataset validator."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = YOLODatasetValidator(num_classes=4)
        assert validator.num_classes == 4
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0
    
    def test_valid_annotation_format(self, temp_dataset):
        """Test validation of correct annotation format."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Create valid label
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 0.5 0.5 0.2 0.2\n1 0.3 0.7 0.1 0.15\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert is_valid, f"Valid annotation failed: {issues}"
        assert len(issues) == 0
    
    def test_invalid_class_id(self, temp_dataset):
        """Test validator catches invalid class IDs."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Class ID 5 is invalid (valid: 0-3)
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "5 0.5 0.5 0.2 0.2\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with invalid class ID"
        assert len(issues) > 0
        assert any("Invalid class ID" in issue for issue in issues)
    
    def test_out_of_range_x_coordinate(self, temp_dataset):
        """Test validator catches x_center > 1."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # x_center = 1.5 is invalid
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 1.5 0.5 0.2 0.2\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with out-of-range x"
        assert len(issues) > 0
        assert any("x_center out of range" in issue for issue in issues)
    
    def test_out_of_range_y_coordinate(self, temp_dataset):
        """Test validator catches y_center < 0."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # y_center = -0.1 is invalid
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 0.5 -0.1 0.2 0.2\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with out-of-range y"
        assert len(issues) > 0
        assert any("y_center out of range" in issue for issue in issues)
    
    def test_out_of_range_width(self, temp_dataset):
        """Test validator catches width > 1."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # width = 1.2 is invalid
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 0.5 0.5 1.2 0.2\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with out-of-range width"
        assert len(issues) > 0
        assert any("width out of range" in issue for issue in issues)
    
    def test_out_of_range_height(self, temp_dataset):
        """Test validator catches height > 1."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # height = 1.5 is invalid
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 0.5 0.5 0.2 1.5\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with out-of-range height"
        assert len(issues) > 0
        assert any("height out of range" in issue for issue in issues)
    
    def test_empty_label_file(self, temp_dataset):
        """Test validator catches empty label files."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Create empty label
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with empty label file"
        assert len(issues) > 0
        assert any("Empty label file" in issue for issue in issues)
    
    def test_invalid_format_too_few_values(self, temp_dataset):
        """Test validator catches lines with too few values."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Only 4 values instead of 5
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 0.5 0.5 0.2\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with wrong number of values"
        assert len(issues) > 0
        assert any("Invalid format" in issue for issue in issues)
    
    def test_invalid_format_non_numeric(self, temp_dataset):
        """Test validator catches non-numeric values."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Non-numeric value
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 abc 0.5 0.2 0.2\n")
        
        is_valid, issues = validator.validate_annotation_format(label_path)
        
        assert not is_valid, "Should fail with non-numeric values"
        assert len(issues) > 0
        assert any("Invalid number format" in issue for issue in issues)
    
    def test_missing_label_file(self, temp_dataset):
        """Test validator catches missing label files."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Create image without corresponding label
        img_path = images_dir / "test.jpg"
        create_test_image(img_path)
        
        is_valid = validator.validate_dataset(tmpdir)
        
        assert not is_valid, "Should fail with missing label file"
        assert len(validator.errors) > 0
        assert any("Missing label file" in error for error in validator.errors)
    
    def test_valid_dataset(self, temp_dataset):
        """Test validator passes on valid dataset."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Create matching image and label
        img_path = images_dir / "test_000.jpg"
        label_path = labels_dir / "test_000.txt"
        
        create_test_image(img_path)
        create_test_label(label_path, "0 0.5 0.5 0.2 0.2\n1 0.3 0.7 0.1 0.15\n")
        
        # Create train.txt
        with open(tmpdir / "train.txt", 'w') as f:
            f.write("images/test_000.jpg\n")
        
        is_valid = validator.validate_dataset(tmpdir)
        
        assert is_valid, f"Valid dataset failed: {validator.errors}"
        assert len(validator.errors) == 0
    
    def test_class_distribution_tracking(self, temp_dataset):
        """Test that validator tracks class distribution."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Create label with multiple classes
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, 
                         "0 0.5 0.5 0.2 0.2\n"
                         "0 0.3 0.3 0.1 0.1\n"
                         "1 0.7 0.7 0.15 0.15\n"
                         "2 0.2 0.8 0.1 0.1\n")
        
        validator.validate_annotation_format(label_path)
        
        # Check distribution
        assert validator.class_distribution[0] == 2
        assert validator.class_distribution[1] == 1
        assert validator.class_distribution[2] == 1
        assert validator.class_distribution[3] == 0
    
    def test_corrupted_image(self, temp_dataset):
        """Test validator catches corrupted images."""
        tmpdir, images_dir, labels_dir = temp_dataset
        
        validator = YOLODatasetValidator(num_classes=4)
        
        # Create corrupted image (invalid data)
        img_path = images_dir / "test.jpg"
        with open(img_path, 'wb') as f:
            f.write(b"not a valid image")
        
        # Create matching label
        label_path = labels_dir / "test.txt"
        create_test_label(label_path, "0 0.5 0.5 0.2 0.2\n")
        
        is_valid = validator.validate_dataset(tmpdir)
        
        assert not is_valid, "Should fail with corrupted image"
        assert len(validator.errors) > 0
