"""
Download Routes - Multi-Page Ballooned Output
API endpoints for generating downloadable files with balloons.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io


router = APIRouter(prefix="/download", tags=["Downloads"])


# ==================
# Request Models
# ==================

class PageData(BaseModel):
    """Page data for download generation"""
    page_number: int
    image: str  # base64 encoded PNG
    width: int = 1700
    height: int = 2200
    dimensions: List[dict] = []
    grid_detected: bool = True


class BOMItem(BaseModel):
    """Bill of Materials item"""
    part_name: str = ""
    part_number: str = ""
    qty: str = "1"


class SpecItem(BaseModel):
    """Specification item"""
    process: str = ""
    spec_number: str = ""
    code: Optional[str] = None


class DownloadRequest(BaseModel):
    """Request for download generation"""
    pages: List[PageData]
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    revision: Optional[str] = None
    serial_number: Optional[str] = None
    fai_report_number: Optional[str] = None
    grid_detected: bool = True
    template_name: Optional[str] = None  # AS9102, PPAP, ISO13485, or custom template ID
    visitor_id: Optional[str] = None
    bom: List[BOMItem] = []
    specifications: List[SpecItem] = []


class SingleImageDownloadRequest(BaseModel):
    """Request for single image download"""
    image: str  # base64 encoded
    width: int
    height: int
    dimensions: List[dict]
    format: str = "png"  # png or jpeg


# ==================
# API Endpoints
# ==================

@router.post("/pdf")
async def download_ballooned_pdf(request: DownloadRequest):
    """
    Generate a single PDF with all pages ballooned.
    """
    from services.download_service import download_service
    from models.schemas import ExportMetadata
    
    # Build metadata
    metadata = None
    if request.part_number or request.part_name or request.revision:
        metadata = ExportMetadata(
            part_number=request.part_number,
            part_name=request.part_name,
            revision=request.revision
        )
    
    # Convert pages to dict format
    pages_data = [
        {
            "page_number": p.page_number,
            "image": p.image,
            "width": p.width,
            "height": p.height,
            "dimensions": p.dimensions
        }
        for p in request.pages
    ]
    
    # Generate PDF
    result = download_service.generate_ballooned_pdf(
        pages=pages_data,
        metadata=metadata
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error_message)
    
    return StreamingResponse(
        io.BytesIO(result.file_bytes),
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        }
    )


@router.post("/zip")
async def download_zip_bundle(request: DownloadRequest):
    """
    Generate a ZIP bundle with ballooned images and AS9102 Excel.
    """
    from services.download_service import download_service
    from models.schemas import ExportMetadata
    
    # Build metadata
    metadata = None
    if request.part_number or request.part_name or request.revision:
        metadata = ExportMetadata(
            part_number=request.part_number,
            part_name=request.part_name,
            revision=request.revision
        )
    
    # Convert pages to dict format
    pages_data = [
        {
            "page_number": p.page_number,
            "image": p.image,
            "width": p.width,
            "height": p.height,
            "dimensions": p.dimensions
        }
        for p in request.pages
    ]
    
    # Generate ZIP
    result = download_service.generate_zip_bundle(
        pages=pages_data,
        metadata=metadata,
        grid_detected=request.grid_detected
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error_message)
    
    return StreamingResponse(
        io.BytesIO(result.file_bytes),
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        }
    )


@router.post("/image")
async def download_single_image(request: SingleImageDownloadRequest):
    """
    Generate a single ballooned image.
    """
    from services.download_service import download_service
    
    result = download_service.generate_single_ballooned_image(
        image_base64=request.image,
        dimensions=request.dimensions,
        width=request.width,
        height=request.height,
        format=request.format
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error_message)
    
    return StreamingResponse(
        io.BytesIO(result.file_bytes),
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        }
    )


@router.post("/excel")
async def download_excel_only(request: DownloadRequest):
    """
    Generate Excel file using selected template.

    Supports:
    - AS9102 (default) - AS9102 Rev C 3-Form Workbook
    - PPAP - Production Part Approval Process with statistics
    - ISO13485 - Medical Devices with traceability focus
    - Custom template ID - User's uploaded template
    """
    from services.export_service import export_service
    from models.schemas import ExportFormat, ExportTemplate, ExportMetadata, BillOfMaterialItem, SpecificationItem

    # Build metadata
    metadata = None
    if request.part_number or request.part_name or request.revision:
        metadata = ExportMetadata(
            part_number=request.part_number,
            part_name=request.part_name,
            revision=request.revision,
            serial_number=request.serial_number,
            fai_report_number=request.fai_report_number
        )

    # Collect all dimensions
    all_dimensions = []
    for page in request.pages:
        for dim in page.dimensions:
            dim_copy = dict(dim)
            dim_copy["page"] = page.page_number
            all_dimensions.append(dim_copy)

    # Convert BOM and Specifications
    bom_items = [
        BillOfMaterialItem(
            part_name=item.part_name,
            part_number=item.part_number,
            qty=item.qty
        )
        for item in request.bom
    ]

    spec_items = [
        SpecificationItem(
            process=item.process,
            spec_number=item.spec_number,
            code=item.code
        )
        for item in request.specifications
    ]

    # Generate Excel with template selection
    file_bytes, content_type, filename = export_service.generate_export(
        dimensions=all_dimensions,
        format=ExportFormat.XLSX,
        template=ExportTemplate.AS9102_FORM3,
        metadata=metadata,
        bom=bom_items,
        specifications=spec_items,
        grid_detected=request.grid_detected,
        total_pages=len(request.pages),
        template_name=request.template_name,
        visitor_id=request.visitor_id
    )

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
