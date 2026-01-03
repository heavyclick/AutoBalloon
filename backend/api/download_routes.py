"""
Download Routes - Multi-Page Ballooned Output
API endpoints for generating downloadable files with balloons.

SECURITY: All download endpoints require valid access verification.
Users must have either:
- Active paid subscription (LemonSqueezy) via users table
- Valid non-expired promo/pass via access_passes table
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import os
import io
import logging

# Configure security logger for unauthorized access attempts
security_logger = logging.getLogger("security.download")
security_logger.setLevel(logging.WARNING)
if not security_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    ))
    security_logger.addHandler(handler)


router = APIRouter(prefix="/download", tags=["Downloads"])


# ==================
# Access Verification
# ==================

def get_supabase_client():
    """Get Supabase client for access verification."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    return create_client(url, key)


async def verify_access(
    email: Optional[str] = None,
    authorization: Optional[str] = None,
    endpoint: str = "download"
) -> dict:
    """
    Verify user has valid access for downloads.

    Checks:
    1. Paid subscription in users table (LemonSqueezy)
    2. Valid non-expired promo/pass in access_passes table

    Args:
        email: Email from request body
        authorization: Bearer token from Authorization header
        endpoint: Name of endpoint for logging purposes

    Returns:
        dict with access info if valid

    Raises:
        HTTPException(403) if no valid access
    """
    # Extract email from authorization header if provided
    user_email = None

    if email:
        user_email = email.lower().strip()
    elif authorization and authorization.startswith("Bearer "):
        # Try to decode email from token (if JWT-like)
        token = authorization.split(" ", 1)[1]
        try:
            # Import auth service to validate token
            from services.auth_service import auth_service
            user = auth_service.get_current_user(token)
            if user:
                user_email = user.email.lower().strip()
        except Exception:
            pass

    if not user_email:
        security_logger.warning(
            f"UNAUTHORIZED_ACCESS: No email provided for {endpoint} - "
            f"auth_header={'present' if authorization else 'missing'}"
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: Email required for verification"
        )

    try:
        db = get_supabase_client()

        # Check 1: Paid Subscription / 24h Pass in users table
        try:
            user_res = db.table("users").select(
                "is_pro, plan_tier, pass_expires_at, subscription_status"
            ).eq("email", user_email).limit(1).execute()

            if user_res.data and len(user_res.data) > 0:
                u = user_res.data[0]

                # Active Pro Subscription (monthly/yearly)
                if u.get("is_pro") and u.get("subscription_status") == "active":
                    return {
                        "has_access": True,
                        "email": user_email,
                        "type": "subscription",
                        "plan": u.get("plan_tier")
                    }

                # Active 24h Pass
                if u.get("plan_tier") == "pass_24h" and u.get("pass_expires_at"):
                    expires = datetime.fromisoformat(
                        u["pass_expires_at"].replace("Z", "+00:00")
                    )
                    if expires > datetime.now(expires.tzinfo):
                        return {
                            "has_access": True,
                            "email": user_email,
                            "type": "pass_24h",
                            "expires_at": u["pass_expires_at"]
                        }
        except Exception as e:
            # User might not exist in users table - continue to check promos
            pass

        # Check 2: Promo codes / Access Passes
        promo_res = db.table("access_passes").select("*").eq(
            "email", user_email
        ).eq("is_active", True).order("created_at", desc=True).limit(1).execute()

        if promo_res.data and len(promo_res.data) > 0:
            row = promo_res.data[0]

            # Check expiry if set
            if row.get("expires_at"):
                expires = datetime.fromisoformat(
                    row["expires_at"].replace("Z", "+00:00")
                )
                if expires < datetime.now(expires.tzinfo):
                    security_logger.warning(
                        f"EXPIRED_ACCESS: {user_email} attempted {endpoint} "
                        f"with expired promo (expired: {row['expires_at']})"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: Your promotional access has expired"
                    )

            return {
                "has_access": True,
                "email": user_email,
                "type": "promo",
                "pass_type": row.get("pass_type"),
                "expires_at": row.get("expires_at")
            }

        # No valid access found
        security_logger.warning(
            f"NO_VALID_ACCESS: {user_email} attempted {endpoint} without valid access"
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: No valid subscription or promotional access found. "
                   "Please purchase a plan or redeem a promo code."
        )

    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(
            f"ACCESS_CHECK_ERROR: Error checking access for {user_email} "
            f"on {endpoint}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying access: {str(e)}"
        )


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
    # SECURITY: Email for access verification
    email: Optional[str] = None


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
async def download_ballooned_pdf(
    request: DownloadRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate a single PDF with all pages ballooned.

    SECURITY: Requires valid access (paid subscription or active promo).
    Provide email in request body OR Authorization header with Bearer token.
    """
    from services.download_service import download_service
    from models.schemas import ExportMetadata

    # SECURITY: Verify access before allowing download
    await verify_access(
        email=request.email,
        authorization=authorization,
        endpoint="/download/pdf"
    )

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
async def download_zip_bundle(
    request: DownloadRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate a ZIP bundle with ballooned images and AS9102 Excel.

    SECURITY: Requires valid access (paid subscription or active promo).
    Provide email in request body OR Authorization header with Bearer token.
    """
    from services.download_service import download_service
    from models.schemas import ExportMetadata

    # SECURITY: Verify access before allowing download
    await verify_access(
        email=request.email,
        authorization=authorization,
        endpoint="/download/zip"
    )

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
async def download_excel_only(
    request: DownloadRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate Excel file using selected template.

    SECURITY: Requires valid access (paid subscription or active promo).
    Provide email in request body OR Authorization header with Bearer token.

    Supports:
    - AS9102 (default) - AS9102 Rev C 3-Form Workbook
    - PPAP - Production Part Approval Process with statistics
    - ISO13485 - Medical Devices with traceability focus
    - Custom template ID - User's uploaded template
    """
    from services.export_service import export_service
    from models.schemas import ExportFormat, ExportTemplate, ExportMetadata, BillOfMaterialItem, SpecificationItem

    # SECURITY: Verify access before allowing download
    await verify_access(
        email=request.email,
        authorization=authorization,
        endpoint="/download/excel"
    )

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
