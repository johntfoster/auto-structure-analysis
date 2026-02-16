"""Tests for FEA solver with known analytical solutions."""

import math
import pytest
from app.services.fea_solver import solve
from app.models.schemas import StructuralModel, Node, Member, Support, Load


def test_simple_truss_solver(simple_truss_model, simple_loads):
    """Test FEA solver with simple 3-member triangle truss."""
    results = solve(simple_truss_model, simple_loads)
    
    # Verify results structure
    assert len(results.member_forces) == 3
    assert len(results.reactions) == 2
    assert results.max_deflection >= 0
    
    # Member forces should not be zero
    for mf in results.member_forces:
        assert mf.member_id in ["M1", "M2", "M3"]
        assert mf.axial != 0  # All members should have some force


def test_simple_beam_reactions():
    """Test simply supported beam with center load - known analytical solution."""
    # Simply supported beam with a vertical member creating a T-shape
    # This avoids collinear nodes which can cause singularity
    # Beam length = 2000 mm, load = 1000 N at top
    # Expected reactions: 500 N each
    
    nodes = [
        Node(id="N1", x=0.0, y=0.0),
        Node(id="N2", x=2000.0, y=0.0),
        Node(id="N3", x=1000.0, y=500.0),  # Top node (offset from beam)
    ]
    
    members = [
        Member(id="M1", start_node="N1", end_node="N2", material="steel"),  # Horizontal beam
        Member(id="M2", start_node="N1", end_node="N3", material="steel"),  # Diagonal to top
        Member(id="M3", start_node="N2", end_node="N3", material="steel"),  # Diagonal to top
    ]
    
    supports = [
        Support(node_id="N1", type="pin"),
        Support(node_id="N2", type="roller"),
    ]
    
    model = StructuralModel(nodes=nodes, members=members, supports=supports)
    loads = [Load(node_id="N3", fx=0.0, fy=-1000.0)]
    
    results = solve(model, loads)
    
    # Check reactions sum to applied load (equilibrium)
    total_reaction_y = sum(r.ry for r in results.reactions)
    assert abs(total_reaction_y - 1000.0) < 1.0  # Within 1N tolerance
    
    # For symmetric structure, reactions should be equal
    reactions_y = [r.ry for r in results.reactions]
    assert abs(reactions_y[0] - 500.0) < 50.0  # Within 50N tolerance (frame action)
    assert abs(reactions_y[1] - 500.0) < 50.0


def test_cantilever_beam():
    """Test cantilever beam with end load."""
    # Cantilever: fixed at one end, load at other
    # Length = 1000 mm, load = 500 N
    
    nodes = [
        Node(id="N1", x=0.0, y=0.0),
        Node(id="N2", x=1000.0, y=0.0),
    ]
    
    members = [
        Member(id="M1", start_node="N1", end_node="N2", material="steel"),
    ]
    
    supports = [
        Support(node_id="N1", type="fixed"),
    ]
    
    model = StructuralModel(nodes=nodes, members=members, supports=supports)
    loads = [Load(node_id="N2", fx=0.0, fy=-500.0)]
    
    results = solve(model, loads)
    
    # Reaction should equal applied load
    assert len(results.reactions) == 1
    assert abs(results.reactions[0].ry - 500.0) < 1.0
    
    # Should have deflection
    assert results.max_deflection > 0


def test_equilibrium_check():
    """Test that sum of forces equals zero (equilibrium)."""
    nodes = [
        Node(id="N1", x=0.0, y=0.0),
        Node(id="N2", x=1000.0, y=0.0),
        Node(id="N3", x=500.0, y=500.0),
    ]
    
    members = [
        Member(id="M1", start_node="N1", end_node="N2", material="steel"),
        Member(id="M2", start_node="N2", end_node="N3", material="steel"),
        Member(id="M3", start_node="N3", end_node="N1", material="steel"),
    ]
    
    supports = [
        Support(node_id="N1", type="pin"),
        Support(node_id="N2", type="roller"),
    ]
    
    model = StructuralModel(nodes=nodes, members=members, supports=supports)
    
    # Apply multiple loads
    loads = [
        Load(node_id="N3", fx=0.0, fy=-2000.0),
    ]
    
    results = solve(model, loads)
    
    # Sum of all vertical reactions should equal sum of applied loads
    total_applied_fy = sum(load.fy for load in loads)
    total_reaction_fy = sum(r.ry for r in results.reactions)
    
    assert abs(total_reaction_fy - abs(total_applied_fy)) < 1.0


def test_horizontal_load():
    """Test truss with horizontal load."""
    nodes = [
        Node(id="N1", x=0.0, y=0.0),
        Node(id="N2", x=1000.0, y=0.0),
        Node(id="N3", x=500.0, y=500.0),
    ]
    
    members = [
        Member(id="M1", start_node="N1", end_node="N2", material="steel"),
        Member(id="M2", start_node="N2", end_node="N3", material="steel"),
        Member(id="M3", start_node="N3", end_node="N1", material="steel"),
    ]
    
    supports = [
        Support(node_id="N1", type="pin"),
        Support(node_id="N2", type="roller"),
    ]
    
    model = StructuralModel(nodes=nodes, members=members, supports=supports)
    loads = [Load(node_id="N3", fx=1000.0, fy=0.0)]
    
    results = solve(model, loads)
    
    # Should have horizontal reaction at pin support
    pin_reaction = next(r for r in results.reactions if r.node_id == "N1")
    assert abs(pin_reaction.rx) > 0  # Should resist horizontal load


def test_zero_load():
    """Test that very small loads produce small reactions."""
    nodes = [
        Node(id="N1", x=0.0, y=0.0),
        Node(id="N2", x=1000.0, y=0.0),
        Node(id="N3", x=500.0, y=500.0),
    ]
    
    members = [
        Member(id="M1", start_node="N1", end_node="N2", material="steel"),
        Member(id="M2", start_node="N1", end_node="N3", material="steel"),
        Member(id="M3", start_node="N2", end_node="N3", material="steel"),
    ]
    
    supports = [
        Support(node_id="N1", type="pin"),
        Support(node_id="N2", type="roller"),
    ]
    
    model = StructuralModel(nodes=nodes, members=members, supports=supports)
    loads = [Load(node_id="N3", fx=0.0, fy=-1.0)]  # Very small load (1N)
    
    results = solve(model, loads)
    
    # Sum of reactions should equal small applied load
    total_fy = sum(r.ry for r in results.reactions)
    assert abs(total_fy - 1.0) < 0.1
