"""Validation utilities for file uploads and inputs."""

from fastapi import UploadFile, HTTPException, status


async def validate_image_upload(file: UploadFile) -> None:
    """
    Validate image upload for size and file type.
    
    Args:
        file: Uploaded file to validate
        
    Raises:
        HTTPException: If validation fails
    """
    # Import settings inside function to allow test overrides
    from app.config import settings
    
    # Check content type
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.allowed_file_types)}"
        )
    
    # Read file content to check size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
        )
    
    # Reset file pointer for downstream processing
    await file.seek(0)
