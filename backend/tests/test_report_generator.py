"""Tests for PDF report generation."""

import pytest
from app.services.report_generator import generate_report
from app.models.schemas import (
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
def simple_model():
    """Create a simple structural model for testing."""
    return StructuralModel(
        nodes=[
            Node(id="1", x=0.0, y=0.0, displacement_x=0.0, displacement_y=0.0),
            Node(id="2", x=100.0, y=0.0, displacement_x=0.5, displacement_y=-1.2),
            Node(id="3", x=50.0, y=100.0, displacement_x=0.3, displacement_y=-2.5),
        ],
        members=[
            Member(id="M1", start_node="1", end_node="2", material="steel"),
            Member(id="M2", start_node="2", end_node="3", material="steel"),
            Member(id="M3", start_node="3", end_node="1", material="steel"),
        ],
        supports=[
            Support(node_id="1", type="pin"),
            Support(node_id="2", type="roller"),
        ],
    )


@pytest.fixture
def simple_results():
    """Create simple analysis results for testing."""
    return AnalysisResults(
        member_forces=[
            MemberForce(
                member_id="M1",
                axial=5000.0,
                shear=100.0,
                moment=50.0,
                stress=10.0,
                stress_ratio=0.05,
            ),
            MemberForce(
                member_id="M2",
                axial=-3000.0,
                shear=50.0,
                moment=25.0,
                stress=6.0,
                stress_ratio=0.03,
            ),
            MemberForce(
                member_id="M3",
                axial=4000.0,
                shear=75.0,
                moment=40.0,
                stress=8.0,
                stress_ratio=0.04,
            ),
        ],
        reactions=[
            Reaction(node_id="1", rx=2000.0, ry=5000.0),
            Reaction(node_id="2", rx=0.0, ry=3000.0),
        ],
        max_deflection=2.5,
        safety_status="PASS",
        max_stress_ratio=0.05,
        nodes_with_displacements=[
            Node(id="1", x=0.0, y=0.0, displacement_x=0.0, displacement_y=0.0),
            Node(id="2", x=100.0, y=0.0, displacement_x=0.5, displacement_y=-1.2),
            Node(id="3", x=50.0, y=100.0, displacement_x=0.3, displacement_y=-2.5),
        ],
    )


@pytest.fixture
def simple_loads():
    """Create simple loads for testing."""
    return [
        Load(node_id="3", fx=0.0, fy=-10000.0),
    ]


def test_generate_report_returns_pdf_bytes(simple_model, simple_results, simple_loads):
    """Test that generate_report returns PDF bytes."""
    pdf_bytes = generate_report(
        model=simple_model,
        results=simple_results,
        loads=simple_loads,
        material="steel",
        analysis_id="test-123"
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # Check PDF header
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_report_with_warning_status(simple_model, simple_results, simple_loads):
    """Test report generation with WARNING safety status."""
    # Modify results to have warning status
    simple_results.safety_status = "WARNING"
    simple_results.max_stress_ratio = 0.85
    simple_results.member_forces[0].stress_ratio = 0.85
    
    pdf_bytes = generate_report(
        model=simple_model,
        results=simple_results,
        loads=simple_loads,
        material="aluminum",
        analysis_id="test-warning"
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_report_with_fail_status(simple_model, simple_results, simple_loads):
    """Test report generation with FAIL safety status."""
    # Modify results to have fail status
    simple_results.safety_status = "FAIL"
    simple_results.max_stress_ratio = 1.2
    simple_results.member_forces[0].stress_ratio = 1.2
    
    pdf_bytes = generate_report(
        model=simple_model,
        results=simple_results,
        loads=simple_loads,
        material="wood",
        analysis_id="test-fail"
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_report_with_no_loads(simple_model, simple_results):
    """Test report generation with no loads."""
    pdf_bytes = generate_report(
        model=simple_model,
        results=simple_results,
        loads=[],
        material="steel",
        analysis_id="test-no-loads"
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_report_with_complex_model():
    """Test report generation with a more complex model."""
    # Create a larger model
    nodes = [Node(id=str(i), x=float(i*50), y=float(i*30), displacement_x=0.0, displacement_y=0.0) 
             for i in range(1, 11)]
    members = [Member(id=f"M{i}", start_node=str(i), end_node=str(i+1), material="steel") 
               for i in range(1, 10)]
    supports = [
        Support(node_id="1", type="pin"),
        Support(node_id="10", type="roller"),
    ]
    
    model = StructuralModel(nodes=nodes, members=members, supports=supports)
    
    # Create corresponding results
    member_forces = [
        MemberForce(
            member_id=f"M{i}",
            axial=float(1000 * i),
            shear=float(50 * i),
            moment=float(25 * i),
            stress=float(5 * i),
            stress_ratio=0.05 * i,
        )
        for i in range(1, 10)
    ]
    
    reactions = [
        Reaction(node_id="1", rx=5000.0, ry=10000.0),
        Reaction(node_id="10", rx=0.0, ry=8000.0),
    ]
    
    results = AnalysisResults(
        member_forces=member_forces,
        reactions=reactions,
        max_deflection=5.0,
        safety_status="PASS",
        max_stress_ratio=0.45,
        nodes_with_displacements=nodes,
    )
    
    loads = [Load(node_id="5", fx=0.0, fy=-20000.0)]
    
    pdf_bytes = generate_report(
        model=model,
        results=results,
        loads=loads,
        material="steel",
        analysis_id="test-complex"
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_report_structure_image_generation(simple_model, simple_results, simple_loads):
    """Test that structure image is generated successfully."""
    # This test ensures the matplotlib image generation doesn't fail
    pdf_bytes = generate_report(
        model=simple_model,
        results=simple_results,
        loads=simple_loads,
        material="steel",
        analysis_id="test-image"
    )
    
    # The PDF should be larger if image is included
    assert len(pdf_bytes) > 5000  # PDF with image should be at least 5KB
