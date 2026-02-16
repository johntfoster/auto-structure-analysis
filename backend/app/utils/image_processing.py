"""Image processing utilities."""

import io
import numpy as np
from PIL import Image
from fastapi import UploadFile


async def load_image(file: UploadFile) -> np.ndarray:
    """
    Load uploaded image file into numpy array.
    
    Args:
        file: Uploaded image file
        
    Returns:
        Image as numpy array (BGR format for OpenCV compatibility)
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert to numpy array
    img_array = np.array(image)
    
    # Convert RGB to BGR for OpenCV
    img_bgr = img_array[:, :, ::-1].copy()
    
    return img_bgr


def resize_for_detection(image: np.ndarray, max_dim: int = 1024) -> np.ndarray:
    """
    Resize image if it exceeds max dimension while maintaining aspect ratio.
    
    Args:
        image: Input image as numpy array
        max_dim: Maximum dimension (width or height) in pixels
        
    Returns:
        Resized image
    """
    h, w = image.shape[:2]
    
    if max(h, w) <= max_dim:
        return image
    
    if h > w:
        new_h = max_dim
        new_w = int(w * (max_dim / h))
    else:
        new_w = max_dim
        new_h = int(h * (max_dim / w))
    
    import cv2
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return resized
