"""FEA solver using PyNite for structural analysis."""

import math
from Pynite import FEModel3D
from app.models.schemas import (
    StructuralModel, 
    Load, 
    AnalysisResults, 
    MemberForce, 
    Reaction,
    Node
)
from app.services.materials import Material, get_material
from app.exceptions import SolverError


def solve(model: StructuralModel, loads: list[Load], material_name: str = "steel") -> AnalysisResults:
    """
    Solve structural model using PyNite FEA.
    
    Args:
        model: Structural model with nodes, members, and supports
        loads: List of point loads to apply
        material_name: Material to use for analysis (steel, aluminum, or wood)
        
    Returns:
        Analysis results with member forces, reactions, deflections, and safety checks
        
    Raises:
        SolverError: If analysis fails
    """
    try:
        # Get material properties
        material = get_material(material_name)
        
        # Create PyNite model
        fem = FEModel3D()
        
        # Create a lookup for node coordinates
        node_coords = {node.id: (node.x, node.y) for node in model.nodes}
        
        # Add nodes to PyNite model (z=0 for 2D truss)
        for node in model.nodes:
            fem.add_node(node.id, node.x, node.y, 0.0)
        
        # Convert material properties to PyNite units (N/mm²)
        E = material.E  # MPa = N/mm²
        G = E / (2 * (1 + 0.3))  # Shear modulus (assuming nu = 0.3)
        nu = 0.3  # Poisson's ratio
        rho = material.density / 1e9  # kg/m³ → kg/mm³
        
        # Add material
        fem.add_material(material_name, E, G, nu, rho)
        
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
                material_name,
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
        
        # Cross-sectional area for stress calculation
        A = 500.0  # mm²
        
        # Extract member forces and calculate stresses
        member_forces = []
        max_stress_ratio = 0.0
        
        for member in model.members:
            # Get axial force at start of member (for truss, constant along length)
            # PyNite uses 'Fx' for axial force in local coordinates
            axial = fem.members[member.id].max_axial()
            shear = fem.members[member.id].max_shear("Fy")  # Shear in local y
            moment = fem.members[member.id].max_moment("Mz")  # Moment about local z
            
            # Calculate axial stress (MPa = N/mm²)
            stress = abs(axial) / A  # MPa
            
            # Calculate stress ratio
            stress_ratio = stress / material.fy
            max_stress_ratio = max(max_stress_ratio, stress_ratio)
            
            member_forces.append(MemberForce(
                member_id=member.id,
                axial=axial,
                shear=shear,
                moment=moment,
                stress=stress,
                stress_ratio=stress_ratio
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
        
        # Calculate maximum deflection and create nodes with displacement data
        max_deflection = 0.0
        nodes_with_displacements = []
        
        for node in model.nodes:
            dx = fem.nodes[node.id].DX.get("Combo 1", 0.0)
            dy = fem.nodes[node.id].DY.get("Combo 1", 0.0)
            deflection = math.sqrt(dx**2 + dy**2)
            max_deflection = max(max_deflection, deflection)
            
            # Create node with displacement data
            nodes_with_displacements.append(Node(
                id=node.id,
                x=node.x,
                y=node.y,
                displacement_x=dx,
                displacement_y=dy
            ))
        
        # Determine safety status
        if max_stress_ratio >= 1.0:
            safety_status = "FAIL"
        elif max_stress_ratio >= 0.8:
            safety_status = "WARNING"
        else:
            safety_status = "PASS"
        
        return AnalysisResults(
            member_forces=member_forces,
            reactions=reactions,
            max_deflection=max_deflection,
            safety_status=safety_status,
            max_stress_ratio=max_stress_ratio,
            nodes_with_displacements=nodes_with_displacements
        )
    
    except Exception as e:
        raise SolverError(f"FEA analysis failed: {str(e)}") from e
