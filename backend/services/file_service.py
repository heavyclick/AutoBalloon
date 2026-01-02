"""

File Service - Multi-Page PDF Processing

Handles PDF page extraction, image conversion, and file validation.



Supports:

- Multi-page PDF extraction (up to 20 pages)

- High-resolution PNG conversion for each page

- Single image passthrough

- Hybrid Vector Text Extraction (extracts selectable text from PDFs)



Uses pdf2image (with poppler backend) for PDF to image conversion.

Uses PyMuPDF (fitz) for accurate vector text extraction with precise bounding boxes.

"""

import io

import base64

import logging

from typing import Optional, List, Tuple, Dict, Any

from dataclasses import dataclass

from enum import Enum

from PIL import Image

from pdf2image import convert_from_bytes

import fitz  # PyMuPDF



# Configure logger

logger = logging.getLogger(__name__)



class FileType(Enum):

    """Supported file types"""

    PDF = "pdf"

    PNG = "png"

    JPEG = "jpeg"

    UNKNOWN = "unknown"





@dataclass

class PageImage:

    """Represents a single page converted to image"""

    page_number: int

    image_bytes: bytes

    width: int

    height: int

    base64_image: str  # For API response

    vector_text: Optional[List[Dict[str, Any]]] = None  # Extracted text with coordinates





@dataclass

class FileProcessingResult:

    """Result of file processing"""

    success: bool

    file_type: FileType

    total_pages: int

    pages: List[PageImage]

    error_message: Optional[str] = None





