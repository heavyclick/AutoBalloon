"""
File Service
Handles PDF and image file processing, converting all inputs to normalized PNG images.
"""
import base64
import io
import tempfile
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import fitz  # PyMuPDF

from config import (
    MAX_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    TARGET_DPI,
)
from models import ErrorCode


class FileServiceError(Exception):
    """Custom exception for file service errors"""
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class FileService:
    """
    Converts uploaded files (PDF, PNG, JPEG, TIFF) to normalized PNG images
    suitable for OCR and vision API processing.
    """
    
    def __init__(self, target_dpi: int = TARGET_DPI):
        self.target_dpi = target_dpi
    
    def validate_file(self, file_content: bytes, filename: str) -> None:
        """
        Validate file size and extension.
        Raises FileServiceError if invalid.
        """
        # Check file size
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise FileServiceError(
                ErrorCode.FILE_TOO_LARGE,
                f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
            )
        
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise FileServiceError(
                ErrorCode.UNSUPPORTED_FORMAT,
                f"Unsupported file format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return "pdf"
        elif ext in {".png", ".jpg", ".jpeg"}:
            return "image"
        elif ext in {".tiff", ".tif"}:
            return "tiff"
        return "unknown"
    
    def process_file(self, file_content: bytes, filename: str) -> Tuple[bytes, str, int, int]:
        """
        Process uploaded file and convert to normalized PNG.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Tuple of (png_bytes, original_format, width, height)
            
        Raises:
            FileServiceError: If file cannot be processed
        """
        self.validate_file(file_content, filename)
        
        file_type = self.get_file_type(filename)
        
        try:
            if file_type == "pdf":
                png_bytes, width, height = self._process_pdf(file_content)
                return png_bytes, "pdf", width, height
            else:
                png_bytes, width, height = self._process_image(file_content)
                return png_bytes, file_type, width, height
        except FileServiceError:
            raise
        except Exception as e:
            raise FileServiceError(
                ErrorCode.PROCESSING_ERROR,
                f"Failed to process file: {str(e)}"
            )
    
    def _process_pdf(self, pdf_content: bytes) -> Tuple[bytes, int, int]:
        """
        Convert first page of PDF to high-resolution PNG.
        Uses PyMuPDF (fitz) for PDF rendering.
        """
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
        except Exception as e:
            raise FileServiceError(
                ErrorCode.INVALID_FILE,
                f"Could not open PDF: {str(e)}"
            )
        
        if doc.page_count == 0:
            doc.close()
            raise FileServiceError(
                ErrorCode.INVALID_FILE,
                "PDF has no pages"
            )
        
        # Get first page
        page = doc[0]
        
        # Calculate zoom factor for target DPI
        # PDF default is 72 DPI
        zoom = self.target_dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        
        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        
        # Convert to PNG bytes
        png_bytes = pixmap.tobytes("png")
        width = pixmap.width
        height = pixmap.height
        
        doc.close()
        
        return png_bytes, width, height
    
    def _process_image(self, image_content: bytes) -> Tuple[bytes, int, int]:
        """
        Process image file (PNG, JPEG, TIFF) and normalize to PNG.
        Preserves original resolution but ensures consistent format.
        """
        try:
            image = Image.open(io.BytesIO(image_content))
        except Exception as e:
            raise FileServiceError(
                ErrorCode.INVALID_FILE,
                f"Could not open image: {str(e)}"
            )
        
        # Convert to RGB if necessary (handles CMYK, RGBA, etc.)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        
        # Get dimensions
        width, height = image.size
        
        # For TIFF with multiple pages, use first page only
        if hasattr(image, 'n_frames') and image.n_frames > 1:
            image.seek(0)
        
        # Convert to PNG bytes
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        png_bytes = output.getvalue()
        
        return png_bytes, width, height
    
    def to_base64(self, png_bytes: bytes) -> str:
        """Convert PNG bytes to base64 data URI"""
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    
    def from_base64(self, data_uri: str) -> bytes:
        """Extract PNG bytes from base64 data URI"""
        if data_uri.startswith("data:"):
            # Remove data URI prefix
            _, b64_data = data_uri.split(",", 1)
        else:
            b64_data = data_uri
        return base64.b64decode(b64_data)
    
    def create_thumbnail(self, png_bytes: bytes, max_width: int = 200) -> str:
        """
        Create a smaller thumbnail for history storage.
        Returns base64 JPEG data URI.
        """
        image = Image.open(io.BytesIO(png_bytes))
        
        # Calculate new dimensions maintaining aspect ratio
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        
        # Resize
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to JPEG for smaller size
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=70, optimize=True)
        
        b64 = base64.b64encode(output.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"


# Singleton instance
file_service = FileService()
