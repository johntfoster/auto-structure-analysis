"""Tests for authentication middleware."""

import pytest
from fastapi import HTTPException
from app.middleware.auth import verify_api_key
from app.config import Settings


@pytest.mark.asyncio
async def test_auth_disabled():
    """Test that authentication passes when disabled."""
    # Mock settings with auth disabled
    import app.config as config_module
    original_settings = config_module.settings
    
    try:
        config_module.settings = Settings(api_key_enabled=False)
        
        # Should pass without API key
        await verify_api_key(None)
        
        # Should also pass with any API key
        await verify_api_key("any-key")
        
    finally:
        config_module.settings = original_settings


@pytest.mark.asyncio
async def test_auth_enabled_valid_key():
    """Test authentication with valid API key."""
    import app.config as config_module
    original_settings = config_module.settings
    
    try:
        config_module.settings = Settings(
            api_key_enabled=True,
            api_key="secret-key-123"
        )
        
        # Should pass with correct key
        await verify_api_key("secret-key-123")
        
    finally:
        config_module.settings = original_settings


@pytest.mark.asyncio
async def test_auth_enabled_invalid_key():
    """Test authentication with invalid API key."""
    import app.config as config_module
    original_settings = config_module.settings
    
    try:
        config_module.settings = Settings(
            api_key_enabled=True,
            api_key="secret-key-123"
        )
        
        # Should fail with incorrect key
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("wrong-key")
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)
        
    finally:
        config_module.settings = original_settings


@pytest.mark.asyncio
async def test_auth_enabled_missing_key():
    """Test authentication with missing API key."""
    import app.config as config_module
    original_settings = config_module.settings
    
    try:
        config_module.settings = Settings(
            api_key_enabled=True,
            api_key="secret-key-123"
        )
        
        # Should fail with no key provided
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)
        
        assert exc_info.value.status_code == 401
        
    finally:
        config_module.settings = original_settings


@pytest.mark.asyncio
async def test_auth_enabled_no_configured_key():
    """Test authentication when enabled but no key configured."""
    import app.config as config_module
    original_settings = config_module.settings
    
    try:
        config_module.settings = Settings(
            api_key_enabled=True,
            api_key=None
        )
        
        # Should fail with 500 error
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("any-key")
        
        assert exc_info.value.status_code == 500
        assert "no key is configured" in str(exc_info.value.detail).lower()
        
    finally:
        config_module.settings = original_settings
