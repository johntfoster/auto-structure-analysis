"""Analysis endpoints for structural analysis."""

import uuid
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from app.models.schemas import (
    AnalysisResponse,
    AnalysisDetail,
    AnalysisListResponse,
    Load,
)
from app.utils.image_processing import load_image, resize_for_detection
from app.services.aruco_detector import detect_aruco
from app.services.structure_detector import detect_structure
from app.services.fea_solver import solve

router = APIRouter(prefix="/api/v1", tags=["analysis"])

# In-memory storage for analyses (would be database in production)
analyses_db: dict[str, AnalysisDetail] = {}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_structure(
    file: UploadFile = File(...),
    scale_length_mm: float = Form(default=100.0)
):
    """
    Analyze a structure from an uploaded image.
    
    Args:
        file: Image file containing structure and ArUco marker
        scale_length_mm: Physical size of the ArUco marker in mm
        
    Returns:
        Analysis ID and status
    """
    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())
    
    try:
        # Load and preprocess image
        image = await load_image(file)
        image = resize_for_detection(image)
        
        # Detect ArUco markers for scale
        aruco_result = detect_aruco(image)
        
        if not aruco_result["marker_ids"]:
            # No marker found - continue with default scale
            scale_factor = 1.0  # 1 pixel = 1 mm (placeholder)
        else:
            # Compute actual scale factor
            first_corner = aruco_result["marker_corners"][0][0]
            # Calculate side length in pixels
            p1 = first_corner[0]
            p2 = first_corner[1]
            side_length_px = ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5
            scale_factor = side_length_px / scale_length_mm
        
        # Detect structure (currently returns mock model)
        model = detect_structure(image, scale_factor)
        
        # Apply default loads (will be parameterized later)
        # For now, apply a downward load at the center top node
        loads = [
            Load(node_id="T1", fx=0.0, fy=-10000.0),  # 10kN downward
            Load(node_id="T2", fx=0.0, fy=-10000.0),  # 10kN downward
        ]
        
        # Solve FEA
        results = solve(model, loads)
        
        # Store analysis results
        analyses_db[analysis_id] = AnalysisDetail(
            analysis_id=analysis_id,
            status="completed",
            model=model,
            results=results,
            error=None
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            message="Analysis completed successfully"
        )
        
    except Exception as e:
        # Store error result
        analyses_db[analysis_id] = AnalysisDetail(
            analysis_id=analysis_id,
            status="failed",
            model=None,
            results=None,
            error=str(e)
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="failed",
            message=f"Analysis failed: {str(e)}"
        )


@router.get("/analysis/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(analysis_id: str):
    """
    Get analysis results by ID.
    
    Args:
        analysis_id: Unique analysis identifier
        
    Returns:
        Analysis details including model and results
    """
    if analysis_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analyses_db[analysis_id]


@router.get("/analyses", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = 1,
    page_size: int = 10
):
    """
    List all analyses with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Paginated list of analyses
    """
    all_analyses = list(analyses_db.values())
    total = len(all_analyses)
    
    # Calculate pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_analyses = all_analyses[start_idx:end_idx]
    
    return AnalysisListResponse(
        analyses=paginated_analyses,
        total=total,
        page=page,
        page_size=page_size
    )
