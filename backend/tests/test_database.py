"""Tests for database functionality."""

import pytest
import tempfile
import os
from app.database import Database
from app.models.schemas import (
    AnalysisDetail,
    StructuralModel,
    AnalysisResults,
    Node,
    Member,
    Support,
    Load,
    MemberForce,
    Reaction
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    
    db = Database(db_path)
    yield db
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def sample_analysis():
    """Create a sample analysis for testing."""
    model = StructuralModel(
        nodes=[
            Node(id="A", x=0.0, y=0.0),
            Node(id="B", x=1000.0, y=0.0)
        ],
        members=[
            Member(id="AB", start_node="A", end_node="B")
        ],
        supports=[
            Support(node_id="A", type="pin"),
            Support(node_id="B", type="roller")
        ]
    )
    
    results = AnalysisResults(
        member_forces=[
            MemberForce(
                member_id="AB",
                axial=10000.0,
                shear=0.0,
                moment=0.0,
                stress=50.0,
                stress_ratio=0.2
            )
        ],
        reactions=[
            Reaction(node_id="A", rx=0.0, ry=5000.0),
            Reaction(node_id="B", rx=0.0, ry=5000.0)
        ],
        max_deflection=2.5,
        safety_status="PASS",
        max_stress_ratio=0.2
    )
    
    loads = [Load(node_id="A", fx=0.0, fy=-10000.0)]
    
    return AnalysisDetail(
        analysis_id="test-123",
        status="completed",
        material="steel",
        scale_factor=1.0,
        detection_method="yolo",
        model=model,
        results=results,
        loads=loads,
        error=None
    )


def test_database_initialization(temp_db):
    """Test database initialization creates tables."""
    # Database should be initialized without errors
    assert temp_db is not None


def test_save_and_get_analysis(temp_db, sample_analysis):
    """Test saving and retrieving an analysis."""
    # Save analysis
    temp_db.save_analysis(sample_analysis)
    
    # Retrieve analysis
    retrieved = temp_db.get_analysis("test-123")
    
    assert retrieved is not None
    assert retrieved.analysis_id == "test-123"
    assert retrieved.status == "completed"
    assert retrieved.material == "steel"
    assert retrieved.model is not None
    assert len(retrieved.model.nodes) == 2
    assert len(retrieved.model.members) == 1


def test_get_nonexistent_analysis(temp_db):
    """Test retrieving a non-existent analysis."""
    result = temp_db.get_analysis("nonexistent")
    assert result is None


def test_list_analyses_empty(temp_db):
    """Test listing analyses when database is empty."""
    analyses, total = temp_db.list_analyses()
    
    assert len(analyses) == 0
    assert total == 0


def test_list_analyses_with_data(temp_db, sample_analysis):
    """Test listing analyses with data."""
    # Save multiple analyses
    for i in range(5):
        analysis = sample_analysis.model_copy()
        analysis.analysis_id = f"test-{i}"
        temp_db.save_analysis(analysis)
    
    # List all
    analyses, total = temp_db.list_analyses(skip=0, limit=10)
    assert len(analyses) == 5
    assert total == 5


def test_list_analyses_pagination(temp_db, sample_analysis):
    """Test pagination when listing analyses."""
    # Save 10 analyses
    for i in range(10):
        analysis = sample_analysis.model_copy()
        analysis.analysis_id = f"test-{i}"
        temp_db.save_analysis(analysis)
    
    # Get first page
    analyses, total = temp_db.list_analyses(skip=0, limit=3)
    assert len(analyses) == 3
    assert total == 10
    
    # Get second page
    analyses, total = temp_db.list_analyses(skip=3, limit=3)
    assert len(analyses) == 3
    assert total == 10


def test_update_analysis(temp_db, sample_analysis):
    """Test updating an existing analysis."""
    # Save initial version
    temp_db.save_analysis(sample_analysis)
    
    # Update the analysis
    sample_analysis.material = "aluminum"
    sample_analysis.status = "failed"
    temp_db.save_analysis(sample_analysis)
    
    # Retrieve and verify
    retrieved = temp_db.get_analysis("test-123")
    assert retrieved.material == "aluminum"
    assert retrieved.status == "failed"


def test_save_failed_analysis(temp_db):
    """Test saving a failed analysis without model/results."""
    failed_analysis = AnalysisDetail(
        analysis_id="failed-123",
        status="failed",
        material="steel",
        scale_factor=0.0,
        detection_method="none",
        model=None,
        results=None,
        loads=[],
        error="Detection failed"
    )
    
    temp_db.save_analysis(failed_analysis)
    
    retrieved = temp_db.get_analysis("failed-123")
    assert retrieved is not None
    assert retrieved.status == "failed"
    assert retrieved.error == "Detection failed"
    assert retrieved.model is None
    assert retrieved.results is None


def test_delete_analysis(temp_db, sample_analysis):
    """Test deleting an analysis."""
    # Save analysis
    temp_db.save_analysis(sample_analysis)
    
    # Verify it exists
    assert temp_db.get_analysis("test-123") is not None
    
    # Delete it
    deleted = temp_db.delete_analysis("test-123")
    assert deleted is True
    
    # Verify it's gone
    assert temp_db.get_analysis("test-123") is None


def test_delete_nonexistent_analysis(temp_db):
    """Test deleting a non-existent analysis."""
    deleted = temp_db.delete_analysis("nonexistent")
    assert deleted is False
