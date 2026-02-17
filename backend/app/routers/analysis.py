"""Analysis endpoints for structural analysis."""

import io
import uuid
import math
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query, Depends, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import cv2
import numpy as np

from app.models.schemas import (
    AnalysisResponse,
    AnalysisDetail,
    AnalysisListResponse,
    Load,
    MaterialInfo,
    ReanalysisRequest,
)
from app.utils.image_processing import load_image, resize_for_detection
from app.utils.validation import validate_image_upload
from app.services.aruco_detector import detect_aruco
from app.services.structure_detector import detect_structure
from app.services.fea_solver import solve
from app.services.materials import get_material, list_materials
from app.services.model_server import get_model_server
from app.services.report_generator import generate_report
from app.exceptions import CalibrationError, DetectionError, AnalysisError
from app.database import get_database, Database
from app.middleware.auth import verify_api_key
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["analysis"])

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze", response_model=AnalysisResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute" if settings.rate_limit_enabled else "1000/minute")
async def analyze_structure(
    request: Request,
    file: UploadFile = File(...),
    scale_length_mm: Optional[float] = Form(default=None),
    material: str = Form(default="steel"),
    db: Database = Depends(get_database)
):
    """
    Analyze a structure from an uploaded image.
    
    Args:
        request: FastAPI request object (for rate limiting)
        file: Image file containing structure and ArUco marker
        scale_length_mm: Physical size of the ArUco marker in mm (optional if marker detected)
        material: Material to use for analysis (steel, aluminum, or wood)
        db: Database instance
        
    Returns:
        Analysis ID and status
    """
    # Validate file upload
    await validate_image_upload(file)
    
    # Validate material before starting analysis
    try:
        mat = get_material(material)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())
    
    try:
        
        # Load and preprocess image
        image = await load_image(file)
        image = resize_for_detection(image)
        
        # Step 1: Detect ArUco markers for scale calibration
        aruco_result = detect_aruco(image)
        
        if not aruco_result["marker_ids"] and scale_length_mm is None:
            # No marker found and no manual scale provided
            raise CalibrationError(
                "No ArUco marker detected in image. "
                "Please either include an ArUco marker in the photo or provide scale_length_mm manually."
            )
        
        # Compute scale factor
        if aruco_result["marker_ids"]:
            # Use detected marker for scale
            first_corner = aruco_result["marker_corners"][0][0]
            # Calculate side length in pixels
            p1 = first_corner[0]
            p2 = first_corner[1]
            side_length_px = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            marker_size = scale_length_mm if scale_length_mm else 100.0
            scale_factor = side_length_px / marker_size
        else:
            # Use manual scale (assume 1000mm = full image width as default)
            scale_factor = image.shape[1] / (scale_length_mm if scale_length_mm else 1000.0)
        
        # Step 2: Detect structure (YOLO → edge detection → mock fallback)
        model, detection_method = detect_structure(image, scale_factor)
        
        if not model.nodes or not model.members:
            raise DetectionError("No structure detected in image. Please ensure structure is clearly visible.")
        
        # Step 3: Apply material properties and calculate self-weight loads
        # For now, use simplified loading (can be extended to self-weight)
        # Apply downward loads at top chord nodes
        loads = []
        for node in model.nodes:
            if node.id.startswith("T"):  # Top chord nodes
                loads.append(Load(node_id=node.id, fx=0.0, fy=-10000.0))  # 10kN downward
        
        # Ensure we have at least one load
        if not loads:
            loads = [Load(node_id=model.nodes[0].id, fx=0.0, fy=-10000.0)]
        
        # Step 4: Run FEA solver
        results = solve(model, loads, material_name=material)
        
        # Step 5: Store results
        analysis_detail = AnalysisDetail(
            analysis_id=analysis_id,
            status="completed",
            model=model,
            results=results,
            material=material,
            loads=loads,
            scale_factor=scale_factor,
            detection_method=detection_method,
            error=None
        )
        db.save_analysis(analysis_detail)
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            message=f"Analysis completed successfully using {detection_method} detection. Safety: {results.safety_status}"
        )
        
    except (CalibrationError, DetectionError, AnalysisError) as e:
        # Store error result
        analysis_detail = AnalysisDetail(
            analysis_id=analysis_id,
            status="failed",
            model=None,
            results=None,
            material=material,
            loads=[],
            scale_factor=0.0,
            detection_method="none",
            error=str(e)
        )
        db.save_analysis(analysis_detail)
        
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Store unexpected error
        analysis_detail = AnalysisDetail(
            analysis_id=analysis_id,
            status="failed",
            model=None,
            results=None,
            material=material,
            loads=[],
            scale_factor=0.0,
            detection_method="none",
            error=str(e)
        )
        db.save_analysis(analysis_detail)
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analysis/{analysis_id}", response_model=AnalysisDetail, dependencies=[Depends(verify_api_key)])
async def get_analysis(analysis_id: str, db: Database = Depends(get_database)):
    """
    Get analysis results by ID.
    
    Args:
        analysis_id: Unique analysis identifier
        db: Database instance
        
    Returns:
        Analysis details including model and results
    """
    analysis = db.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis


