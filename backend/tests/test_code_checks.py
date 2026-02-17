"""Tests for building code compliance checks."""

import pytest
from app.services.code_checks import (
    check_aisc_slenderness,
    check_aisc_compression_capacity,
    check_aisc_tension_capacity,
    check_aisc_combined_loading,
    perform_code_checks
)


class TestAISCCodeChecks:
    """Test suite for AISC code compliance checks."""
    
    def test_slenderness_pass(self):
        """Test slenderness check that passes."""
        # Short column: L = 1000mm, r = 20mm
        # KL/r = 1.0 * 1000 / 20 = 50 (< 200, should pass)
        result = check_aisc_slenderness(
            length=1000.0,
            radius_of_gyration=20.0,
            fy=250.0,
            E=200000.0,
            axial_force=-10000.0
        )
        
        assert result.code == "AISC"
        assert result.status == "PASS"
        assert result.ratio < 1.0
        assert "E2" in result.reference
    
    def test_slenderness_fail(self):
        """Test slenderness check that fails."""
        # Slender column: L = 5000mm, r = 20mm
        # KL/r = 1.0 * 5000 / 20 = 250 (> 200, should fail)
        result = check_aisc_slenderness(
            length=5000.0,
            radius_of_gyration=20.0,
            fy=250.0,
            E=200000.0,
            axial_force=-10000.0
        )
        
        assert result.code == "AISC"
        assert result.status == "FAIL"
        assert result.ratio > 1.0
    
    def test_compression_capacity_short_column(self):
        """Test compression capacity for short column (inelastic buckling)."""
        # Short, stocky column
        result = check_aisc_compression_capacity(
            area=1000.0,  # mm²
            length=500.0,  # mm
            radius_of_gyration=30.0,  # mm
            fy=250.0,  # MPa
            E=200000.0,  # MPa
            axial_force=-50000.0  # N (compression)
        )
        
        assert result.code == "AISC"
        assert result.status in ["PASS", "FAIL"]
        assert result.ratio >= 0.0
        assert "Chapter E" in result.reference
    
    def test_compression_capacity_slender_column(self):
        """Test compression capacity for slender column (elastic buckling)."""
        # Long, slender column
        result = check_aisc_compression_capacity(
            area=500.0,  # mm²
            length=3000.0,  # mm
            radius_of_gyration=15.0,  # mm
            fy=250.0,  # MPa
            E=200000.0,  # MPa
            axial_force=-10000.0  # N (compression)
        )
        
        assert result.code == "AISC"
        assert result.status in ["PASS", "FAIL"]
        assert "Chapter E" in result.reference
    
    def test_compression_not_applicable_for_tension(self):
        """Test that compression check is N/A for tension members."""
        result = check_aisc_compression_capacity(
            area=500.0,
            length=1000.0,
            radius_of_gyration=20.0,
            fy=250.0,
            E=200000.0,
            axial_force=10000.0  # Positive = tension
        )
        
        assert result.status == "PASS"
        assert result.ratio == 0.0
        assert "tension" in result.details.lower()
    
    def test_tension_capacity_pass(self):
        """Test tension capacity check that passes."""
        result = check_aisc_tension_capacity(
            area=1000.0,  # mm²
            fy=250.0,  # MPa
            fu=400.0,  # MPa
            axial_force=50000.0  # N (tension)
        )
        
        assert result.code == "AISC"
        # φPn = 0.9 * 250 * 1000 = 225,000 N
        # Ratio = 50,000 / 225,000 = 0.22 < 1.0
        assert result.status == "PASS"
        assert result.ratio < 1.0
        assert "Chapter D" in result.reference
    
    def test_tension_capacity_fail(self):
        """Test tension capacity check that fails."""
        result = check_aisc_tension_capacity(
            area=500.0,  # mm²
            fy=250.0,  # MPa
            fu=400.0,  # MPa
            axial_force=150000.0  # N (high tension)
        )
        
        assert result.code == "AISC"
        # φPn = 0.9 * 250 * 500 = 112,500 N
        # Ratio = 150,000 / 112,500 = 1.33 > 1.0
        assert result.status == "FAIL"
        assert result.ratio > 1.0
    
    def test_tension_not_applicable_for_compression(self):
        """Test that tension check is N/A for compression members."""
        result = check_aisc_tension_capacity(
            area=500.0,
            fy=250.0,
            fu=400.0,
            axial_force=-10000.0  # Negative = compression
        )
        
        assert result.status == "PASS"
        assert result.ratio == 0.0
        assert "compression" in result.details.lower()
    
    def test_combined_loading_high_axial(self):
        """Test combined loading with high axial ratio (>= 0.2)."""
        # Uses equation: (Pr/Pc) + (8/9)(Mr/Mc) <= 1.0
        result = check_aisc_combined_loading(
            area=1000.0,
            section_modulus=10000.0,
            axial_force=30000.0,  # N
            moment=50000000.0,  # N·mm
            fy=250.0,
            Pc=100000.0,  # N
            Mc=200000000.0  # N·mm
        )
        
        assert result.code == "AISC"
        # Pr/Pc = 30000/100000 = 0.3 (>= 0.2)
        # Mr/Mc = 50e6/200e6 = 0.25
        # Ratio = 0.3 + (8/9)*0.25 = 0.3 + 0.222 = 0.522 < 1.0
        assert result.status == "PASS"
        assert result.ratio < 1.0
        assert "Chapter H" in result.reference
    
    def test_combined_loading_low_axial(self):
        """Test combined loading with low axial ratio (< 0.2)."""
        # Uses equation: (Pr/2Pc) + (Mr/Mc) <= 1.0
        result = check_aisc_combined_loading(
            area=1000.0,
            section_modulus=10000.0,
            axial_force=10000.0,  # N (low)
            moment=100000000.0,  # N·mm
            fy=250.0,
            Pc=100000.0,  # N
            Mc=200000000.0  # N·mm
        )
        
        assert result.code == "AISC"
        # Pr/Pc = 10000/100000 = 0.1 (< 0.2)
        # Mr/Mc = 100e6/200e6 = 0.5
        # Ratio = 0.1/2 + 0.5 = 0.05 + 0.5 = 0.55 < 1.0
        assert result.status == "PASS"
        assert result.ratio < 1.0
    
    def test_combined_loading_fail(self):
        """Test combined loading that fails."""
        result = check_aisc_combined_loading(
            area=1000.0,
            section_modulus=10000.0,
            axial_force=80000.0,  # N (high)
            moment=150000000.0,  # N·mm (high)
            fy=250.0,
            Pc=100000.0,  # N
            Mc=200000000.0  # N·mm
        )
        
        assert result.code == "AISC"
        # Pr/Pc = 80000/100000 = 0.8 (>= 0.2)
        # Mr/Mc = 150e6/200e6 = 0.75
        # Ratio = 0.8 + (8/9)*0.75 = 0.8 + 0.667 = 1.467 > 1.0
        assert result.status == "FAIL"
        assert result.ratio > 1.0
    
    def test_perform_code_checks_compression_member(self):
        """Test comprehensive code checks for compression member."""
        checks = perform_code_checks(
            member_id="M1",
            length=2000.0,
            area=1000.0,
            section_modulus=15000.0,
            radius_of_gyration=25.0,
            axial_force=-50000.0,  # Compression
            moment=10000000.0,
            material_name="steel",
            code="AISC"
        )
        
        assert checks.member_id == "M1"
        assert len(checks.checks) >= 2  # Slenderness + compression
        assert checks.overall_status in ["PASS", "FAIL"]
        
        # Should have slenderness check
        assert any(c.check_name == "Slenderness Ratio" for c in checks.checks)
        
        # Should have compression capacity check
        assert any(c.check_name == "Compression Capacity" for c in checks.checks)
    
    def test_perform_code_checks_tension_member(self):
        """Test comprehensive code checks for tension member."""
        checks = perform_code_checks(
            member_id="M2",
            length=1500.0,
            area=800.0,
            section_modulus=12000.0,
            radius_of_gyration=22.0,
            axial_force=40000.0,  # Tension
            moment=0.0,  # No moment
            material_name="steel",
            code="AISC"
        )
        
        assert checks.member_id == "M2"
        assert len(checks.checks) >= 2  # Slenderness + tension
        
        # Should have tension capacity check
        assert any(c.check_name == "Tension Capacity" for c in checks.checks)
    
    def test_code_check_result_structure(self):
        """Test that code check results have proper structure."""
        result = check_aisc_slenderness(
            length=1000.0,
            radius_of_gyration=20.0,
            fy=250.0,
            E=200000.0,
            axial_force=-10000.0
        )
        
        # Verify all required fields are present
        assert hasattr(result, 'code')
        assert hasattr(result, 'check_name')
        assert hasattr(result, 'status')
        assert hasattr(result, 'ratio')
        assert hasattr(result, 'reference')
        assert hasattr(result, 'details')
        
        # Verify field types
        assert result.code in ["AISC", "NDS"]
        assert result.status in ["PASS", "FAIL"]
        assert isinstance(result.ratio, float)
        assert isinstance(result.reference, str)
        assert isinstance(result.details, str)
