"""
Template Routes - Custom Template Upload, List, Delete, Download
Handles custom Excel template management for exports.
"""
import io
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.export_service import export_service

router = APIRouter(prefix="/templates", tags=["templates"])

# Maximum template file size (5MB)
MAX_TEMPLATE_SIZE = 5 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = [".xlsx"]


class TemplateUploadResponse(BaseModel):
    success: bool
    template: Optional[dict] = None
    message: Optional[str] = None


class TemplateListResponse(BaseModel):
    success: bool
    templates: list = []


class TemplateDeleteResponse(BaseModel):
    success: bool
    message: str


def get_visitor_id(x_visitor_id: Optional[str] = Header(None)) -> str:
    """Extract visitor_id from header or return empty string."""
    return x_visitor_id or ""


@router.post("/upload", response_model=TemplateUploadResponse)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    x_visitor_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None)
):
    """
    Upload a custom Excel template (.xlsx) file.

    The template can contain {{placeholders}} that will be replaced during export:

    Metadata placeholders:
    - {{part_number}}, {{part_name}}, {{revision}}, {{serial_number}}, {{date}}

    Dimension table row placeholders (use in a row to create repeating data):
    - {{dim.id}}, {{dim.zone}}, {{dim.value}}, {{dim.actual}}
    - {{dim.min}}, {{dim.max}}, {{dim.method}}, {{dim.class}}

    BOM table row placeholders:
    - {{bom.part_number}}, {{bom.part_name}}, {{bom.qty}}

    Specification table row placeholders:
    - {{spec.process}}, {{spec.spec_number}}
    """
    visitor_id = x_visitor_id or ""
    user_email = x_user_email

    if not visitor_id and not user_email:
        raise HTTPException(
            status_code=400,
            detail="Missing visitor_id or user_email header"
        )

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = "." + file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
        )

    # Read file content
    file_bytes = await file.read()

    # Check file size
    if len(file_bytes) > MAX_TEMPLATE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_TEMPLATE_SIZE // (1024*1024)}MB."
        )

    # Check for empty file
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    try:
        template_info = export_service.upload_template(
            file_bytes=file_bytes,
            template_name=name,
            visitor_id=visitor_id,
            user_email=user_email
        )

        return TemplateUploadResponse(
            success=True,
            template=template_info,
            message="Template uploaded successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/list", response_model=TemplateListResponse)
async def list_templates(
    x_visitor_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None)
):
    """
    List all custom templates for the current user.

    Templates are matched by visitor_id or user_email.
    """
    visitor_id = x_visitor_id or ""
    user_email = x_user_email

    if not visitor_id and not user_email:
        return TemplateListResponse(success=True, templates=[])

    templates = export_service.list_templates(
        visitor_id=visitor_id,
        user_email=user_email
    )

    # Remove sensitive file_path from response
    safe_templates = []
    for tmpl in templates:
        safe_templates.append({
            "id": tmpl.get("id"),
            "name": tmpl.get("name"),
            "created_at": tmpl.get("created_at"),
            "file_size": tmpl.get("file_size")
        })

    return TemplateListResponse(success=True, templates=safe_templates)


@router.delete("/{template_id}", response_model=TemplateDeleteResponse)
async def delete_template(
    template_id: str,
    x_visitor_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None)
):
    """
    Delete a custom template by ID.

    Only the owner (matched by visitor_id or email) can delete their templates.
    """
    visitor_id = x_visitor_id or ""
    user_email = x_user_email

    if not visitor_id and not user_email:
        raise HTTPException(
            status_code=400,
            detail="Missing visitor_id or user_email header"
        )

    success = export_service.delete_template(
        template_id=template_id,
        visitor_id=visitor_id,
        user_email=user_email
    )

    if success:
        return TemplateDeleteResponse(
            success=True,
            message="Template deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Template not found or you don't have permission to delete it"
        )


@router.get("/{template_id}/download")
async def download_template(
    template_id: str,
    x_visitor_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None)
):
    """
    Download a custom template file by ID.

    Returns the original .xlsx file.
    """
    visitor_id = x_visitor_id or ""
    user_email = x_user_email

    if not visitor_id and not user_email:
        raise HTTPException(
            status_code=400,
            detail="Missing visitor_id or user_email header"
        )

    result = export_service.get_template_file(
        template_id=template_id,
        visitor_id=visitor_id,
        user_email=user_email
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Template not found or you don't have permission to download it"
        )

    file_bytes, filename = result

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# Available tokens reference for documentation
AVAILABLE_TOKENS = {
    "metadata": {
        "{{part_number}}": "Part number from export metadata",
        "{{part_name}}": "Part name from export metadata",
        "{{revision}}": "Revision level",
        "{{serial_number}}": "Serial number",
        "{{fai_report_number}}": "FAI report number",
        "{{date}}": "Current date (YYYY-MM-DD format)"
    },
    "dimensions": {
        "{{dim.id}}": "Dimension/characteristic number",
        "{{dim.zone}}": "Zone reference (e.g., A1, B2)",
        "{{dim.value}}": "Dimension value/requirement",
        "{{dim.actual}}": "Actual measured value",
        "{{dim.min}}": "Minimum limit",
        "{{dim.max}}": "Maximum limit",
        "{{dim.method}}": "Inspection method (CMM, Caliper, etc.)",
        "{{dim.class}}": "Classification (Critical, Major, Minor)",
        "{{dim.subtype}}": "Feature type (Linear, Diameter, etc.)"
    },
    "bom": {
        "{{bom.part_number}}": "BOM item part number",
        "{{bom.part_name}}": "BOM item part name",
        "{{bom.qty}}": "BOM item quantity"
    },
    "specifications": {
        "{{spec.process}}": "Process/material name",
        "{{spec.spec_number}}": "Specification number"
    }
}


@router.get("/tokens")
async def get_available_tokens():
    """
    Get a list of all available tokens that can be used in custom templates.

    Use these placeholders in your Excel template cells, and they will be
    automatically replaced with the corresponding data during export.
    """
    return {
        "success": True,
        "tokens": AVAILABLE_TOKENS,
        "instructions": (
            "Place these tokens in your Excel template cells. "
            "Metadata tokens (like {{part_number}}) can be used anywhere. "
            "Table tokens (like {{dim.id}}) should be placed in a row that will be "
            "repeated for each data item."
        )
    }
