"""Tests for file upload validation."""

import pytest
import io
from fastapi import HTTPException, UploadFile
from app.utils.validation import validate_image_upload
from app.config import Settings


async def create_upload_file(content: bytes, content_type: str, filename: str = "test.jpg") -> UploadFile:
    """Helper to create an UploadFile for testing."""
    file_obj = io.BytesIO(content)
    return UploadFile(
        filename=filename,
        file=file_obj,
        headers={"content-type": content_type}
    )


@pytest.mark.asyncio
async def test_valid_jpeg_upload():
    """Test validation of a valid JPEG file."""
    # Create a small test file (< 10MB)
    content = b"fake-jpeg-content" * 100
    file = await create_upload_file(content, "image/jpeg", "test.jpg")
    
    # Should pass without raising exception
    await validate_image_upload(file)


@pytest.mark.asyncio
async def test_valid_png_upload():
    """Test validation of a valid PNG file."""
    content = b"fake-png-content" * 100
    file = await create_upload_file(content, "image/png", "test.png")
    
    # Should pass without raising exception
    await validate_image_upload(file)


@pytest.mark.asyncio
async def test_invalid_file_type():
    """Test validation rejects invalid file types."""
    content = b"fake-pdf-content" * 100
    file = await create_upload_file(content, "application/pdf", "test.pdf")
    
    with pytest.raises(HTTPException) as exc_info:
        await validate_image_upload(file)
    
    assert exc_info.value.status_code == 400
    assert "Invalid file type" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_file_too_large():
    """Test validation rejects files over size limit."""
    import app.config as config_module
    original_settings = config_module.settings
    
    try:
        # Set a small limit for testing
        config_module.settings = Settings(max_upload_size_mb=1)
        
        # Create a file larger than 1MB
        content = b"x" * (2 * 1024 * 1024)  # 2MB
        file = await create_upload_file(content, "image/jpeg", "large.jpg")
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_image_upload(file)
        
        assert exc_info.value.status_code == 413
        assert "too large" in str(exc_info.value.detail).lower()
        
    finally:
        config_module.settings = original_settings


@pytest.mark.asyncio
async def test_file_at_size_limit():
    """Test validation accepts files at the size limit."""
    import app.config as config_module
    original_settings = config_module.settings
    
    try:
        # Set limit to 1MB
        config_module.settings = Settings(max_upload_size_mb=1)
        
        # Create a file exactly at 1MB
        content = b"x" * (1024 * 1024)  # 1MB
        file = await create_upload_file(content, "image/jpeg", "limit.jpg")
        
        # Should pass
        await validate_image_upload(file)
        
    finally:
        config_module.settings = original_settings


@pytest.mark.asyncio
async def test_file_pointer_reset():
    """Test that file pointer is reset after validation."""
    content = b"test-content" * 100
    file = await create_upload_file(content, "image/jpeg", "test.jpg")
    
    # Validate the file
    await validate_image_upload(file)
    
    # File pointer should be reset to beginning
    read_content = await file.read()
    assert read_content == content


@pytest.mark.asyncio
async def test_unsupported_image_type():
    """Test validation rejects unsupported image formats."""
    content = b"fake-gif-content" * 100
    file = await create_upload_file(content, "image/gif", "test.gif")
    
    with pytest.raises(HTTPException) as exc_info:
        await validate_image_upload(file)
    
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_empty_file():
    """Test validation of an empty file."""
    content = b""
    file = await create_upload_file(content, "image/jpeg", "empty.jpg")
    
    # Should pass validation (size is 0 < limit)
    await validate_image_upload(file)
