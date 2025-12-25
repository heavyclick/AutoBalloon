"""
API Routes - Multi-Page Support
Handles file upload, multi-page processing, and export generation.
"""
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from services.detection_service import DetectionService, create_detection_service
from services.export_service import ExportService, export_service
from services.file_service import FileService, file_service
from models import ExportFormat, ExportTemplate, ExportMetadata


router = APIRouter()


# ==================
# Request/Response Models
# ==================

class DimensionResponse(BaseModel):
    """Single dimension in API response"""
    id: int
    value: str
    zone: Optional[str]
    page: int = 1
    bounding_box: dict
    confidence: float


class PageResponse(BaseModel):
    """Single page in API response"""
    page_number: int
    image: str  # base64 encoded PNG
    width: int
    height: int
    dimensions: List[DimensionResponse]
    grid_detected: bool


class ProcessingResponse(BaseModel):
    """Full processing response"""
    success: bool
    total_pages: int
    pages: List[PageResponse]
    all_dimensions: List[DimensionResponse]
    message: Optional[str] = None


class ExportRequest(BaseModel):
    """Export request body"""
    dimensions: List[dict]  # Dimension data from frontend
    format: str = "xlsx"  # "csv" or "xlsx"
    template: str = "AS9102_FORM3"  # "SIMPLE" or "AS9102_FORM3"
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    revision: Optional[str] = None
    total_pages: int = 1
    grid_detected: bool = True


# ==================
# Dependency Injection
# ==================

def get_detection_service() -> DetectionService:
    """Get configured detection service"""
    import os
    return create_detection_service(
        ocr_api_key=os.getenv("GOOGLE_CLOUD_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )


# ==================
# API Endpoints
# ==================

@router.post("/process", response_model=ProcessingResponse)
async def process_drawing(
    file: UploadFile = File(...),
    detection_service: DetectionService = None
):
    """
    Process uploaded engineering drawing (PDF or image).
    
    Supports:
    - Multi-page PDF (up to 20 pages)
    - Single images (PNG, JPEG)
    
    Returns:
    - All pages with base64 images
    - Dimensions with sequential balloon numbers across all pages
    - Grid detection status per page
    """
    if detection_service is None:
        detection_service = get_detection_service()
    
    # Read file bytes
    file_bytes = await file.read()
    
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # Process file (handles both PDF and images)
    result = await detection_service.detect_dimensions_multipage(
        file_bytes=file_bytes,
        filename=file.filename
    )
    
    if not result.success:
        raise HTTPException(
            status_code=422, 
            detail=result.error_message or "Failed to process file"
        )
    
    # Convert to response format
    pages = []
    for page_result in result.pages:
        page_dimensions = [
            DimensionResponse(
                id=dim.id,
                value=dim.value,
                zone=dim.zone,
                page=dim.page,
                bounding_box={
                    "xmin": dim.bounding_box.xmin,
                    "ymin": dim.bounding_box.ymin,
                    "xmax": dim.bounding_box.xmax,
                    "ymax": dim.bounding_box.ymax,
                    "center_x": dim.bounding_box.center_x,
                    "center_y": dim.bounding_box.center_y
                },
                confidence=dim.confidence
            )
            for dim in page_result.dimensions
        ]
        
        pages.append(PageResponse(
            page_number=page_result.page_number,
            image=page_result.image_base64,
            width=page_result.width,
            height=page_result.height,
            dimensions=page_dimensions,
            grid_detected=page_result.grid_detected
        ))
    
    # Flatten all dimensions for response
    all_dimensions = [
        DimensionResponse(
            id=dim.id,
            value=dim.value,
            zone=dim.zone,
            page=dim.page,
            bounding_box={
                "xmin": dim.bounding_box.xmin,
                "ymin": dim.bounding_box.ymin,
                "xmax": dim.bounding_box.xmax,
                "ymax": dim.bounding_box.ymax,
                "center_x": dim.bounding_box.center_x,
                "center_y": dim.bounding_box.center_y
            },
            confidence=dim.confidence
        )
        for dim in result.all_dimensions
    ]
    
    return ProcessingResponse(
        success=True,
        total_pages=result.total_pages,
        pages=pages,
        all_dimensions=all_dimensions,
        message=result.error_message  # e.g., "Processed 20 of 25 pages"
    )


@router.post("/export")
async def export_inspection_data(request: ExportRequest):
    """
    Export dimension data to CSV or AS9102 Excel.
    
    Supports:
    - CSV format (simple)
    - Excel with AS9102 Form 3 template
    - Multi-page drawings with Sheet column
    """
    # Parse format and template
    export_format = ExportFormat.CSV if request.format.lower() == "csv" else ExportFormat.XLSX
    export_template = (
        ExportTemplate.SIMPLE 
        if request.template.upper() == "SIMPLE" 
        else ExportTemplate.AS9102_FORM3
    )
    
    # Build metadata
    metadata = None
    if request.part_number or request.part_name or request.revision:
        metadata = ExportMetadata(
            part_number=request.part_number,
            part_name=request.part_name,
            revision=request.revision
        )
    
    # Generate export
    file_bytes, content_type, filename = export_service.generate_export(
        dimensions=request.dimensions,
        format=export_format,
        template=export_template,
        metadata=metadata,
        filename="inspection",
        grid_detected=request.grid_detected,
        total_pages=request.total_pages
    )
    
    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "autoballoon-api"}
