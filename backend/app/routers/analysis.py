"""Analysis endpoints for structural analysis."""

import io
import uuid
import math
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
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
from app.services.aruco_detector import detect_aruco
from app.services.structure_detector import detect_structure
from app.services.fea_solver import solve
from app.services.materials import get_material, list_materials
from app.services.model_server import get_model_server
from app.exceptions import CalibrationError, DetectionError, AnalysisError

router = APIRouter(prefix="/api/v1", tags=["analysis"])

# In-memory storage for analyses (would be database in production)
analyses_db: dict[str, AnalysisDetail] = {}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_structure(
    file: UploadFile = File(...),
    scale_length_mm: Optional[float] = Form(default=None),
    material: str = Form(default="steel")
):
    """
    Analyze a structure from an uploaded image.
    
    Args:
        file: Image file containing structure and ArUco marker
        scale_length_mm: Physical size of the ArUco marker in mm (optional if marker detected)
        material: Material to use for analysis (steel, aluminum, or wood)
        
    Returns:
        Analysis ID and status
    """
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
        analyses_db[analysis_id] = AnalysisDetail(
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
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            message=f"Analysis completed successfully using {detection_method} detection. Safety: {results.safety_status}"
        )
        
    except (CalibrationError, DetectionError, AnalysisError) as e:
        # Store error result
        analyses_db[analysis_id] = AnalysisDetail(
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
        
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Store unexpected error
        analyses_db[analysis_id] = AnalysisDetail(
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
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


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


@router.post("/analysis/{analysis_id}/reanalyze", response_model=AnalysisDetail)
async def reanalyze_structure(analysis_id: str, request: ReanalysisRequest):
    """
    Re-run analysis with modified parameters.
    
    Args:
        analysis_id: ID of existing analysis
        request: Reanalysis parameters (material and/or loads)
        
    Returns:
        Updated analysis results
    """
    # Check if analysis exists
    if analysis_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    original = analyses_db[analysis_id]
    
    # Can't reanalyze a failed analysis without a model
    if original.status == "failed" or original.model is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot reanalyze a failed analysis. Please run a new analysis."
        )
    
    try:
        # Use new material or keep original
        material = request.material if request.material else original.material
        
        # Validate material
        try:
            get_material(material)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Use new loads or keep original
        loads = request.loads if request.loads is not None else original.loads
        
        # Re-run FEA with updated parameters
        results = solve(original.model, loads, material_name=material)
        
        # Update stored analysis
        analyses_db[analysis_id] = AnalysisDetail(
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
        
        return analyses_db[analysis_id]
        
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
