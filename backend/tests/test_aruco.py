"""Tests for ArUco marker detection and generation."""

import io
import numpy as np
import cv2
from PIL import Image

from app.services.aruco_detector import generate_marker, detect_aruco


def test_generate_marker():
    """Test ArUco marker generation."""
    marker_bytes = generate_marker(marker_id=0, size_px=200)
    
    assert isinstance(marker_bytes, bytes)
    assert len(marker_bytes) > 0
    
    # Verify it's a valid PNG
    img = Image.open(io.BytesIO(marker_bytes))
    assert img.format == "PNG"
    assert img.size[0] > 200  # Should have border
    assert img.size[1] > 200


def test_detect_generated_marker():
    """Test detecting a generated ArUco marker."""
    # Generate a marker
    marker_bytes = generate_marker(marker_id=5, size_px=200)
    
    # Load as image
    img_pil = Image.open(io.BytesIO(marker_bytes))
    img_array = np.array(img_pil)
    
    # Convert to BGR (OpenCV format)
    if len(img_array.shape) == 2:
        # Grayscale
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
    else:
        # RGB to BGR
        img_bgr = img_array[:, :, ::-1].copy()
    
    # Detect marker
    result = detect_aruco(img_bgr)
    
    assert result["marker_ids"] == [5]
    assert len(result["marker_corners"]) == 1
    assert result["scale_factor"] is not None
    assert result["scale_factor"] > 0


def test_detect_no_marker(sample_image_array):
    """Test detection on image without markers."""
    result = detect_aruco(sample_image_array)
    
    assert result["marker_ids"] == []
    assert result["marker_corners"] == []
    assert result["scale_factor"] is None


def test_multiple_markers():
    """Test detecting multiple ArUco markers."""
    # Create a larger canvas
    canvas = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Generate and place two markers
    marker1_bytes = generate_marker(marker_id=1, size_px=150)
    marker2_bytes = generate_marker(marker_id=2, size_px=150)
    
    img1 = np.array(Image.open(io.BytesIO(marker1_bytes)))
    img2 = np.array(Image.open(io.BytesIO(marker2_bytes)))
    
    # Place markers on canvas
    canvas[50:50+img1.shape[0], 50:50+img1.shape[1]] = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR) if len(img1.shape) == 2 else img1[:, :, ::-1]
    canvas[50:50+img2.shape[0], 500:500+img2.shape[1]] = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR) if len(img2.shape) == 2 else img2[:, :, ::-1]
    
    # Detect markers
    result = detect_aruco(canvas)
    
    # Should detect both markers
    assert len(result["marker_ids"]) == 2
    assert 1 in result["marker_ids"]
    assert 2 in result["marker_ids"]
