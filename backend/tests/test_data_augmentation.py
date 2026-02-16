"""Tests for data augmentation pipeline."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from ml.augment import YOLOAugmenter


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200
    # Add some patterns
    cv2.rectangle(img, (100, 100), (200, 200), (50, 50, 50), -1)
    cv2.circle(img, (400, 300), 50, (100, 100, 100), -1)
    return img


@pytest.fixture
def sample_boxes():
    """Create sample YOLO boxes."""
    return [
        (0, 0.5, 0.5, 0.2, 0.2),  # Center box
        (1, 0.3, 0.3, 0.1, 0.1),  # Upper left
        (2, 0.7, 0.7, 0.15, 0.15),  # Lower right
    ]


@pytest.fixture
def temp_dataset():
    """Create a temporary dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create directories
        images_dir = tmpdir / "images"
        labels_dir = tmpdir / "labels"
        images_dir.mkdir()
        labels_dir.mkdir()
        
        # Create sample images and labels
        for i in range(3):
            # Create image
            img = np.ones((480, 640, 3), dtype=np.uint8) * 200
            cv2.rectangle(img, (100+i*50, 100), (200+i*50, 200), (50, 50, 50), -1)
            img_path = images_dir / f"test_{i:03d}.jpg"
            cv2.imwrite(str(img_path), img)
            
            # Create label
            label_path = labels_dir / f"test_{i:03d}.txt"
            with open(label_path, 'w') as f:
                f.write(f"0 0.5 0.5 0.2 0.2\n")
                f.write(f"1 0.3 0.3 0.1 0.1\n")
        
        # Create train/val splits
        with open(tmpdir / "train.txt", 'w') as f:
            f.write("images/test_000.jpg\n")
            f.write("images/test_001.jpg\n")
        
        with open(tmpdir / "val.txt", 'w') as f:
            f.write("images/test_002.jpg\n")
        
        yield tmpdir


