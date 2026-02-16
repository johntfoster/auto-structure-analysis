"""Pydantic models for API schemas and internal data structures."""

from typing import Literal
from pydantic import BaseModel, Field


class Node(BaseModel):
    """A node in the structural model."""
    id: str
    x: float  # mm
    y: float  # mm


class Member(BaseModel):
    """A structural member connecting two nodes."""
    id: str
    start_node: str
    end_node: str
    material: str = "steel"


class Support(BaseModel):
    """A support constraint at a node."""
    node_id: str
    type: Literal["pin", "roller", "fixed"]


class StructuralModel(BaseModel):
    """Complete structural model definition."""
    nodes: list[Node]
    members: list[Member]
    supports: list[Support]


class Load(BaseModel):
    """Point load applied to a node."""
    node_id: str
    fx: float = 0.0  # N
    fy: float = 0.0  # N


class MemberForce(BaseModel):
    """Forces in a member."""
    member_id: str
    axial: float  # N (tension positive)
    shear: float  # N
    moment: float  # N·mm


class Reaction(BaseModel):
    """Reaction force at a support."""
    node_id: str
    rx: float  # N
    ry: float  # N


class AnalysisResults(BaseModel):
    """FEA analysis results."""
    member_forces: list[MemberForce]
    reactions: list[Reaction]
    max_deflection: float  # mm


class AnalysisRequest(BaseModel):
    """Request body for structure analysis."""
    scale_length_mm: float = Field(default=100.0, description="Physical length of ArUco marker in mm")


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint."""
    analysis_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    message: str


class AnalysisDetail(BaseModel):
    """Detailed analysis result."""
    analysis_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    model: StructuralModel | None = None
    results: AnalysisResults | None = None
    error: str | None = None


class AnalysisListResponse(BaseModel):
    """Paginated list of analyses."""
    analyses: list[AnalysisDetail]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
