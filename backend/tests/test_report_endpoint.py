"""Tests for report download endpoint."""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_database
from app.config import Settings
import app.config as config_module
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
def client(temp_db_path):
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
    
    test_client = TestClient(app)
    
    yield test_client
    
    # Restore original settings
    config_module.settings = original_settings
    db_module._db = None


def test_download_report_success(client):
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
    
    analysis = AnalysisDetail(
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
    
    # Save to database
    db = get_database()
    db.save_analysis(analysis)
    
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


def test_download_report_not_found(client):
    """Test report download for non-existent analysis."""
    response = client.get("/api/v1/analysis/non-existent-id/report")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_report_failed_analysis(client):
    """Test report download for failed analysis."""
    analysis_id = "failed-analysis-123"
    
    analysis = AnalysisDetail(
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
    
    # Save to database
    db = get_database()
    db.save_analysis(analysis)
    
    response = client.get(f"/api/v1/analysis/{analysis_id}/report")
    
    assert response.status_code == 400
    assert "failed" in response.json()["detail"].lower()


def test_download_report_filename_format(client):
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
    
    analysis = AnalysisDetail(
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
    
    # Save to database
    db = get_database()
    db.save_analysis(analysis)
    
    response = client.get(f"/api/v1/analysis/{analysis_id}/report")
    
    assert response.status_code == 200
    
    # Check filename includes first 8 chars of analysis ID
    disposition = response.headers["Content-Disposition"]
    assert analysis_id[:8] in disposition
    assert "analysis_report" in disposition
