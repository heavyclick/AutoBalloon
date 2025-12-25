"""
Pydantic models for AutoBalloon API
Updated to support multi-page PDF processing
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BoundingBox(BaseModel):
    """Normalized bounding box coordinates (0-1000 scale)"""
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)
    
    @property
    def center_x(self) -> int:
        return (self.xmin + self.xmax) // 2
    
    @property
    def center_y(self) -> int:
        return (self.ymin + self.ymax) // 2


class Dimension(BaseModel):
    """A detected dimension with its location and metadata"""
    id: int
    value: str
    zone: Optional[str] = None
    bounding_box: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0)
    page: int = 1  # NEW: Page number for multi-page documents
    manually_added: bool = False
    manually_moved: bool = False


class GridInfo(BaseModel):
    """Grid detection results"""
    detected: bool
    columns: list[str] = []
    rows: list[str] = []
    boundaries: Optional[dict] = None


class ProcessingMetadata(BaseModel):
    """Metadata about the processing operation"""
    filename: str
    original_format: str
    processed_at: datetime
    dimension_count: int
    processing_time_ms: int


# ==================
# UPDATED: Multi-page response models
# ==================

class PageResult(BaseModel):
    """Result for a single page in multi-page processing"""
    page_number: int
    image: str  # Base64 encoded PNG
    width: int
    height: int
    dimensions: List[Dimension] = []
    grid_detected: bool = True


class ProcessResponse(BaseModel):
    """Response from /api/process endpoint - Updated for multi-page"""
    success: bool
    total_pages: int = 1  # NEW: Total pages in document
    pages: List[PageResult] = []  # NEW: Per-page results
    image: Optional[str] = None  # Base64 encoded image (legacy single-page)
    dimensions: list[Dimension] = []  # All dimensions (legacy, or flattened)
    grid: Optional[GridInfo] = None
    metadata: Optional[ProcessingMetadata] = None
    message: Optional[str] = None  # NEW: Warning messages (e.g., "Processed 20 of 25 pages")
    error: Optional[dict] = None


class ErrorCode(str, Enum):
    INVALID_FILE = "INVALID_FILE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    VISION_API_ERROR = "VISION_API_ERROR"
    OCR_API_ERROR = "OCR_API_ERROR"
    PARSE_ERROR = "PARSE_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    USAGE_LIMIT_EXCEEDED = "USAGE_LIMIT_EXCEEDED"


class ErrorResponse(BaseModel):
    """Error details"""
    code: ErrorCode
    message: str


class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"


class ExportTemplate(str, Enum):
    SIMPLE = "SIMPLE"
    AS9102_FORM3 = "AS9102_FORM3"


class ExportMetadata(BaseModel):
    """Optional metadata for exports"""
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    revision: Optional[str] = None


class ExportRequest(BaseModel):
    """Request body for /api/export endpoint - Updated for multi-page"""
    format: ExportFormat
    template: ExportTemplate = ExportTemplate.AS9102_FORM3
    dimensions: list[dict]
    metadata: Optional[ExportMetadata] = None
    filename: str = "inspection"
    total_pages: int = 1  # NEW: For Sheet column in export
    grid_detected: bool = True  # NEW: For footer note


class UpdateBalloonRequest(BaseModel):
    """Request to update a balloon's position"""
    dimension_id: int
    new_bounding_box: BoundingBox


class UpdateBalloonResponse(BaseModel):
    """Response after updating balloon position"""
    success: bool
    updated_zone: Optional[str] = None


class AddBalloonRequest(BaseModel):
    """Request to manually add a balloon"""
    value: str
    bounding_box: BoundingBox
    page: int = 1  # NEW: Which page to add balloon to


class AddBalloonResponse(BaseModel):
    """Response after adding a balloon"""
    success: bool
    dimension: Optional[Dimension] = None


class HealthResponse(BaseModel):
    """Response from /api/health endpoint"""
    status: str
    version: str