@router.get("/analyses", response_model=AnalysisListResponse, dependencies=[Depends(verify_api_key)])
async def list_analyses(
    page: int = 1,
    page_size: int = 10,
    db: Database = Depends(get_database)
):
    """
    List all analyses with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database instance
        
    Returns:
        Paginated list of analyses
    """
    # Calculate skip offset
    skip = (page - 1) * page_size
    
    # Get analyses from database
    analyses, total = db.list_analyses(skip=skip, limit=page_size)
    
    return AnalysisListResponse(
        analyses=analyses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/materials", response_model=list[MaterialInfo])
async def get_materials():
    """
    Get list of available materials.
    
    Returns:
        List of material properties
    """
    materials = list_materials()
    return [
        MaterialInfo(
            name=m.name,
            E=m.E,
            fy=m.fy,
            density=m.density,
            description=m.description
        )
        for m in materials
    ]


@router.post("/analysis/{analysis_id}/reanalyze", response_model=AnalysisDetail, dependencies=[Depends(verify_api_key)])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute" if settings.rate_limit_enabled else "1000/minute")
async def reanalyze_structure(
    request: Request,
    analysis_id: str,
    reanalysis_request: ReanalysisRequest,
    db: Database = Depends(get_database)
):
    """
    Re-run analysis with modified parameters.
    
    Args:
        request: FastAPI request object (for rate limiting)
        analysis_id: ID of existing analysis
        reanalysis_request: Reanalysis parameters (material and/or loads)
        db: Database instance
        
    Returns:
        Updated analysis results
    """
    # Check if analysis exists
    original = db.get_analysis(analysis_id)
    if not original:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Can't reanalyze a failed analysis without a model
    if original.status == "failed" or original.model is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot reanalyze a failed analysis. Please run a new analysis."
        )
    
    try:
        # Use new material or keep original
        material = reanalysis_request.material if reanalysis_request.material else original.material
        
        # Validate material
        try:
            get_material(material)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Use new loads or keep original
        loads = reanalysis_request.loads if reanalysis_request.loads is not None else original.loads
        
        # Re-run FEA with updated parameters
        results = solve(original.model, loads, material_name=material)
        
        # Update stored analysis
        updated_analysis = AnalysisDetail(
            analysis_id=analysis_id,
            status="completed",
            model=original.model,
            results=results,
            material=material,
            loads=loads,
            scale_factor=original.scale_factor,
            detection_method=original.detection_method,
            error=None
        )
        db.save_analysis(updated_analysis)
        
        return updated_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reanalysis failed: {str(e)}")


@router.get("/marker")
async def generate_marker(
    id: int = Query(default=0, description="ArUco marker ID (0-49)"),
    size: int = Query(default=200, description="Marker size in pixels")
):
    """
    Generate ArUco marker image.
    
    Args:
        id: Marker ID from DICT_4X4_50 (0-49)
        size: Size of marker in pixels
        
    Returns:
        PNG image of the ArUco marker
    """
    if id < 0 or id > 49:
        raise HTTPException(status_code=400, detail="Marker ID must be between 0 and 49")
    
    if size < 50 or size > 1000:
        raise HTTPException(status_code=400, detail="Size must be between 50 and 1000 pixels")
    
    # Generate ArUco marker
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, id, size)
    
    # Convert to PNG
    success, buffer = cv2.imencode('.png', marker_img)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode marker image")
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(buffer.tobytes()),
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename=aruco_marker_{id}.png"
        }
    )


@router.get("/model/status")
async def get_model_status():
    """
    Get YOLO model status and information.
    
    Returns:
        Model info including loaded status, path, class names, and input size
    """
    model_server = get_model_server()
    return model_server.get_model_info()


@router.get("/analysis/{analysis_id}/report", dependencies=[Depends(verify_api_key)])
async def download_report(analysis_id: str, db: Database = Depends(get_database)):
    """
    Generate and download a PDF report for an analysis.
    
    Args:
        analysis_id: ID of the analysis
        db: Database instance
        
    Returns:
        PDF file as streaming response
    """
    # Check if analysis exists
    analysis = db.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Can't generate report for failed analysis
    if analysis.status == "failed" or analysis.model is None or analysis.results is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate report for failed analysis"
        )
    
    try:
        # Generate PDF report
        pdf_bytes = generate_report(
            model=analysis.model,
            results=analysis.results,
            loads=analysis.loads,
            material=analysis.material,
            analysis_id=analysis_id
        )
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_report_{analysis_id[:8]}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
