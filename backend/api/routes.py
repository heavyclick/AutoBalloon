"""
API Routes
FastAPI endpoints for AutoBalloon - Core processing functionality
"""
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
import io

from models import (
    ProcessResponse,
    ProcessingMetadata,
    GridInfo,
    Dimension,
    BoundingBox,
    ErrorCode,
    ErrorResponse,
    ExportRequest,
    ExportFormat,
    ExportTemplate,
    ExportMetadata,
    UpdateBalloonRequest,
    UpdateBalloonResponse,
    AddBalloonRequest,
    AddBalloonResponse,
    HealthResponse,
)
from services import (
    file_service,
    FileServiceError,
    create_detection_service,
    create_vision_service,
    create_grid_service,
    export_service,
    usage_service,
    history_service,
    auth_service,
    User,
)
from config import GOOGLE_CLOUD_API_KEY, GEMINI_API_KEY

router = APIRouter(prefix="/api")


# ==================
# Dependencies
# ==================

async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return auth_service.get_current_user(parts[1])


def get_detection_service():
    """Get detection service with API keys from config"""
    return create_detection_service(
        ocr_api_key=GOOGLE_CLOUD_API_KEY or None,
        gemini_api_key=GEMINI_API_KEY or None
    )


def get_grid_service():
    """Get grid service with Gemini vision"""
    vision_service = None
    if GEMINI_API_KEY:
        vision_service = create_vision_service(GEMINI_API_KEY)
    return create_grid_service(vision_service)


# ==================
# Endpoints
# ==================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@router.post("/process", response_model=ProcessResponse)
async def process_file(
    file: UploadFile = File(...),
    visitor_id: Optional[str] = None,
    detection_service=Depends(get_detection_service),
    grid_service=Depends(get_grid_service),
    user: Optional[User] = Depends(get_optional_user)
):
    """
    Process a manufacturing blueprint and detect dimensions.
    
    Accepts: PDF, PNG, JPEG, TIFF (max 25MB)
    Returns: Base64 image, detected dimensions with zones, grid info
    
    Usage limits:
    - Free users: 3 drawings/month
    - Pro users: Unlimited
    """
    start_time = time.time()
    
    # Check usage limits (before processing)
    if user:
        can_process = usage_service.can_process(user_id=user.id, is_pro=user.is_pro)
    elif visitor_id:
        can_process = usage_service.can_process(visitor_id=visitor_id)
    else:
        # No tracking info - allow but log warning
        can_process = True
    
    if not can_process:
        return ProcessResponse(
            success=False,
            error={
                "code": "USAGE_LIMIT_EXCEEDED",
                "message": "You've reached your free limit. Upgrade to Pro for unlimited processing."
            }
        )
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.INVALID_FILE.value, "message": str(e)}
        )
    
    # Process file to normalized PNG
    try:
        png_bytes, original_format, width, height = file_service.process_file(
            content, 
            file.filename or "upload.pdf"
        )
    except FileServiceError as e:
        return ProcessResponse(
            success=False,
            error={"code": e.code.value, "message": e.message}
        )
    
    # Detect grid
    grid_info = await grid_service.detect_grid(png_bytes)
    
    # Detect dimensions
    try:
        dimensions = await detection_service.detect_dimensions(
            png_bytes, width, height
        )
    except Exception as e:
        # Return partial result with image but no dimensions
        return ProcessResponse(
            success=True,
            image=file_service.to_base64(png_bytes),
            dimensions=[],
            grid=grid_info,
            metadata=ProcessingMetadata(
                filename=file.filename or "upload",
                original_format=original_format,
                processed_at=datetime.utcnow(),
                dimension_count=0,
                processing_time_ms=int((time.time() - start_time) * 1000)
            ),
            error={"code": ErrorCode.PROCESSING_ERROR.value, "message": str(e)}
        )
    
    # Assign zones to dimensions
    if grid_info.detected:
        grid_service.assign_zones_to_dimensions(dimensions)
    
    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Increment usage count (after successful processing)
    if user:
        usage_service.increment_user_usage(user.id, user.is_pro)
    elif visitor_id:
        usage_service.increment_anonymous_usage(visitor_id)
    
    # Save to history for Pro users
    if user and user.is_pro and history_service.get_history_enabled(user.id):
        thumbnail = file_service.create_thumbnail(png_bytes)
        history_service.add_entry(
            user_id=user.id,
            filename=file.filename or "upload",
            thumbnail=thumbnail,
            dimensions=[d.model_dump() for d in dimensions],
            image_data=file_service.to_base64(png_bytes),
            grid=grid_info.model_dump() if grid_info else None,
            processing_time_ms=processing_time_ms
        )
    
    return ProcessResponse(
        success=True,
        image=file_service.to_base64(png_bytes),
        dimensions=dimensions,
        grid=grid_info,
        metadata=ProcessingMetadata(
            filename=file.filename or "upload",
            original_format=original_format,
            processed_at=datetime.utcnow(),
            dimension_count=len(dimensions),
            processing_time_ms=processing_time_ms
        )
    )


@router.post("/export")
async def export_inspection(request: ExportRequest):
    """
    Export inspection data to CSV or Excel.
    
    Supports AS9102 Form 3 format for aerospace compliance.
    """
    try:
        # Convert metadata if provided
        metadata = None
        if request.metadata:
            metadata = ExportMetadata(
                part_number=request.metadata.part_number,
                part_name=request.metadata.part_name,
                revision=request.metadata.revision
            )
        
        # Generate export
        file_bytes, content_type, filename = export_service.generate_export(
            dimensions=request.dimensions,
            format=request.format,
            template=request.template,
            metadata=metadata,
            filename=request.filename
        )
        
        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "EXPORT_ERROR", "message": str(e)}
        )


@router.post("/update-balloon", response_model=UpdateBalloonResponse)
async def update_balloon(
    request: UpdateBalloonRequest,
    grid_service=Depends(get_grid_service)
):
    """
    Update a balloon's position after user drag.
    Recalculates zone based on new position.
    """
    try:
        new_zone = grid_service.recalculate_zone(request.new_bounding_box)
        
        return UpdateBalloonResponse(
            success=True,
            updated_zone=new_zone
        )
    except Exception as e:
        return UpdateBalloonResponse(
            success=False,
            updated_zone=None
        )


@router.post("/add-balloon", response_model=AddBalloonResponse)
async def add_balloon(
    request: AddBalloonRequest,
    grid_service=Depends(get_grid_service)
):
    """
    Manually add a new balloon at a user-specified position.
    """
    try:
        # Calculate zone for the new position
        zone = grid_service.assign_zone(request.bounding_box)
        
        # Create new dimension (ID will be assigned by frontend)
        new_dimension = Dimension(
            id=0,  # Frontend assigns the actual ID
            value=request.value,
            zone=zone,
            bounding_box=request.bounding_box,
            confidence=1.0,  # User-added = full confidence
            manually_added=True
        )
        
        return AddBalloonResponse(
            success=True,
            dimension=new_dimension
        )
    except Exception as e:
        return AddBalloonResponse(
            success=False,
            dimension=None
        )
