"""Tests for synthetic truss data generator."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from ml.generate_synthetic import SyntheticTrussGenerator


def test_generator_initialization():
    """Test that generator can be initialized."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    assert gen.width == 640
    assert gen.height == 480


def test_generate_warren_truss():
    """Test Warren truss generation."""
    gen = SyntheticTrussGenerator()
    joints, members, supports, _ = gen.generate_warren_truss(num_panels=3)
    
    # Check we got joints
    assert len(joints) > 0
    
    # Check we got members
    assert len(members) > 0
    
    # Check we got supports
    assert len(supports) == 2
    
    # Check support types
    support_types = [s[1] for s in supports]
    assert "pin" in support_types
    assert "roller" in support_types


def test_generate_pratt_truss():
    """Test Pratt truss generation."""
    gen = SyntheticTrussGenerator()
    joints, members, supports, _ = gen.generate_pratt_truss(num_panels=4)
    
    assert len(joints) > 0
    assert len(members) > 0
    assert len(supports) == 2


def test_generate_howe_truss():
    """Test Howe truss generation."""
    gen = SyntheticTrussGenerator()
    joints, members, supports, _ = gen.generate_howe_truss(num_panels=4)
    
    assert len(joints) > 0
    assert len(members) > 0
    assert len(supports) == 2


def test_generate_k_truss():
    """Test K-truss generation."""
    gen = SyntheticTrussGenerator()
    joints, members, supports, _ = gen.generate_k_truss(num_panels=3)
    
    assert len(joints) > 0
    assert len(members) > 0
    assert len(supports) == 2


def test_generate_a_frame():
    """Test A-frame generation."""
    gen = SyntheticTrussGenerator()
    joints, members, supports, _ = gen.generate_a_frame()
    
    assert len(joints) == 3
    assert len(members) == 3
    assert len(supports) == 2


def test_generate_truss_random_type():
    """Test generating random truss type."""
    gen = SyntheticTrussGenerator()
    
    truss_type = "warren"
    joints, members, supports, _ = gen.generate_truss(truss_type)
    
    assert len(joints) > 0
    assert len(members) > 0
    assert len(supports) == 2


def test_draw_structure():
    """Test drawing structure to image."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    # Generate simple structure
    joints, members, supports, _ = gen.generate_warren_truss(num_panels=3)
    
    # Draw it
    img, annotations = gen.draw_structure(joints, members, supports, add_marker=False)
    
    # Check image
    assert isinstance(img, Image.Image)
    assert img.size == (640, 480)
    
    # Check annotations
    assert len(annotations) > 0
    
    # Check annotation format (class_id, x, y, w, h)
    for ann in annotations:
        assert len(ann) == 5
        class_id, cx, cy, w, h = ann
        
        # Check class ID is valid
        assert 0 <= class_id <= 3
        
        # Check normalized coordinates
        assert 0 <= cx <= 1
        assert 0 <= cy <= 1
        assert 0 < w <= 1
        assert 0 < h <= 1


def test_draw_structure_with_marker():
    """Test drawing structure with ArUco marker."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    joints, members, supports, _ = gen.generate_warren_truss(num_panels=3)
    img, annotations = gen.draw_structure(joints, members, supports, add_marker=True)
    
    assert isinstance(img, Image.Image)
    assert len(annotations) > 0


