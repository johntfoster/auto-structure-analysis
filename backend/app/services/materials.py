"""Material properties service for structural analysis."""

from dataclasses import dataclass


@dataclass
class Material:
    """Material properties for structural analysis."""
    name: str
    E: float  # Elastic modulus (MPa)
    fy: float  # Yield strength (MPa)
    density: float  # kg/m³
    description: str


# Preset materials
_MATERIALS = {
    "steel": Material(
        name="steel",
        E=200000.0,  # MPa (200 GPa)
        fy=250.0,  # MPa (A36 steel)
        density=7850.0,  # kg/m³
        description="Structural Steel (A36)"
    ),
    "aluminum": Material(
        name="aluminum",
        E=69000.0,  # MPa (69 GPa)
        fy=270.0,  # MPa (6061-T6)
        density=2700.0,  # kg/m³
        description="Aluminum Alloy (6061-T6)"
    ),
    "wood": Material(
        name="wood",
        E=12000.0,  # MPa (12 GPa)
        fy=40.0,  # MPa (Southern Pine)
        density=550.0,  # kg/m³
        description="Wood (Southern Pine)"
    ),
}


def get_material(name: str) -> Material:
    """
    Get material properties by name.
    
    Args:
        name: Material name (steel, aluminum, or wood)
        
    Returns:
        Material properties
        
    Raises:
        ValueError: If material name is not recognized
    """
    name = name.lower()
    if name not in _MATERIALS:
        raise ValueError(
            f"Unknown material: {name}. "
            f"Available materials: {', '.join(_MATERIALS.keys())}"
        )
    return _MATERIALS[name]


def list_materials() -> list[Material]:
    """
    List all available materials.
    
    Returns:
        List of all preset materials
    """
    return list(_MATERIALS.values())
