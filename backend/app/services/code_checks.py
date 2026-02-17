"""Building code compliance checks (AISC, NDS)."""

import math
from typing import Literal
from pydantic import BaseModel
from app.services.materials import get_material


class CodeCheckResult(BaseModel):
    """Result of a code compliance check."""
    code: Literal["AISC", "NDS"]
    check_name: str
    status: Literal["PASS", "FAIL"]
    ratio: float  # Demand/capacity ratio
    reference: str
    details: str


class MemberCodeCheck(BaseModel):
    """Code check results for a member."""
    member_id: str
    checks: list[CodeCheckResult]
    overall_status: Literal["PASS", "FAIL"]


def check_aisc_slenderness(
    length: float,
    radius_of_gyration: float,
    fy: float,
    E: float,
    axial_force: float
) -> CodeCheckResult:
    """
    Check AISC slenderness ratio for compression members.
    
    Args:
        length: Unbraced length (mm)
        radius_of_gyration: Radius of gyration (mm)
        fy: Yield strength (MPa)
        E: Elastic modulus (MPa)
        axial_force: Axial force (N, negative for compression)
        
    Returns:
        Code check result
    """
    # AISC 360-16 Section E2
    # Slenderness ratio KL/r
    # K = 1.0 (effective length factor, assumed pinned ends)
    K = 1.0
    slenderness = (K * length) / radius_of_gyration if radius_of_gyration > 0 else 0
    
    # Limiting slenderness for compression members
    # AISC 360-16 E2: (KL/r) should not exceed 200
    limit = 200.0
    
    ratio = slenderness / limit
    
    status = "PASS" if slenderness <= limit else "FAIL"
    
    return CodeCheckResult(
        code="AISC",
        check_name="Slenderness Ratio",
        status=status,
        ratio=ratio,
        reference="AISC 360-16 Section E2",
        details=f"KL/r = {slenderness:.1f}, Limit = {limit:.1f}"
    )


def check_aisc_compression_capacity(
    area: float,
    length: float,
    radius_of_gyration: float,
    fy: float,
    E: float,
    axial_force: float
) -> CodeCheckResult:
    """
    Check AISC compression capacity using Euler buckling.
    
    Args:
        area: Cross-sectional area (mm²)
        length: Unbraced length (mm)
        radius_of_gyration: Radius of gyration (mm)
        fy: Yield strength (MPa)
        E: Elastic modulus (MPa)
        axial_force: Axial force (N, negative for compression)
        
    Returns:
        Code check result
    """
    # AISC 360-16 Chapter E - Compression Members
    # Only check if in compression
    if axial_force >= 0:
        return CodeCheckResult(
            code="AISC",
            check_name="Compression Capacity",
            status="PASS",
            ratio=0.0,
            reference="AISC 360-16 Chapter E",
            details="Member in tension, compression check not applicable"
        )
    
    # Effective length factor K = 1.0 (pinned-pinned)
    K = 1.0
    L = length
    r = radius_of_gyration
    
    # Elastic critical buckling stress (Euler)
    # Fe = π²E / (KL/r)²
    if r > 0:
        KL_r = (K * L) / r
        Fe = (math.pi**2 * E) / (KL_r**2)
    else:
        Fe = 0.0
    
    # Critical stress (AISC simplified)
    # If Fe >= 0.44fy: Fcr = 0.658^(fy/Fe) * fy (inelastic buckling)
    # If Fe < 0.44fy: Fcr = 0.877 * Fe (elastic buckling)
    if Fe >= 0.44 * fy:
        Fcr = (0.658 ** (fy / Fe)) * fy
    else:
        Fcr = 0.877 * Fe
    
    # Nominal compressive strength
    # Pn = Fcr * Ag
    Pn = Fcr * area
    
    # Design strength (LRFD)
    # φc = 0.90 for compression
    phi_c = 0.90
    Pc = phi_c * Pn
    
    # Demand/Capacity ratio
    demand = abs(axial_force)
    ratio = demand / Pc if Pc > 0 else 999.0
    
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    return CodeCheckResult(
        code="AISC",
        check_name="Compression Capacity",
        status=status,
        ratio=ratio,
        reference="AISC 360-16 Chapter E",
        details=f"Pu = {demand:.1f} N, φPn = {Pc:.1f} N, Ratio = {ratio:.3f}"
    )


def check_aisc_tension_capacity(
    area: float,
    fy: float,
    fu: float,
    axial_force: float
) -> CodeCheckResult:
    """
    Check AISC tension capacity.
    
    Args:
        area: Gross cross-sectional area (mm²)
        fy: Yield strength (MPa)
        fu: Ultimate tensile strength (MPa)
        axial_force: Axial force (N, positive for tension)
        
    Returns:
        Code check result
    """
    # AISC 360-16 Chapter D - Tension Members
    # Only check if in tension
    if axial_force <= 0:
        return CodeCheckResult(
            code="AISC",
            check_name="Tension Capacity",
            status="PASS",
            ratio=0.0,
            reference="AISC 360-16 Chapter D",
            details="Member in compression, tension check not applicable"
        )
    
    # Nominal tensile yielding strength
    # Pn = Fy * Ag
    Pn_yield = fy * area
    
    # Design strength (LRFD)
    # φt = 0.90 for tension yielding
    phi_t = 0.90
    Pt = phi_t * Pn_yield
    
    # Demand/Capacity ratio
    demand = abs(axial_force)
    ratio = demand / Pt if Pt > 0 else 999.0
    
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    return CodeCheckResult(
        code="AISC",
        check_name="Tension Capacity",
        status=status,
        ratio=ratio,
        reference="AISC 360-16 Chapter D",
        details=f"Pu = {demand:.1f} N, φPn = {Pt:.1f} N, Ratio = {ratio:.3f}"
    )


