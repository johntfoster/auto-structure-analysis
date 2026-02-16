"""Health check endpoints."""

from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns basic service status and version.
    """
    return HealthResponse(
        status="ok",
        version="0.1.0"
    )
