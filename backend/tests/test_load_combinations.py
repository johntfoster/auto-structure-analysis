"""Tests for load combinations."""

import pytest
from app.models.schemas import (
    StructuralModel, Node, Member, Support, Load,
    LoadCase, LoadCombination
)
from app.services.fea_solver import (
    solve_with_combinations, get_envelope_results
)


class TestLoadCombinations:
    """Test suite for load combinations."""
    
    def setup_method(self):
        """Set up test fixture - simple beam."""
        self.model = StructuralModel(
            structure_type="frame",
            nodes=[
                Node(id="A", x=0.0, y=0.0),
                Node(id="B", x=1000.0, y=0.0),
                Node(id="C", x=2000.0, y=0.0),
            ],
            members=[
                Member(id="m1", start_node="A", end_node="B"),
                Member(id="m2", start_node="B", end_node="C"),
            ],
            supports=[
                Support(node_id="A", type="pin"),
                Support(node_id="C", type="roller"),
            ]
        )
    
    def test_load_case_schema(self):
        """Test LoadCase model."""
        dead_load = LoadCase(
            name="Dead",
            type="dead",
            loads=[Load(node_id="B", fx=0.0, fy=-500.0)],
            description="Self-weight"
        )
        
        assert dead_load.name == "Dead"
        assert dead_load.type == "dead"
        assert len(dead_load.loads) == 1
    
    def test_load_combination_schema(self):
        """Test LoadCombination model."""
        combo = LoadCombination(
            name="1.2D + 1.6L",
            factors={"Dead": 1.2, "Live": 1.6},
            description="ASCE 7-16 Strength Design"
        )
        
        assert combo.name == "1.2D + 1.6L"
        assert combo.factors["Dead"] == 1.2
        assert combo.factors["Live"] == 1.6
    
    def test_solve_single_combination(self):
        """Test solving with a single load combination."""
        # Define load cases
        dead = LoadCase(
            name="Dead",
            type="dead",
            loads=[Load(node_id="B", fx=0.0, fy=-500.0)]
        )
        
        live = LoadCase(
            name="Live",
            type="live",
            loads=[Load(node_id="B", fx=0.0, fy=-1000.0)]
        )
        
        # Define combination: 1.2D + 1.6L
        combo = LoadCombination(
            name="1.2D+1.6L",
            factors={"Dead": 1.2, "Live": 1.6}
        )
        
        # Solve
        results = solve_with_combinations(
            self.model,
            [dead, live],
            [combo],
            material_name="steel"
        )
        
        assert "1.2D+1.6L" in results
        assert results["1.2D+1.6L"].safety_status in ["PASS", "WARNING", "FAIL"]
    
    def test_solve_multiple_combinations(self):
        """Test solving with multiple load combinations."""
        # Define load cases
        dead = LoadCase(
            name="Dead",
            type="dead",
            loads=[Load(node_id="B", fx=0.0, fy=-500.0)]
        )
        
        live = LoadCase(
            name="Live",
            type="live",
            loads=[Load(node_id="B", fx=0.0, fy=-1000.0)]
        )
        
        wind = LoadCase(
            name="Wind",
            type="wind",
            loads=[Load(node_id="B", fx=800.0, fy=0.0)]
        )
        
        # Define multiple combinations
        combos = [
            LoadCombination(name="1.4D", factors={"Dead": 1.4}),
            LoadCombination(name="1.2D+1.6L", factors={"Dead": 1.2, "Live": 1.6}),
            LoadCombination(name="1.2D+1.0L+1.0W", factors={"Dead": 1.2, "Live": 1.0, "Wind": 1.0}),
        ]
        
        # Solve
        results = solve_with_combinations(
            self.model,
            [dead, live, wind],
            combos,
            material_name="steel"
        )
        
        assert len(results) == 3
        assert "1.4D" in results
        assert "1.2D+1.6L" in results
        assert "1.2D+1.0L+1.0W" in results
    
    def test_load_combination_factors(self):
        """Test that load combination factors are applied correctly."""
        # Use a truss model for clearer stress behavior
        truss_model = StructuralModel(
            structure_type="truss",
            nodes=[
                Node(id="A", x=0.0, y=0.0),
                Node(id="B", x=1000.0, y=0.0),
                Node(id="C", x=500.0, y=500.0),
            ],
            members=[
                Member(id="m1", start_node="A", end_node="C"),
                Member(id="m2", start_node="B", end_node="C"),
                Member(id="m3", start_node="A", end_node="B"),
            ],
            supports=[
                Support(node_id="A", type="pin"),
                Support(node_id="B", type="roller"),
            ]
        )
        
        # Single load case
        dead = LoadCase(
            name="Dead",
            type="dead",
            loads=[Load(node_id="C", fx=0.0, fy=-10000.0)]
        )
        
        # Two combinations with different factors
        combo1 = LoadCombination(name="1.0D", factors={"Dead": 1.0})
        combo2 = LoadCombination(name="1.4D", factors={"Dead": 1.4})
        
        # Solve
        results = solve_with_combinations(
            truss_model,
            [dead],
            [combo1, combo2],
            material_name="steel"
        )
        
        # 1.4D should have larger forces than 1.0D
        stress_1D = results["1.0D"].max_stress_ratio
        stress_14D = results["1.4D"].max_stress_ratio
        
        assert stress_14D > stress_1D
        # Should be approximately 1.4x (within tolerance for nonlinear effects)
        assert 1.3 < (stress_14D / stress_1D) < 1.5
    
    def test_envelope_results(self):
        """Test envelope (maximum) results from multiple combinations."""
        # Define load cases
        dead = LoadCase(
            name="Dead",
            type="dead",
            loads=[Load(node_id="B", fx=0.0, fy=-500.0)]
        )
        
        live = LoadCase(
            name="Live",
            type="live",
            loads=[Load(node_id="B", fx=0.0, fy=-1000.0)]
        )
        
        # Multiple combinations
        combos = [
            LoadCombination(name="1.4D", factors={"Dead": 1.4}),
            LoadCombination(name="1.2D+1.6L", factors={"Dead": 1.2, "Live": 1.6}),
        ]
        
        # Solve
        results = solve_with_combinations(
            self.model,
            [dead, live],
            combos,
            material_name="steel"
        )
        
        # Get envelope
        envelope = get_envelope_results(results)
        
        # Envelope should have the maximum stress ratio
        max_stress_from_combos = max(r.max_stress_ratio for r in results.values())
        assert envelope.max_stress_ratio == max_stress_from_combos
        
        # Envelope should have safety status
        assert envelope.safety_status in ["PASS", "WARNING", "FAIL"]
    
    def test_missing_load_case_error(self):
        """Test error when referencing non-existent load case."""
        dead = LoadCase(
            name="Dead",
            type="dead",
            loads=[Load(node_id="B", fx=0.0, fy=-500.0)]
        )
        
        # Combination references "Live" which doesn't exist
        combo = LoadCombination(
            name="1.2D+1.6L",
            factors={"Dead": 1.2, "Live": 1.6}
        )
        
        with pytest.raises(Exception) as exc_info:
            solve_with_combinations(
                self.model,
                [dead],  # Only Dead, no Live
                [combo],
                material_name="steel"
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_standard_asce_combinations(self):
        """Test standard ASCE 7-16 load combinations."""
        # Define load cases
        dead = LoadCase(name="D", type="dead", 
                       loads=[Load(node_id="B", fx=0.0, fy=-500.0)])
        live = LoadCase(name="L", type="live",
                       loads=[Load(node_id="B", fx=0.0, fy=-800.0)])
        wind = LoadCase(name="W", type="wind",
                       loads=[Load(node_id="B", fx=600.0, fy=0.0)])
        
        # ASCE 7-16 strength design combinations
        combos = [
            LoadCombination(name="1.4D", factors={"D": 1.4}),
            LoadCombination(name="1.2D+1.6L", factors={"D": 1.2, "L": 1.6}),
            LoadCombination(name="1.2D+1.0L+1.0W", factors={"D": 1.2, "L": 1.0, "W": 1.0}),
            LoadCombination(name="0.9D+1.0W", factors={"D": 0.9, "W": 1.0}),
        ]
        
        # Solve all combinations
        results = solve_with_combinations(
            self.model,
            [dead, live, wind],
            combos,
            material_name="steel"
        )
        
        assert len(results) == 4
        
        # All should have valid results
        for combo_name, result in results.items():
            assert result.safety_status in ["PASS", "WARNING", "FAIL"]
            assert len(result.member_forces) == 2
