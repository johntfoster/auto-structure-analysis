"""Tests for frame structure FEA solver."""

import pytest
from app.models.schemas import (
    StructuralModel, Node, Member, Support, Load
)
from app.services.fea_solver import solve


class TestFrameSolver:
    """Test suite for frame structure analysis."""
    
    def test_simple_frame_portal(self):
        """Test a simple portal frame with moment connections."""
        # Create a simple portal frame (rectangular)
        model = StructuralModel(
            structure_type="frame",
            nodes=[
                Node(id="A", x=0.0, y=0.0),      # Bottom left
                Node(id="B", x=1000.0, y=0.0),   # Bottom right
                Node(id="C", x=0.0, y=1000.0),   # Top left
                Node(id="D", x=1000.0, y=1000.0) # Top right
            ],
            members=[
                Member(id="col1", start_node="A", end_node="C"),  # Left column
                Member(id="col2", start_node="B", end_node="D"),  # Right column
                Member(id="beam", start_node="C", end_node="D"),  # Top beam
            ],
            supports=[
                Support(node_id="A", type="fixed"),  # Fixed at base
                Support(node_id="B", type="fixed"),  # Fixed at base
            ]
        )
        
        # Apply horizontal load at top left (wind load)
        loads = [Load(node_id="C", fx=1000.0, fy=0.0)]
        
        # Solve
        results = solve(model, loads, material_name="steel")
        
        # Verify results
        assert results.safety_status in ["PASS", "WARNING", "FAIL"]
        assert len(results.member_forces) == 3
        
        # Frame should have non-zero moments
        has_moment = any(abs(mf.moment) > 1.0 for mf in results.member_forces)
        assert has_moment, "Frame members should have bending moments"
        
        # Check reactions exist
        assert len(results.reactions) == 2
        
    def test_frame_vs_truss_behavior(self):
        """Compare frame and truss behavior for the same geometry."""
        # Create cantilever-style geometry where frame/truss difference is clear
        nodes = [
            Node(id="A", x=0.0, y=0.0),
            Node(id="B", x=1000.0, y=0.0),
        ]
        members = [
            Member(id="m1", start_node="A", end_node="B"),
        ]
        supports = [
            Support(node_id="A", type="fixed"),
        ]
        loads = [Load(node_id="B", fx=0.0, fy=-1000.0)]
        
        # Solve as truss
        truss_model = StructuralModel(
            structure_type="truss",
            nodes=nodes,
            members=members,
            supports=supports
        )
        truss_results = solve(truss_model, loads, material_name="steel")
        
        # Solve as frame
        frame_model = StructuralModel(
            structure_type="frame",
            nodes=nodes,
            members=members,
            supports=supports
        )
        frame_results = solve(frame_model, loads, material_name="steel")
        
        # Truss should have minimal moments (RZ constrained)
        truss_max_moment = max(abs(mf.moment) for mf in truss_results.member_forces)
        
        # Frame should have significant moments (RZ free, rigid connections)
        frame_max_moment = max(abs(mf.moment) for mf in frame_results.member_forces)
        
        # Frame moments should be larger than truss moments
        # For a cantilever, frame can carry moment, truss cannot
        assert frame_max_moment > truss_max_moment
        
    def test_cantilever_beam_frame(self):
        """Test a cantilever beam (classic frame problem)."""
        model = StructuralModel(
            structure_type="frame",
            nodes=[
                Node(id="A", x=0.0, y=0.0),
                Node(id="B", x=1000.0, y=0.0),
            ],
            members=[
                Member(id="m1", start_node="A", end_node="B"),
            ],
            supports=[
                Support(node_id="A", type="fixed"),
            ]
        )
        
        # Apply vertical load at free end
        loads = [Load(node_id="B", fx=0.0, fy=-1000.0)]
        
        # Solve
        results = solve(model, loads, material_name="steel")
        
        # Should have results
        assert len(results.member_forces) == 1
        
        # Should have significant moment
        moment = results.member_forces[0].moment
        assert abs(moment) > 100.0, "Cantilever should have significant bending moment"
        
        # Should have deflection
        assert results.max_deflection > 0.0
        
    def test_frame_default_type(self):
        """Test that structure_type defaults to 'truss' for backward compatibility."""
        model = StructuralModel(
            nodes=[
                Node(id="A", x=0.0, y=0.0),
                Node(id="B", x=1000.0, y=0.0),
            ],
            members=[
                Member(id="m1", start_node="A", end_node="B"),
            ],
            supports=[
                Support(node_id="A", type="pin"),
                Support(node_id="B", type="roller"),
            ]
        )
        
        # Should default to truss
        assert model.structure_type == "truss"
        
        # Solve should work
        loads = [Load(node_id="A", fx=0.0, fy=-1000.0)]
        results = solve(model, loads, material_name="steel")
        
        assert results.safety_status in ["PASS", "WARNING", "FAIL"]
