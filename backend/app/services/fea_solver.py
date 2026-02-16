"""FEA solver using PyNite for structural analysis."""

import math
from Pynite import FEModel3D
from app.models.schemas import (
    StructuralModel, 
    Load, 
    AnalysisResults, 
    MemberForce, 
    Reaction
)


def solve(model: StructuralModel, loads: list[Load]) -> AnalysisResults:
    """
    Solve structural model using PyNite FEA.
    
    Args:
        model: Structural model with nodes, members, and supports
        loads: List of point loads to apply
        
    Returns:
        Analysis results with member forces, reactions, and deflections
    """
    # Create PyNite model
    fem = FEModel3D()
    
    # Create a lookup for node coordinates
    node_coords = {node.id: (node.x, node.y) for node in model.nodes}
    
    # Add nodes to PyNite model (z=0 for 2D truss)
    for node in model.nodes:
        fem.add_node(node.id, node.x, node.y, 0.0)
    
    # Material properties for steel
    E = 200000.0  # N/mm² (Young's modulus for steel)
    G = 80000.0   # N/mm² (Shear modulus)
    nu = 0.3      # Poisson's ratio
    rho = 7.85e-6 # kg/mm³ (density)
    
    # Add material
    fem.add_material("steel", E, G, nu, rho)
    
    # Cross-sectional properties (typical small truss member)
    A = 500.0    # mm² (cross-sectional area)
    Iy = 5000.0  # mm⁴ (moment of inertia about y-axis)
    Iz = 5000.0  # mm⁴ (moment of inertia about z-axis)
    J = 10000.0  # mm⁴ (torsional constant)
    
    # Add section
    fem.add_section("truss_section", A, Iy, Iz, J)
    
    # Add members to PyNite model
    for member in model.members:
        fem.add_member(
            member.id,
            member.start_node,
            member.end_node,
            "steel",
            "truss_section"
        )
    
    # Add supports
    for support in model.supports:
        node_id = support.node_id
        if support.type == "pin":
            # Pin support: fixed in x, y, free rotation
            fem.def_support(node_id, True, True, True, False, False, False)
        elif support.type == "roller":
            # Roller support: fixed in y only, free in x and rotation
            fem.def_support(node_id, False, True, True, False, False, False)
        elif support.type == "fixed":
            # Fixed support: all DOFs constrained
            fem.def_support(node_id, True, True, True, True, True, True)
    
    # Add loads
    for load in loads:
        if load.fx != 0.0:
            fem.add_node_load(load.node_id, "FX", load.fx)
        if load.fy != 0.0:
            fem.add_node_load(load.node_id, "FY", load.fy)
    
    # Analyze the model
    fem.analyze(check_statics=True)
    
    # Extract member forces
    member_forces = []
    for member in model.members:
        # Get axial force at start of member (for truss, constant along length)
        # PyNite uses 'Fx' for axial force in local coordinates
        axial = fem.members[member.id].max_axial()
        shear = fem.members[member.id].max_shear("Fy")  # Shear in local y
        moment = fem.members[member.id].max_moment("Mz")  # Moment about local z
        
        member_forces.append(MemberForce(
            member_id=member.id,
            axial=axial,
            shear=shear,
            moment=moment
        ))
    
    # Extract reactions
    reactions = []
    for support in model.supports:
        node_id = support.node_id
        rx = fem.nodes[node_id].RxnFX.get("Combo 1", 0.0)
        ry = fem.nodes[node_id].RxnFY.get("Combo 1", 0.0)
        
        reactions.append(Reaction(
            node_id=node_id,
            rx=rx,
            ry=ry
        ))
    
    # Calculate maximum deflection
    max_deflection = 0.0
    for node in model.nodes:
        dx = fem.nodes[node.id].DX.get("Combo 1", 0.0)
        dy = fem.nodes[node.id].DY.get("Combo 1", 0.0)
        deflection = math.sqrt(dx**2 + dy**2)
        max_deflection = max(max_deflection, deflection)
    
    return AnalysisResults(
        member_forces=member_forces,
        reactions=reactions,
        max_deflection=max_deflection
    )
