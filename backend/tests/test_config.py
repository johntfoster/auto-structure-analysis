"""Tests for application configuration."""

import pytest
from app.config import Settings


def test_default_settings():
    """Test default configuration values."""
    settings = Settings()
    
    assert settings.api_title == "Auto Structure Analysis API"
    assert settings.api_version == "0.1.0"
    assert settings.rate_limit_enabled is True
    assert settings.rate_limit_per_minute == 30
    assert settings.max_upload_size_mb == 10
    assert "image/jpeg" in settings.allowed_file_types
    assert "image/png" in settings.allowed_file_types
    assert settings.api_key_enabled is False


def test_cors_origins():
    """Test CORS origins configuration."""
    settings = Settings()
    
    assert "http://localhost:5173" in settings.cors_origins
    assert "https://johntfoster.github.io" in settings.cors_origins


def test_database_url():
    """Test database URL configuration."""
    settings = Settings()
    
    assert settings.database_url == "sqlite:///./analyses.db"


def test_custom_settings():
    """Test custom configuration via environment."""
    settings = Settings(
        api_key_enabled=True,
        api_key="test-key-123",
        rate_limit_per_minute=60,
        max_upload_size_mb=20
    )
    
    assert settings.api_key_enabled is True
    assert settings.api_key == "test-key-123"
    assert settings.rate_limit_per_minute == 60
    assert settings.max_upload_size_mb == 20