class FileService:

    """

    Handles multi-page PDF and image file processing.

    """

    

    # Configuration

    MAX_PAGES = 20  # Maximum pages to process

    DEFAULT_DPI = 200  # Resolution for PDF to image conversion

    MAX_IMAGE_DIMENSION = 4096  # Maximum width/height for images

    

    def __init__(self, max_pages: int = 20, dpi: int = 200):

        """

        Initialize file service.

        

        Args:

            max_pages: Maximum number of pages to process (default 20)

            dpi: DPI for PDF to image conversion (default 200)

        """

        self.max_pages = max_pages

        self.dpi = dpi

    

    def detect_file_type(self, file_bytes: bytes, filename: Optional[str] = None) -> FileType:

        """

        Detect file type from bytes and/or filename.

        

        Args:

            file_bytes: Raw file bytes

            filename: Optional filename with extension

            

        Returns:

            Detected FileType

        """

        # Check magic bytes first

        if file_bytes[:4] == b'%PDF':

            return FileType.PDF

        if file_bytes[:8] == b'\x89PNG\r\n\x1a\n':

            return FileType.PNG

        if file_bytes[:2] == b'\xff\xd8':

            return FileType.JPEG

        

        # Fallback to filename extension

        if filename:

            ext = filename.lower().split('.')[-1]

            if ext == 'pdf':

                return FileType.PDF

            if ext == 'png':

                return FileType.PNG

            if ext in ('jpg', 'jpeg'):

                return FileType.JPEG

        

        return FileType.UNKNOWN

    

    def process_file(

        self, 

        file_bytes: bytes, 

        filename: Optional[str] = None

    ) -> FileProcessingResult:

        """

        Process uploaded file, extracting pages as images.

        

        For PDFs: Converts each page to a high-resolution PNG and extracts vector text.

        For images: Returns single page with original image.

        

        Args:

            file_bytes: Raw file bytes

            filename: Optional filename

            

        Returns:

            FileProcessingResult with page images and text data

        """

        file_type = self.detect_file_type(file_bytes, filename)

        

        if file_type == FileType.PDF:

            return self._process_pdf(file_bytes)

        elif file_type in (FileType.PNG, FileType.JPEG):

            return self._process_image(file_bytes, file_type)

        else:

            return FileProcessingResult(

                success=False,

                file_type=FileType.UNKNOWN,

                total_pages=0,

                pages=[],

                error_message="Unsupported file type. Please upload a PDF, PNG, or JPEG."

            )

    

    def _process_pdf(self, pdf_bytes: bytes) -> FileProcessingResult:

        """

        Process multi-page PDF, converting each page to PNG and extracting text.



        Args:

            pdf_bytes: Raw PDF file bytes



        Returns:

            FileProcessingResult with all page images and vector data

        """

        try:

            # Initialize PyMuPDF document for text extraction

            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            total_pages_pdf = len(pdf_doc)



            # Determine pages to process

            pages_to_process = min(total_pages_pdf, self.max_pages)



            # Convert PDF pages to images using pdf2image

            pil_images = convert_from_bytes(

                pdf_bytes,

                dpi=self.dpi,

                first_page=1,

                last_page=pages_to_process,

                fmt='png'

            )



            pages = []

            for i, pil_img in enumerate(pil_images):

                page_num = i + 1



                # --- Vector Text Extraction (PyMuPDF - Accurate Bounding Boxes) ---

                vector_data = []

                try:

                    fitz_page = pdf_doc[i]

                    page_rect = fitz_page.rect

                    w = page_rect.width

                    h = page_rect.height



                    if w > 0 and h > 0:

                        # Extract text with detailed position information

                        # Using "dict" format provides blocks, lines, spans with accurate bounding boxes

                        text_dict = fitz_page.get_text("dict")



                        # Iterate through text blocks, lines, and spans

                        for block in text_dict.get("blocks", []):

                            # Only process text blocks (type 0), not image blocks (type 1)

                            if block.get("type") != 0:

                                continue



                            for line in block.get("lines", []):

                                for span in line.get("spans", []):

                                    text = span.get("text", "").strip()

                                    if not text:

                                        continue



                                    # Get actual bounding box from PyMuPDF (x0, y0, x1, y1)

                                    bbox = span.get("bbox")

                                    if not bbox or len(bbox) != 4:

                                        continue



                                    x0, y0, x1, y1 = bbox



                                    # Convert to normalized 0-1000 scale

                                    # PDF Coordinates: Origin is Bottom-Left

                                    # System Coordinates: Origin is Top-Left (0-1000)

                                    vector_data.append({

                                        'text': text,

                                        'bbox': {

                                            'xmin': (x0 / w) * 1000,

                                            'ymin': (y0 / h) * 1000,  # Already top-left origin in fitz

                                            'xmax': (x1 / w) * 1000,

                                            'ymax': (y1 / h) * 1000

                                        }

                                    })



                    logger.info(f"Extracted {len(vector_data)} text spans from page {page_num}")

                except Exception as e:

                    logger.warning(f"Vector extraction failed for page {page_num}: {e}")

                # ---------------------------------------------



                # Convert PIL image to PNG bytes

                png_buffer = io.BytesIO()

                pil_img.save(png_buffer, format='PNG')

                png_bytes = png_buffer.getvalue()

                

                # Get dimensions

                width, height = pil_img.size

                

                # Encode to base64

                base64_image = base64.b64encode(png_bytes).decode('utf-8')

                

                pages.append(PageImage(

                    page_number=page_num,

                    image_bytes=png_bytes,

                    width=width,

                    height=height,

                    base64_image=base64_image,

                    vector_text=vector_data  # Pass extracted data

                ))

            

            warning_msg = None

            if total_pages_pdf > self.max_pages:

                warning_msg = f"Processed {pages_to_process} of {total_pages_pdf} pages (max {self.max_pages})"



            # Close the PyMuPDF document

            pdf_doc.close()



            return FileProcessingResult(

                success=True,

                file_type=FileType.PDF,

                total_pages=total_pages_pdf,

                pages=pages,

                error_message=warning_msg

            )



        except Exception as e:

            logger.error(f"Failed to process PDF: {str(e)}")

            # Ensure document is closed even on error

            try:

                if 'pdf_doc' in locals():

                    pdf_doc.close()

            except:

                pass

            return FileProcessingResult(

                success=False,

                file_type=FileType.PDF,

                total_pages=0,

                pages=[],

                error_message=f"Failed to process PDF: {str(e)}"

            )

    

    def _process_image(

        self, 

        image_bytes: bytes, 

        file_type: FileType

    ) -> FileProcessingResult:

        """

        Process single image file.

        

        Args:

            image_bytes: Raw image bytes

            file_type: Detected file type

            

        Returns:

            FileProcessingResult with single page

        """

        try:

            # Open image to get dimensions and potentially convert

            img = Image.open(io.BytesIO(image_bytes))

            width, height = img.size

            

            # Convert to PNG if JPEG (for consistency)

            if file_type == FileType.JPEG:

                png_buffer = io.BytesIO()

                img.save(png_buffer, format='PNG')

                png_bytes = png_buffer.getvalue()

            else:

                png_bytes = image_bytes

            

            # Encode to base64

            base64_image = base64.b64encode(png_bytes).decode('utf-8')

            

            page = PageImage(

                page_number=1,

                image_bytes=png_bytes,

                width=width,

                height=height,

                base64_image=base64_image,

                vector_text=None # No vector text for images

            )

            

            return FileProcessingResult(

                success=True,

                file_type=file_type,

                total_pages=1,

                pages=[page]

            )

            

        except Exception as e:

            return FileProcessingResult(

                success=False,

                file_type=file_type,

                total_pages=0,

                pages=[],

                error_message=f"Failed to process image: {str(e)}"

            )

    

    def get_page_as_png(

        self, 

        pdf_bytes: bytes, 

        page_number: int

    ) -> Optional[Tuple[bytes, int, int]]:

        """

        Extract a specific page from PDF as PNG.

        

        Args:

            pdf_bytes: Raw PDF bytes

            page_number: Page number (1-indexed)

            

        Returns:

            Tuple of (png_bytes, width, height) or None if failed

        """

        try:

            # Convert just the requested page

            pil_images = convert_from_bytes(

                pdf_bytes,

                dpi=self.dpi,

                first_page=page_number,

                last_page=page_number,

                fmt='png'

            )

            

            if not pil_images:

                return None

            

            pil_img = pil_images[0]

            

            # Convert to PNG bytes

            png_buffer = io.BytesIO()

            pil_img.save(png_buffer, format='PNG')

            png_bytes = png_buffer.getvalue()

            

            width, height = pil_img.size

            

            return (png_bytes, width, height)

            

        except Exception:

            return None





# Singleton instance

file_service = FileService()
