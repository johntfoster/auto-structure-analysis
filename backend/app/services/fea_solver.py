"""FEA solver using PyNite for structural analysis."""

import math
from Pynite import FEModel3D
from app.models.schemas import (
    StructuralModel, 
    Load, 
    LoadCase,
    LoadCombination,
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
        
        # Determine if this is a truss or frame structure
        is_frame = model.structure_type == "frame"
        
        # Create PyNite model
        fem = FEModel3D()
        
        # Create a lookup for node coordinates
        node_coords = {node.id: (node.x, node.y) for node in model.nodes}
        
        # Add nodes to PyNite model (z=0 for 2D structure)
        for node in model.nodes:
            fem.add_node(node.id, node.x, node.y, 0.0)
            
            # For 2D planar analysis, constrain out-of-plane DOFs
            # This prevents instability in Z-direction and rotations about X and Y
            if not is_frame:
                # For trusses in XY plane: constrain DZ, RX, RY, and RZ
                # Trusses are pin-connected so no moment transfer anyway
                fem.def_support(node.id, support_DX=False, support_DY=False, support_DZ=True,
                              support_RX=True, support_RY=True, support_RZ=True)
            else:
                # For frames in XY plane: constrain DZ and rotations about X and Y
                # Keep RZ free for moment connections
                fem.def_support(node.id, support_DX=False, support_DY=False, support_DZ=True,
                              support_RX=True, support_RY=True, support_RZ=False)
        
        # Convert material properties to PyNite units (N/mm²)
        E = material.E  # MPa = N/mm²
        G = E / (2 * (1 + 0.3))  # Shear modulus (assuming nu = 0.3)
        nu = 0.3  # Poisson's ratio
        rho = material.density / 1e9  # kg/m³ → kg/mm³
        
        # Add material
        fem.add_material(material_name, E, G, nu, rho)
        
        # Cross-sectional properties
        # For frames, use larger moment of inertia to handle bending
        if is_frame:
            A = 1000.0    # mm² (cross-sectional area)
            Iy = 50000.0  # mm⁴ (moment of inertia about y-axis)
            Iz = 50000.0  # mm⁴ (moment of inertia about z-axis)
            J = 100000.0  # mm⁴ (torsional constant)
            section_name = "frame_section"
        else:
            # Truss members (smaller section)
            A = 500.0    # mm² (cross-sectional area)
            Iy = 5000.0  # mm⁴ (moment of inertia about y-axis)
            Iz = 5000.0  # mm⁴ (moment of inertia about z-axis)
            J = 10000.0  # mm⁴ (torsional constant)
            section_name = "truss_section"
        
        # Add section
        fem.add_section(section_name, A, Iy, Iz, J)
        
        # Add members to PyNite model
        for member in model.members:
            fem.add_member(
                member.id,
                member.start_node,
                member.end_node,
                material_name,
                section_name
            )
            # Note: For trusses, rotations are already constrained at nodes
            # For frames, rotations are free to allow moment transfer
        
        # Add supports (override the default node constraints)
        for support in model.supports:
            node_id = support.node_id
            if support.type == "pin":
                # Pin support: fixed in x, y, z, free rotation about z (in-plane rotation)
                fem.def_support(node_id, True, True, True, True, True, False if is_frame else True)
            elif support.type == "roller":
                # Roller support: fixed in y, z only, free in x and rotation
                fem.def_support(node_id, False, True, True, True, True, False if is_frame else True)
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
        
        # Extract member forces and calculate stresses
        member_forces = []
        max_stress_ratio = 0.0
        
        for member in model.members:
            # Get axial force at start of member
            # PyNite uses 'Fx' for axial force in local coordinates
            axial = fem.members[member.id].max_axial()
            shear = fem.members[member.id].max_shear("Fy")  # Shear in local y
            moment = fem.members[member.id].max_moment("Mz")  # Moment about local z
            
            # Calculate stresses based on structure type
            if is_frame:
                # For frames, consider both axial and bending stress
                # Axial stress: σ_a = P/A
                axial_stress = abs(axial) / A
                
                # Bending stress: σ_b = M*c/I where c = depth/2
                # Assume rectangular section: depth = sqrt(12*I/width), width = A/depth
                # Simplified: use section modulus S = I/c
                depth = 30.0  # mm (assumed depth for visualization)
                S = Iz / (depth / 2)  # Section modulus
                bending_stress = abs(moment) / S if S > 0 else 0.0
                
                # Combined stress (simplified - ignores interaction)
                stress = axial_stress + bending_stress  # MPa
            else:
                # For trusses, only axial stress
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


def solve_with_combinations(
    model: StructuralModel,
    load_cases: list[LoadCase],
    combinations: list[LoadCombination],
    material_name: str = "steel"
) -> dict[str, AnalysisResults]:
    """
    Solve structural model with multiple load combinations.
    
    Args:
        model: Structural model with nodes, members, and supports
        load_cases: List of named load cases
        combinations: List of load combinations with factors
        material_name: Material to use for analysis
        
    Returns:
        Dictionary mapping combination name to analysis results
        
    Raises:
        SolverError: If analysis fails
    """
    results = {}
    
    # Create lookup for load cases
    load_case_map = {lc.name: lc for lc in load_cases}
    
    for combo in combinations:
        # Combine loads according to factors
        combined_loads = []
        load_map: dict[str, Load] = {}  # Map node_id to combined load
        
        for case_name, factor in combo.factors.items():
            if case_name not in load_case_map:
                raise SolverError(f"Load case '{case_name}' not found")
            
            case = load_case_map[case_name]
            for load in case.loads:
                if load.node_id not in load_map:
                    load_map[load.node_id] = Load(
                        node_id=load.node_id,
                        fx=0.0,
                        fy=0.0
                    )
                
                # Add factored loads
                load_map[load.node_id].fx += load.fx * factor
                load_map[load.node_id].fy += load.fy * factor
        
        combined_loads = list(load_map.values())
        
        # Solve for this combination
        combo_results = solve(model, combined_loads, material_name)
        results[combo.name] = combo_results
    
    return results


def get_envelope_results(
    combination_results: dict[str, AnalysisResults]
) -> AnalysisResults:
    """
    Get envelope (maximum) results from multiple load combinations.
    
    Args:
        combination_results: Dictionary of combination name to results
        
    Returns:
        Envelope analysis results with maximum values
    """
    if not combination_results:
        raise ValueError("No combination results provided")
    
    # Get first result as template
    first_result = next(iter(combination_results.values()))
    
    # Initialize envelope with first result
    envelope_member_forces = []
    member_ids = [mf.member_id for mf in first_result.member_forces]
    
    for member_id in member_ids:
        max_axial = 0.0
        max_shear = 0.0
        max_moment = 0.0
        max_stress = 0.0
        max_stress_ratio = 0.0
        
        # Find maximum values across all combinations
        for combo_name, results in combination_results.items():
            for mf in results.member_forces:
                if mf.member_id == member_id:
                    max_axial = max(max_axial, abs(mf.axial))
                    max_shear = max(max_shear, abs(mf.shear))
                    max_moment = max(max_moment, abs(mf.moment))
                    max_stress = max(max_stress, abs(mf.stress))
                    max_stress_ratio = max(max_stress_ratio, mf.stress_ratio)
        
        envelope_member_forces.append(MemberForce(
            member_id=member_id,
            axial=max_axial,
            shear=max_shear,
            moment=max_moment,
            stress=max_stress,
            stress_ratio=max_stress_ratio
        ))
    
    # Get maximum deflection across all combinations
    max_deflection = max(r.max_deflection for r in combination_results.values())
    
    # Get maximum stress ratio
    overall_max_stress_ratio = max(r.max_stress_ratio for r in combination_results.values())
    
    # Determine safety status from envelope
    if overall_max_stress_ratio >= 1.0:
        safety_status = "FAIL"
    elif overall_max_stress_ratio >= 0.8:
        safety_status = "WARNING"
    else:
        safety_status = "PASS"
    
    # Use reactions and displacements from worst case (highest stress ratio)
    worst_case = max(combination_results.values(), key=lambda r: r.max_stress_ratio)
    
    return AnalysisResults(
        member_forces=envelope_member_forces,
        reactions=worst_case.reactions,
        max_deflection=max_deflection,
        safety_status=safety_status,
        max_stress_ratio=overall_max_stress_ratio,
        nodes_with_displacements=worst_case.nodes_with_displacements
    )
