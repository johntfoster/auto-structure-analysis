"""ArUco marker detection and generation service."""

import io
import numpy as np
import cv2
from PIL import Image


def detect_aruco(image: np.ndarray) -> dict:
    """
    Detect ArUco markers in an image.
    
    Args:
        image: Input image as numpy array (BGR format)
        
    Returns:
        Dictionary containing:
        - marker_ids: List of detected marker IDs
        - marker_corners: List of marker corner coordinates
        - scale_factor: Computed scale factor (pixels per mm) if markers detected
    """
    # Use DICT_4X4_50 ArUco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    
    # Detect markers
    corners, ids, rejected = detector.detectMarkers(image)
    
    result = {
        "marker_ids": [],
        "marker_corners": [],
        "scale_factor": None
    }
    
    if ids is not None and len(ids) > 0:
        result["marker_ids"] = ids.flatten().tolist()
        result["marker_corners"] = [corner.tolist() for corner in corners]
        
        # Compute scale factor from first detected marker
        # Marker size in pixels = distance between opposite corners
        first_corner = corners[0][0]  # Shape: (4, 2)
        
        # Calculate diagonal distance (pixels)
        p1 = first_corner[0]  # Top-left
        p2 = first_corner[2]  # Bottom-right
        diagonal_px = np.linalg.norm(p2 - p1)
        
        # For a square marker, diagonal = sqrt(2) * side_length
        side_length_px = diagonal_px / np.sqrt(2)
        
        # Assume marker is 100mm (will be parameterized in API)
        # This is a placeholder - actual scale will be computed in analysis endpoint
        result["scale_factor"] = side_length_px / 100.0  # pixels per mm
    
    return result


def generate_marker(marker_id: int, size_px: int = 200) -> bytes:
    """
    Generate a printable ArUco marker as PNG bytes.
    
    Args:
        marker_id: ID of the marker to generate (0-49 for DICT_4X4_50)
        size_px: Size of the marker image in pixels
        
    Returns:
        PNG image as bytes
    """
    # Use DICT_4X4_50 ArUco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Generate marker image
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size_px)
    
    # Add white border (10% of size)
    border = size_px // 10
    marker_with_border = cv2.copyMakeBorder(
        marker_img,
        border, border, border, border,
        cv2.BORDER_CONSTANT,
        value=255
    )
    
    # Convert to PIL Image
    pil_img = Image.fromarray(marker_with_border)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    pil_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()