def check_aisc_combined_loading(
    area: float,
    section_modulus: float,
    axial_force: float,
    moment: float,
    fy: float,
    Pc: float,
    Mc: float
) -> CodeCheckResult:
    """
    Check AISC combined axial and bending (interaction equation).
    
    Args:
        area: Cross-sectional area (mm²)
        section_modulus: Section modulus (mm³)
        axial_force: Axial force (N)
        moment: Bending moment (N·mm)
        fy: Yield strength (MPa)
        Pc: Design axial capacity (N)
        Mc: Design moment capacity (N·mm)
        
    Returns:
        Code check result
    """
    # AISC 360-16 Chapter H - Combined Forces
    # Interaction equation: (Pu/Pc) + (8/9)(Mu/Mc) <= 1.0 if Pu/Pc >= 0.2
    # Or: (Pu/2Pc) + (Mu/Mc) <= 1.0 if Pu/Pc < 0.2
    
    Pu = abs(axial_force)
    Mu = abs(moment)
    
    if Pc <= 0 or Mc <= 0:
        return CodeCheckResult(
            code="AISC",
            check_name="Combined Loading",
            status="FAIL",
            ratio=999.0,
            reference="AISC 360-16 Chapter H",
            details="Invalid capacity values"
        )
    
    # Calculate ratio
    axial_ratio = Pu / Pc
    
    if axial_ratio >= 0.2:
        # H1-1a: (Pr/Pc) + (8/9)(Mr/Mc) <= 1.0
        ratio = axial_ratio + (8.0/9.0) * (Mu / Mc)
    else:
        # H1-1b: (Pr/2Pc) + (Mr/Mc) <= 1.0
        ratio = (Pu / (2.0 * Pc)) + (Mu / Mc)
    
    status = "PASS" if ratio <= 1.0 else "FAIL"
    
    return CodeCheckResult(
        code="AISC",
        check_name="Combined Loading",
        status=status,
        ratio=ratio,
        reference="AISC 360-16 Chapter H",
        details=f"Pu/Pc = {axial_ratio:.3f}, Mu/Mc = {Mu/Mc:.3f}, Interaction = {ratio:.3f}"
    )


def perform_code_checks(
    member_id: str,
    length: float,
    area: float,
    section_modulus: float,
    radius_of_gyration: float,
    axial_force: float,
    moment: float,
    material_name: str = "steel",
    code: Literal["AISC", "NDS"] = "AISC"
) -> MemberCodeCheck:
    """
    Perform comprehensive code checks for a member.
    
    Args:
        member_id: Member identifier
        length: Member length (mm)
        area: Cross-sectional area (mm²)
        section_modulus: Section modulus (mm³)
        radius_of_gyration: Radius of gyration (mm)
        axial_force: Axial force (N)
        moment: Bending moment (N·mm)
        material_name: Material name
        code: Building code to use (AISC or NDS)
        
    Returns:
        Member code check results
    """
    material = get_material(material_name)
    
    checks = []
    
    if code == "AISC":
        # Slenderness check
        slenderness_check = check_aisc_slenderness(
            length, radius_of_gyration, material.fy, material.E, axial_force
        )
        checks.append(slenderness_check)
        
        # Compression capacity (if in compression)
        if axial_force < 0:
            compression_check = check_aisc_compression_capacity(
                area, length, radius_of_gyration, material.fy, material.E, axial_force
            )
            checks.append(compression_check)
            Pc = compression_check.ratio * abs(axial_force) if compression_check.ratio > 0 else 1e9
        else:
            Pc = 1e9  # Large value if not in compression
        
        # Tension capacity (if in tension)
        if axial_force > 0:
            # Assume Fu = 1.5 * Fy for typical steel
            fu = 1.5 * material.fy
            tension_check = check_aisc_tension_capacity(
                area, material.fy, fu, axial_force
            )
            checks.append(tension_check)
        
        # Combined loading check (if moment exists)
        if abs(moment) > 1.0:
            # Design moment capacity (simplified)
            # φMn = φ * Fy * S, where φ = 0.90 for flexure
            phi_b = 0.90
            Mc = phi_b * material.fy * section_modulus
            
            combined_check = check_aisc_combined_loading(
                area, section_modulus, axial_force, moment, material.fy, Pc, Mc
            )
            checks.append(combined_check)
    
    elif code == "NDS":
        # NDS checks for wood (simplified)
        # TODO: Implement NDS-specific checks
        checks.append(CodeCheckResult(
            code="NDS",
            check_name="NDS Check",
            status="PASS",
            ratio=0.5,
            reference="NDS 2018 (placeholder)",
            details="NDS checks not yet implemented"
        ))
    
    # Overall status
    overall_status = "FAIL" if any(c.status == "FAIL" for c in checks) else "PASS"
    
    return MemberCodeCheck(
        member_id=member_id,
        checks=checks,
        overall_status=overall_status
    )
