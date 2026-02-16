"""Tests for materials service."""

import pytest
from app.services.materials import get_material, list_materials, Material


def test_all_preset_materials_have_valid_properties():
    """Test that all preset materials have valid, non-zero properties."""
    materials = list_materials()
    
    assert len(materials) == 3, "Should have 3 preset materials"
    
    for mat in materials:
        assert isinstance(mat, Material)
        assert mat.name in ["steel", "aluminum", "wood"]
        assert mat.E > 0, f"{mat.name} should have positive elastic modulus"
        assert mat.fy > 0, f"{mat.name} should have positive yield strength"
        assert mat.density > 0, f"{mat.name} should have positive density"
        assert mat.description, f"{mat.name} should have description"


def test_get_material_steel():
    """Test getting steel material properties."""
    steel = get_material("steel")
    
    assert steel.name == "steel"
    assert steel.E == 200000.0  # 200 GPa in MPa
    assert steel.fy == 250.0  # MPa
    assert steel.density == 7850.0  # kg/m³
    assert "A36" in steel.description


def test_get_material_aluminum():
    """Test getting aluminum material properties."""
    aluminum = get_material("aluminum")
    
    assert aluminum.name == "aluminum"
    assert aluminum.E == 69000.0  # 69 GPa in MPa
    assert aluminum.fy == 270.0  # MPa
    assert aluminum.density == 2700.0  # kg/m³
    assert "6061-T6" in aluminum.description


def test_get_material_wood():
    """Test getting wood material properties."""
    wood = get_material("wood")
    
    assert wood.name == "wood"
    assert wood.E == 12000.0  # 12 GPa in MPa
    assert wood.fy == 40.0  # MPa
    assert wood.density == 550.0  # kg/m³
    assert "Southern Pine" in wood.description


def test_get_material_case_insensitive():
    """Test that material names are case-insensitive."""
    steel_lower = get_material("steel")
    steel_upper = get_material("STEEL")
    steel_mixed = get_material("Steel")
    
    assert steel_lower.name == steel_upper.name == steel_mixed.name == "steel"


def test_get_material_invalid_raises_error():
    """Test that invalid material name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown material"):
        get_material("concrete")
    
    with pytest.raises(ValueError, match="Unknown material"):
        get_material("invalid")


def test_list_materials_returns_all_presets():
    """Test that list_materials returns all preset materials."""
    materials = list_materials()
    
    assert len(materials) == 3
    
    material_names = {m.name for m in materials}
    assert material_names == {"steel", "aluminum", "wood"}


def test_materials_have_expected_relative_properties():
    """Test that materials have expected relative properties."""
    steel = get_material("steel")
    aluminum = get_material("aluminum")
    wood = get_material("wood")
    
    # Steel should be stiffer than aluminum and wood
    assert steel.E > aluminum.E > wood.E
    
    # Steel should be denser than aluminum and wood
    assert steel.density > aluminum.density > wood.density
