"""Tests for report download endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.analysis import analyses_db
from app.models.schemas import (
    AnalysisDetail,
    StructuralModel,
    Node,
    Member,
    Support,
    AnalysisResults,
    MemberForce,
    Reaction,
    Load
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_analyses_db():
    """Clear analyses database before each test."""
    analyses_db.clear()
    yield
    analyses_db.clear()


def test_download_report_success():
    """Test successful PDF report download."""
    # Create a test analysis in the database
    analysis_id = "test-analysis-123"
    
    model = StructuralModel(
        nodes=[
            Node(id="1", x=0.0, y=0.0, displacement_x=0.0, displacement_y=0.0),
            Node(id="2", x=100.0, y=0.0, displacement_x=0.5, displacement_y=-1.0),
        ],
        members=[
            Member(id="M1", start_node="1", end_node="2", material="steel"),
        ],
        supports=[
            Support(node_id="1", type="pin"),
            Support(node_id="2", type="roller"),
        ],
    )
    
    results = AnalysisResults(
        member_forces=[
            MemberForce(
                member_id="M1",
                axial=5000.0,
                shear=100.0,
                moment=50.0,
                stress=10.0,
                stress_ratio=0.05,
            ),
        ],
        reactions=[
            Reaction(node_id="1", rx=2000.0, ry=3000.0),
            Reaction(node_id="2", rx=0.0, ry=2000.0),
        ],
        max_deflection=1.0,
        safety_status="PASS",
        max_stress_ratio=0.05,
        nodes_with_displacements=[
            Node(id="1", x=0.0, y=0.0, displacement_x=0.0, displacement_y=0.0),
            Node(id="2", x=100.0, y=0.0, displacement_x=0.5, displacement_y=-1.0),
        ],
    )
    
    loads = [Load(node_id="2", fx=0.0, fy=-5000.0)]
    
    analyses_db[analysis_id] = AnalysisDetail(
        analysis_id=analysis_id,
        status="completed",
        model=model,
        results=results,
        material="steel",
        loads=loads,
        scale_factor=1.0,
        detection_method="mock",
        error=None,
    )
    
    # Download report
    response = client.get(f"/api/v1/analysis/{analysis_id}/report")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "Content-Disposition" in response.headers
    assert "attachment" in response.headers["Content-Disposition"]
    assert ".pdf" in response.headers["Content-Disposition"]
    
    # Check PDF content
    pdf_bytes = response.content
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_download_report_not_found():
    """Test report download for non-existent analysis."""
    response = client.get("/api/v1/analysis/non-existent-id/report")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_report_failed_analysis():
    """Test report download for failed analysis."""
    analysis_id = "failed-analysis-123"
    
    analyses_db[analysis_id] = AnalysisDetail(
        analysis_id=analysis_id,
        status="failed",
        model=None,
        results=None,
        material="steel",
        loads=[],
        scale_factor=0.0,
        detection_method="none",
        error="Analysis failed",
    )
    
    response = client.get(f"/api/v1/analysis/{analysis_id}/report")
    
    assert response.status_code == 400
    assert "failed" in response.json()["detail"].lower()


def test_download_report_filename_format():
    """Test that report filename includes analysis ID."""
    analysis_id = "test-filename-analysis"
    
    model = StructuralModel(
        nodes=[
            Node(id="1", x=0.0, y=0.0, displacement_x=0.0, displacement_y=0.0),
        ],
        members=[],
        supports=[],
    )
    
    results = AnalysisResults(
        member_forces=[],
        reactions=[],
        max_deflection=0.0,
        safety_status="PASS",
        max_stress_ratio=0.0,
        nodes_with_displacements=[],
    )
    
    analyses_db[analysis_id] = AnalysisDetail(
        analysis_id=analysis_id,
        status="completed",
        model=model,
        results=results,
        material="steel",
        loads=[],
        scale_factor=1.0,
        detection_method="mock",
        error=None,
    )
    
    response = client.get(f"/api/v1/analysis/{analysis_id}/report")
    
    assert response.status_code == 200
    
    # Check filename includes first 8 chars of analysis ID
    disposition = response.headers["Content-Disposition"]
    assert analysis_id[:8] in disposition
    assert "analysis_report" in disposition