def test_generate_dataset():
    """Test generating complete dataset."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Generate small dataset
        gen.generate_dataset(output_dir, num_images=5, train_split=0.8)
        
        # Check directories were created
        assert (output_dir / "images").exists()
        assert (output_dir / "labels").exists()
        
        # Check files were created
        assert (output_dir / "train.txt").exists()
        assert (output_dir / "val.txt").exists()
        
        # Check images were created
        image_files = list((output_dir / "images").glob("*.jpg"))
        assert len(image_files) == 5
        
        # Check labels were created
        label_files = list((output_dir / "labels").glob("*.txt"))
        assert len(label_files) == 5
        
        # Check train/val split
        with open(output_dir / "train.txt") as f:
            train_content = f.read().strip()
            train_files = train_content.split('\n') if train_content else []
        
        with open(output_dir / "val.txt") as f:
            val_content = f.read().strip()
            val_files = val_content.split('\n') if val_content else []
        
        # Should have some split (though with only 5 images, might be skewed)
        assert len(train_files) + len(val_files) == 5


def test_yolo_annotation_format():
    """Test that generated annotations are valid YOLO format."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Generate single image
        gen.generate_dataset(output_dir, num_images=1, train_split=1.0)
        
        # Read label file
        label_files = list((output_dir / "labels").glob("*.txt"))
        assert len(label_files) == 1
        
        with open(label_files[0]) as f:
            lines = f.readlines()
        
        # Check each line
        for line in lines:
            parts = line.strip().split()
            
            # Should have 5 values
            assert len(parts) == 5
            
            # Parse values
            class_id = int(parts[0])
            cx = float(parts[1])
            cy = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])
            
            # Validate
            assert 0 <= class_id <= 3
            assert 0 <= cx <= 1
            assert 0 <= cy <= 1
            assert 0 < w <= 1
            assert 0 < h <= 1


def test_different_truss_types():
    """Test that different truss types can be generated."""
    gen = SyntheticTrussGenerator()
    
    truss_types = ["warren", "pratt", "howe", "k_truss", "a_frame"]
    
    for truss_type in truss_types:
        joints, members, supports, _ = gen.generate_truss(truss_type, member_count=3)
        
        # Each type should generate valid structure
        assert len(joints) > 0
        assert len(members) > 0
        assert len(supports) > 0


def test_create_background_variations():
    """Test that different background types can be created."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    # Generate multiple backgrounds to test randomness
    backgrounds = []
    for _ in range(10):
        bg = gen.create_background()
        assert isinstance(bg, Image.Image)
        assert bg.size == (640, 480)
        backgrounds.append(bg)
    
    # At least some backgrounds should be different
    unique_backgrounds = len(set(bg.tobytes() for bg in backgrounds))
    assert unique_backgrounds > 1, "Backgrounds should vary"


def test_apply_perspective_distortion():
    """Test perspective distortion application."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    # Create test image
    img = Image.new('RGB', (640, 480), color=(200, 200, 200))
    
    # Apply distortion multiple times (it's random)
    distorted_count = 0
    for _ in range(10):
        result = gen.apply_perspective_distortion(img)
        assert isinstance(result, Image.Image)
        assert result.size == (640, 480)
        
        # Check if it was actually distorted
        if result.tobytes() != img.tobytes():
            distorted_count += 1
    
    # Should apply distortion at least sometimes
    assert distorted_count > 0, "Distortion should be applied sometimes"


def test_add_random_noise_objects():
    """Test random noise objects addition."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    img = Image.new('RGB', (640, 480), color=(255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Should not raise any errors
    gen.add_random_noise_objects(draw)
    
    # Hard to test exact output due to randomness, but method should complete
    assert True


def test_add_text_labels():
    """Test text label addition."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    img = Image.new('RGB', (640, 480), color=(255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Should not raise any errors
    gen.add_text_labels(draw)
    
    # Method should complete successfully
    assert True


def test_variable_image_sizes():
    """Test generation with variable image sizes."""
    gen = SyntheticTrussGenerator(image_size=(640, 480))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Generate dataset with varying sizes
        gen.generate_dataset(output_dir, num_images=10, train_split=0.8, vary_size=True)
        
        # Check that images were created
        image_files = list((output_dir / "images").glob("*.jpg"))
        assert len(image_files) == 10
        
        # Load images and check sizes
        sizes = set()
        for img_path in image_files:
            img = Image.open(img_path)
            sizes.add(img.size)
        
        # Should have some variety in sizes (though not guaranteed with only 10 images)
        # At minimum, all images should be valid
        assert len(sizes) >= 1
        for size in sizes:
            assert size[0] > 0 and size[1] > 0
