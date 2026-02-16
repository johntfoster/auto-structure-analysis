"""Tests for health check endpoint."""

import pytest


def test_health_endpoint(client):
    """Test health check returns 200 and correct status."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint_async(async_client):
    """Test health check with async client."""
    response = await async_client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
