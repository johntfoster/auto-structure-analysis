"""Integration tests for analysis API endpoints."""

import pytest


def test_analyze_endpoint_success(client, sample_image):
    """Test successful image analysis."""
    files = {"file": ("test.png", sample_image, "image/png")}
    data = {"scale_length_mm": 100.0}
    
    response = client.post("/api/v1/analyze", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    assert "analysis_id" in result
    assert result["status"] in ["completed", "failed"]
    assert "message" in result


def test_analyze_endpoint_no_scale(client, sample_image):
    """Test analysis with default scale parameter."""
    files = {"file": ("test.png", sample_image, "image/png")}
    
    response = client.post("/api/v1/analyze", files=files)
    
    assert response.status_code == 200
    result = response.json()
    assert "analysis_id" in result


@pytest.mark.asyncio
async def test_analyze_endpoint_async(async_client, sample_image):
    """Test analysis endpoint with async client."""
    files = {"file": ("test.png", sample_image, "image/png")}
    data = {"scale_length_mm": 100.0}
    
    response = await async_client.post("/api/v1/analyze", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    assert "analysis_id" in result


def test_get_analysis_success(client, sample_image):
    """Test retrieving analysis results."""
    # First, create an analysis
    files = {"file": ("test.png", sample_image, "image/png")}
    create_response = client.post("/api/v1/analyze", files=files)
    analysis_id = create_response.json()["analysis_id"]
    
    # Then retrieve it
    get_response = client.get(f"/api/v1/analysis/{analysis_id}")
    
    assert get_response.status_code == 200
    result = get_response.json()
    assert result["analysis_id"] == analysis_id
    assert "status" in result
    assert "model" in result or result["status"] == "failed"


def test_get_analysis_not_found(client):
    """Test retrieving non-existent analysis."""
    response = client.get("/api/v1/analysis/nonexistent-id")
    
    assert response.status_code == 404


def test_list_analyses_empty(client):
    """Test listing analyses when none exist (fresh start)."""
    # Note: This test might fail if other tests created analyses
    # In production, would use test database isolation
    response = client.get("/api/v1/analyses")
    
    assert response.status_code == 200
    result = response.json()
    assert "analyses" in result
    assert "total" in result
    assert "page" in result
    assert "page_size" in result
    assert isinstance(result["analyses"], list)


def test_list_analyses_with_data(client, sample_image):
    """Test listing analyses after creating some."""
    # Create a few analyses
    files = {"file": ("test.png", sample_image, "image/png")}
    
    analysis_ids = []
    for i in range(3):
        response = client.post("/api/v1/analyze", files=files)
        analysis_ids.append(response.json()["analysis_id"])
    
    # List all analyses
    response = client.get("/api/v1/analyses")
    
    assert response.status_code == 200
    result = response.json()
    assert result["total"] >= 3
    assert len(result["analyses"]) >= 3
    
    # Verify our analyses are in the list
    returned_ids = [a["analysis_id"] for a in result["analyses"]]
    for aid in analysis_ids:
        assert aid in returned_ids


def test_list_analyses_pagination(client, sample_image):
    """Test pagination of analyses list."""
    # Get first page
    response = client.get("/api/v1/analyses?page=1&page_size=2")
    
    assert response.status_code == 200
    result = response.json()
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert len(result["analyses"]) <= 2


@pytest.mark.asyncio
async def test_full_analysis_workflow(async_client, sample_image):
    """Test complete workflow: create, retrieve, list."""
    # Create analysis
    files = {"file": ("test.png", sample_image, "image/png")}
    data = {"scale_length_mm": 100.0}
    
    create_response = await async_client.post("/api/v1/analyze", files=files, data=data)
    assert create_response.status_code == 200
    analysis_id = create_response.json()["analysis_id"]
    
    # Retrieve specific analysis
    get_response = await async_client.get(f"/api/v1/analysis/{analysis_id}")
    assert get_response.status_code == 200
    analysis_detail = get_response.json()
    assert analysis_detail["analysis_id"] == analysis_id
    
    # List all analyses
    list_response = await async_client.get("/api/v1/analyses")
    assert list_response.status_code == 200
    analyses = list_response.json()["analyses"]
    
    # Our analysis should be in the list
    analysis_ids = [a["analysis_id"] for a in analyses]
    assert analysis_id in analysis_ids


def test_analyze_with_custom_scale(client, sample_image):
    """Test analysis with custom scale length."""
    files = {"file": ("test.png", sample_image, "image/png")}
    data = {"scale_length_mm": 50.0}  # Custom scale
    
    response = client.post("/api/v1/analyze", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    assert "analysis_id" in result


def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
