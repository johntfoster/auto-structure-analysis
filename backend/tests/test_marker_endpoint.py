"""Tests for ArUco marker generation endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_marker_endpoint_default():
    """Test marker generation with default parameters."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/marker")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_marker_endpoint_custom_id():
    """Test marker generation with custom ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/marker?id=5")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_marker_endpoint_custom_size():
    """Test marker generation with custom size."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/marker?size=300")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_marker_endpoint_invalid_id():
    """Test marker generation with invalid ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # ID too high
        response = await client.get("/api/v1/marker?id=100")
    
    assert response.status_code == 400
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # ID negative
        response = await client.get("/api/v1/marker?id=-1")
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_marker_endpoint_invalid_size():
    """Test marker generation with invalid size."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Size too small
        response = await client.get("/api/v1/marker?size=10")
    
    assert response.status_code == 400
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Size too large
        response = await client.get("/api/v1/marker?size=2000")
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_marker_endpoint_multiple_ids():
    """Test that different marker IDs produce different images."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.get("/api/v1/marker?id=0")
        response2 = await client.get("/api/v1/marker?id=1")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Different IDs should produce different images
    assert response1.content != response2.content


@pytest.mark.asyncio
async def test_marker_endpoint_different_sizes():
    """Test that different sizes produce different images."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.get("/api/v1/marker?size=100")
        response2 = await client.get("/api/v1/marker?size=200")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Different sizes should produce different file sizes
    assert len(response1.content) != len(response2.content)
