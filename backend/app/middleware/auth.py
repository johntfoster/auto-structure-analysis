"""Authentication middleware for API key validation."""

from typing import Optional
from fastapi import Header, HTTPException, status


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """
    Verify API key if authentication is enabled.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Raises:
        HTTPException: If authentication is enabled and key is invalid
    """
    # Import settings inside function to allow test overrides
    from app.config import settings
    
    # Skip authentication if disabled
    if not settings.api_key_enabled:
        return
    
    # Check if API key is configured
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key authentication is enabled but no key is configured"
        )
    
    # Validate API key
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
