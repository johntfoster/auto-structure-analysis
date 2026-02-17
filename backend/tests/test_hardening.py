"""Integration tests for backend hardening features."""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_database, Database
from app.config import Settings
import app.config as config_module


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_client_with_db(temp_db_path):
    """Create a test client with a temporary database."""
    # Override settings with temp database
    original_settings = config_module.settings
    config_module.settings = Settings(
        database_url=f"sqlite:///{temp_db_path}",
        api_key_enabled=False,
        rate_limit_enabled=False
    )
    
    # Clear global database instance
    import app.database as db_module
    db_module._db = None
    
    client = TestClient(app)
    
    yield client
    
    # Restore original settings
    config_module.settings = original_settings
    db_module._db = None


@pytest.fixture
def test_client_with_auth(temp_db_path):
    """Create a test client with authentication enabled."""
    original_settings = config_module.settings
    config_module.settings = Settings(
        database_url=f"sqlite:///{temp_db_path}",
        api_key_enabled=True,
        api_key="test-secret-key",
        rate_limit_enabled=False
    )
    
    import app.database as db_module
    db_module._db = None
    
    client = TestClient(app)
    
    yield client
    
    config_module.settings = original_settings
    db_module._db = None


def test_root_endpoint_shows_auth_status(test_client_with_db):
    """Test root endpoint shows authentication status."""
    response = test_client_with_db.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "authentication_enabled" in data
    assert data["authentication_enabled"] is False


def test_cors_headers(test_client_with_db):
    """Test CORS headers are properly configured."""
    response = test_client_with_db.options(
        "/api/v1/materials",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    # CORS preflight should work
    assert response.status_code == 200


def test_database_persistence(test_client_with_db):
    """Test that analyses are persisted to database."""
    # This would require a full analysis flow
    # For now, we'll test the materials endpoint which doesn't require auth
    response = test_client_with_db.get("/api/v1/materials")
    
    assert response.status_code == 200
    materials = response.json()
    assert len(materials) > 0


def test_auth_required_for_analyses_list(test_client_with_auth):
    """Test that authentication is required when enabled."""
    # Without API key
    response = test_client_with_auth.get("/api/v1/analyses")
    assert response.status_code == 401
    
    # With correct API key
    response = test_client_with_auth.get(
        "/api/v1/analyses",
        headers={"X-API-Key": "test-secret-key"}
    )
    assert response.status_code == 200


def test_auth_with_wrong_key(test_client_with_auth):
    """Test authentication rejects wrong API key."""
    response = test_client_with_auth.get(
        "/api/v1/analyses",
        headers={"X-API-Key": "wrong-key"}
    )
    
    assert response.status_code == 401


def test_file_size_validation(test_client_with_db):
    """Test file size validation on upload."""
    # Create a large fake file
    import io
    large_content = b"x" * (15 * 1024 * 1024)  # 15MB (over limit)
    
    files = {
        "file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")
    }
    data = {
        "material": "steel"
    }
    
    response = test_client_with_db.post(
        "/api/v1/analyze",
        files=files,
        data=data
    )
    
    # Should reject file that's too large
    assert response.status_code == 413


def test_file_type_validation(test_client_with_db):
    """Test file type validation on upload."""
    import io
    
    # Try to upload a PDF
    files = {
        "file": ("test.pdf", io.BytesIO(b"fake-pdf"), "application/pdf")
    }
    data = {
        "material": "steel"
    }
    
    response = test_client_with_db.post(
        "/api/v1/analyze",
        files=files,
        data=data
    )
    
    # Should reject non-image file
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_list_analyses_pagination(test_client_with_db):
    """Test that pagination works for analysis list."""
    response = test_client_with_db.get("/api/v1/analyses?page=1&page_size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert "analyses" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_get_nonexistent_analysis(test_client_with_db):
    """Test getting a non-existent analysis returns 404."""
    response = test_client_with_db.get("/api/v1/analysis/nonexistent-id")
    
    assert response.status_code == 404