class TestYOLOAugmenter:
    """Test YOLO augmenter."""
    
    def test_initialization(self):
        """Test augmenter initialization."""
        augmenter = YOLOAugmenter()
        assert augmenter is not None
        assert hasattr(augmenter, 'preserve_aspect')
    
    def test_brightness_contrast(self, sample_image):
        """Test brightness/contrast adjustment."""
        augmenter = YOLOAugmenter()
        
        original_mean = np.mean(sample_image)
        augmented = augmenter.adjust_brightness_contrast(sample_image.copy())
        
        # Check that image was modified
        assert not np.array_equal(sample_image, augmented)
        
        # Check that shape is preserved
        assert augmented.shape == sample_image.shape
        
        # Check values are still valid
        assert augmented.min() >= 0
        assert augmented.max() <= 255
    
    def test_blur(self, sample_image):
        """Test blur augmentation."""
        augmenter = YOLOAugmenter()
        
        # Blur might not always apply (random choice includes 'none')
        # Run multiple times to ensure at least one blur happens
        blurred = False
        for _ in range(10):
            augmented = augmenter.add_blur(sample_image.copy())
            if not np.array_equal(sample_image, augmented):
                blurred = True
                break
        
        assert blurred, "Blur should be applied in at least one of multiple attempts"
        assert augmented.shape == sample_image.shape
    
    def test_noise(self, sample_image):
        """Test noise augmentation."""
        augmenter = YOLOAugmenter()
        
        # Run multiple times since noise is random
        noisy = False
        for _ in range(10):
            augmented = augmenter.add_noise(sample_image.copy())
            if not np.array_equal(sample_image, augmented):
                noisy = True
                break
        
        assert noisy, "Noise should be applied in at least one of multiple attempts"
        assert augmented.shape == sample_image.shape
        assert augmented.min() >= 0
        assert augmented.max() <= 255
    
    def test_horizontal_flip_preserves_count(self, sample_image, sample_boxes):
        """Test that horizontal flip preserves annotation count."""
        augmenter = YOLOAugmenter()
        
        flipped_img, flipped_boxes = augmenter.horizontal_flip(sample_image, sample_boxes)
        
        assert len(flipped_boxes) == len(sample_boxes), "Flip should preserve box count"
    
    def test_horizontal_flip_mirrors_boxes(self, sample_image, sample_boxes):
        """Test that horizontal flip correctly mirrors bounding boxes."""
        augmenter = YOLOAugmenter()
        
        flipped_img, flipped_boxes = augmenter.horizontal_flip(sample_image, sample_boxes)
        
        # Check x coordinates are mirrored
        for orig, flipped in zip(sample_boxes, flipped_boxes):
            orig_class, orig_x, orig_y, orig_w, orig_h = orig
            flip_class, flip_x, flip_y, flip_w, flip_h = flipped
            
            # Class should be same
            assert orig_class == flip_class
            
            # X should be mirrored: new_x = 1 - old_x
            assert abs(flip_x - (1.0 - orig_x)) < 1e-6
            
            # Y should be unchanged
            assert abs(flip_y - orig_y) < 1e-6
            
            # Width and height should be unchanged
            assert abs(flip_w - orig_w) < 1e-6
            assert abs(flip_h - orig_h) < 1e-6
    
    def test_horizontal_flip_valid_range(self, sample_image, sample_boxes):
        """Test that flipped boxes remain in valid range."""
        augmenter = YOLOAugmenter()
        
        flipped_img, flipped_boxes = augmenter.horizontal_flip(sample_image, sample_boxes)
        
        for box in flipped_boxes:
            class_id, x, y, w, h = box
            assert 0 <= x <= 1, f"X coordinate {x} out of range"
            assert 0 <= y <= 1, f"Y coordinate {y} out of range"
            assert 0 < w <= 1, f"Width {w} out of range"
            assert 0 < h <= 1, f"Height {h} out of range"
    
    def test_random_crop_preserves_some_boxes(self, sample_image, sample_boxes):
        """Test that random crop preserves at least some boxes."""
        augmenter = YOLOAugmenter()
        
        cropped_img, cropped_boxes = augmenter.random_crop(sample_image, sample_boxes)
        
        # Should keep at least one box (or return original if none kept)
        assert len(cropped_boxes) > 0
    
    def test_random_crop_valid_boxes(self, sample_image, sample_boxes):
        """Test that cropped boxes remain valid."""
        augmenter = YOLOAugmenter()
        
        cropped_img, cropped_boxes = augmenter.random_crop(sample_image, sample_boxes)
        
        for box in cropped_boxes:
            class_id, x, y, w, h = box
            assert 0 <= x <= 1, f"X coordinate {x} out of range"
            assert 0 <= y <= 1, f"Y coordinate {y} out of range"
            assert 0 < w <= 1, f"Width {w} out of range"
            assert 0 < h <= 1, f"Height {h} out of range"
    
    def test_augmentation_produces_different_images(self, sample_image):
        """Test that augmentation produces visually different images."""
        augmenter = YOLOAugmenter()
        
        # Create temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            img_path = tmpdir / "test.jpg"
            label_path = tmpdir / "test.txt"
            
            cv2.imwrite(str(img_path), sample_image)
            
            with open(label_path, 'w') as f:
                f.write("0 0.5 0.5 0.2 0.2\n")
            
            # Apply augmentation
            augmented, boxes = augmenter.augment_image(img_path, label_path, 'full')
            
            # Calculate pixel difference
            diff = np.abs(sample_image.astype(float) - augmented.astype(float))
            mean_diff = np.mean(diff)
            
            # There should be some difference (but augmentation is random, so might be small)
            # Run multiple times to ensure at least one has significant change
            has_significant_change = mean_diff > 5.0
            
            if not has_significant_change:
                # Try again
                for _ in range(5):
                    augmented, boxes = augmenter.augment_image(img_path, label_path, 'full')
                    diff = np.abs(sample_image.astype(float) - augmented.astype(float))
                    mean_diff = np.mean(diff)
                    if mean_diff > 5.0:
                        has_significant_change = True
                        break
            
            assert has_significant_change, "Augmentation should produce visible changes"
    
    def test_augment_dataset(self, temp_dataset):
        """Test full dataset augmentation."""
        augmenter = YOLOAugmenter()
        
        output_dir = temp_dataset / "augmented"
        
        augmenter.augment_dataset(
            dataset_dir=temp_dataset,
            output_dir=output_dir,
            multiplier=2
        )
        
        # Check output structure
        assert (output_dir / "images").exists()
        assert (output_dir / "labels").exists()
        assert (output_dir / "train.txt").exists()
        assert (output_dir / "val.txt").exists()
        
        # Count files
        aug_images = list((output_dir / "images").glob("*.jpg"))
        aug_labels = list((output_dir / "labels").glob("*.txt"))
        
        # Should have original + augmented (3 originals * 2 multiplier = 6 total)
        assert len(aug_images) == 6, f"Expected 6 images, got {len(aug_images)}"
        assert len(aug_labels) == 6, f"Expected 6 labels, got {len(aug_labels)}"
        
        # Check that augmented labels have matching images
        for label_file in aug_labels:
            img_file = output_dir / "images" / f"{label_file.stem}.jpg"
            assert img_file.exists(), f"Missing image for label {label_file.name}"
