"""
Detection Service - Multi-Page Support
Orchestrates OCR + Gemini Vision fusion for accurate dimension detection.
"""
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from difflib import SequenceMatcher

from services.ocr_service import OCRService, OCRDetection, create_ocr_service
from services.vision_service import VisionService, create_vision_service
from services.file_service import FileService, PageImage, FileProcessingResult
from models.schemas import Dimension, BoundingBox, ErrorCode


@dataclass
class PageDetectionResult:
    """Result of dimension detection for a single page"""
    page_number: int
    dimensions: List[Dimension]
    grid_detected: bool
    image_base64: str
    width: int
    height: int


@dataclass
class MultiPageDetectionResult:
    """Result of dimension detection for all pages"""
    success: bool
    total_pages: int
    pages: List[PageDetectionResult]
    all_dimensions: List[Dimension]
    error_message: Optional[str] = None


class DetectionService:
    """
    Fuses OCR and Gemini Vision results for accurate dimension detection.
    """
    
    MODIFIER_PATTERN = re.compile(
        r'^[\(\[]?\d+[xX][\)\]]?$|'
        r'^[xX]\d+$|'
        r'^TYP(?:ICAL)?$|'
        r'^REF(?:ERENCE)?$|'
        r'^C/?C$|'
        r'^C-C$|'
        r'^B\.?C\.?$|'
        r'^PCD$|'
        r'^MAX(?:IMUM)?$|'
        r'^MIN(?:IMUM)?$|'
        r'^NOM(?:INAL)?$|'
        r'^BSC$|'
        r'^BASIC$|'
        r'^THRU$|'
        r'^DEEP$|'
        r'^DP$|'
        r'^\d+\s*PL(?:ACES?)?\.?$|'
        r'^EQ\.?\s*SP\.?$',
        re.IGNORECASE
    )
    
    STANDARD_GRID_COLUMNS = ['H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
    STANDARD_GRID_ROWS = ['4', '3', '2', '1']
    
    def __init__(
        self, 
        ocr_service: Optional[OCRService] = None,
        vision_service: Optional[VisionService] = None,
        file_service: Optional[FileService] = None,
        grid_service = None
    ):
        self.ocr_service = ocr_service
        self.vision_service = vision_service
        self.file_service = file_service or FileService()
        self.grid_service = grid_service
    
    async def detect_dimensions_multipage(
        self,
        file_bytes: bytes,
        filename: Optional[str] = None
    ) -> MultiPageDetectionResult:
        """
        Detect dimensions from a multi-page PDF or single image.
        """
        file_result = self.file_service.process_file(file_bytes, filename)
        
        if not file_result.success:
            return MultiPageDetectionResult(
                success=False,
                total_pages=0,
                pages=[],
                all_dimensions=[],
                error_message=file_result.error_message
            )
        
        page_results = []
        current_dimension_id = 1
        
        for page_image in file_result.pages:
            page_dimensions = await self._detect_dimensions_on_page(
                page_image.image_bytes,
                page_image.width,
                page_image.height
            )
            
            grid_detected = True  # Default to standard grid
            
            # Assign zones and IDs
            for dim in page_dimensions:
                dim.zone = self._calculate_zone(
                    dim.bounding_box.center_x,
                    dim.bounding_box.center_y,
                    None
                )
                dim.id = current_dimension_id
                dim.page = page_image.page_number
                current_dimension_id += 1
            
            page_results.append(PageDetectionResult(
                page_number=page_image.page_number,
                dimensions=page_dimensions,
                grid_detected=grid_detected,
                image_base64=page_image.base64_image,
                width=page_image.width,
                height=page_image.height
            ))
        
        all_dimensions = []
        for page_result in page_results:
            all_dimensions.extend(page_result.dimensions)
        
        return MultiPageDetectionResult(
            success=True,
            total_pages=file_result.total_pages,
            pages=page_results,
            all_dimensions=all_dimensions,
            error_message=file_result.error_message
        )
    
    async def _detect_dimensions_on_page(
        self,
        image_bytes: bytes,
        image_width: int,
        image_height: int
    ) -> List[Dimension]:
        """Detect dimensions for a single page."""
        ocr_detections = await self._run_ocr(image_bytes, image_width, image_height)
        dimension_values = await self._run_gemini(image_bytes)
        matched_dimensions = self._match_dimensions(ocr_detections, dimension_values)
        sorted_dimensions = self._sort_reading_order(matched_dimensions)
        return sorted_dimensions
    
    def _calculate_zone(
        self, 
        center_x: float, 
        center_y: float,
        grid: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """Calculate grid zone for a point."""
        columns = grid['columns'] if grid else self.STANDARD_GRID_COLUMNS
        rows = grid['rows'] if grid else self.STANDARD_GRID_ROWS
        
        num_cols = len(columns)
        col_width = 1000 / num_cols
        col_idx = min(int(center_x / col_width), num_cols - 1)
        
        num_rows = len(rows)
        row_height = 1000 / num_rows
        row_idx = min(int(center_y / row_height), num_rows - 1)
        
        column_label = columns[col_idx] if col_idx < len(columns) else '?'
        row_label = rows[row_idx] if row_idx < len(rows) else '?'
        
        return f"{column_label}{row_label}"
    
    async def _run_ocr(
        self, 
        image_bytes: bytes, 
        image_width: int, 
        image_height: int
    ) -> List[OCRDetection]:
        """Run OCR and group adjacent text"""
        if not self.ocr_service:
            return []
        
        try:
            detections = await self.ocr_service.detect_text(
                image_bytes, image_width, image_height
            )
            grouped = self.ocr_service.group_adjacent_text(detections)
            return grouped
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    async def _run_gemini(self, image_bytes: bytes) -> List[str]:
        """Run Gemini to identify dimension values"""
        if not self.vision_service:
            return []
        
        try:
            dimensions = await self.vision_service.identify_dimensions(image_bytes)
            return dimensions
        except Exception as e:
            print(f"Gemini error: {e}")
            return []
    
    def _is_modifier_only(self, text: str) -> bool:
        """Check if OCR text is a modifier only."""
        return bool(self.MODIFIER_PATTERN.match(text.strip()))
    
    def _extract_base_value(self, dimension: str) -> str:
        """Extract the base numeric value from a compound dimension."""
        base = dimension
        base = re.sub(r'\s*[\(\[]\d+[xX][\)\]]\s*$', '', base)
        base = re.sub(r'\s+(TYP|TYPICAL|REF|REFERENCE|C/C|C-C|B\.?C\.?|PCD|MAX|MIN|NOM|BSC|BASIC|THRU|DEEP|EQ\s*SP)\.?\s*$', '', base, flags=re.IGNORECASE)
        base = re.sub(r'\s+\d+\s*PL(ACES?)?\.?\s*$', '', base, flags=re.IGNORECASE)
        return base.strip()
    
    def _merge_bounding_boxes(self, boxes: List[dict]) -> dict:
        """Merge multiple bounding boxes into one."""
        if not boxes:
            return {}
        if len(boxes) == 1:
            return boxes[0]
        
        xmin = min(b['xmin'] for b in boxes)
        ymin = min(b['ymin'] for b in boxes)
        xmax = max(b['xmax'] for b in boxes)
        ymax = max(b['ymax'] for b in boxes)
        
        return {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
    
    def _find_nearby_modifiers(
        self, 
        base_ocr: OCRDetection, 
        ocr_detections: List[OCRDetection],
        used_indices: set
    ) -> List[OCRDetection]:
        """Find modifier OCR boxes near the base dimension box."""
        nearby = []
        base_box = base_ocr.bounding_box
        
        height = base_box['ymax'] - base_box['ymin']
        width = base_box['xmax'] - base_box['xmin']
        
        y_threshold = max(height * 2.5, 80)
        x_threshold = max(width * 2, 100)
        
        base_center_x = (base_box['xmin'] + base_box['xmax']) / 2
        base_center_y = (base_box['ymin'] + base_box['ymax']) / 2
        
        for ocr in ocr_detections:
            if id(ocr) in used_indices or ocr is base_ocr:
                continue
            
            if not self._is_modifier_only(ocr.text):
                continue
            
            ocr_box = ocr.bounding_box
            ocr_center_x = (ocr_box['xmin'] + ocr_box['xmax']) / 2
            ocr_center_y = (ocr_box['ymin'] + ocr_box['ymax']) / 2
            
            x_dist = abs(ocr_center_x - base_center_x)
            y_dist = abs(ocr_center_y - base_center_y)
            
            if x_dist < x_threshold and y_dist < y_threshold:
                nearby.append(ocr)
        
        return nearby
    
    def _match_dimensions(
        self, 
        ocr_detections: List[OCRDetection],
        gemini_dimensions: List[str]
    ) -> List[Dimension]:
        """Match Gemini's dimension list against OCR detections."""
        matched = []
        used_ocr_indices = set()
        
        for dim_value in gemini_dimensions:
            best_match = self._find_best_ocr_match(
                dim_value, 
                ocr_detections, 
                used_ocr_indices
            )
            
            if best_match:
                ocr_detection, match_confidence, merged_box = best_match
                used_ocr_indices.add(id(ocr_detection))
                
                combined_confidence = ocr_detection.confidence * match_confidence
                final_box = merged_box if merged_box else ocr_detection.bounding_box
                
                matched.append(Dimension(
                    id=0,
                    value=dim_value,
                    zone=None,
                    bounding_box=BoundingBox(**final_box),
                    confidence=combined_confidence,
                    page=1
                ))
        
        return matched
    
    def _find_best_ocr_match(
        self,
        dimension_value: str,
        ocr_detections: List[OCRDetection],
        used_indices: set
    ) -> Optional[tuple]:
        """Find the OCR detection that best matches the dimension value."""
        normalized_dim = self._normalize_for_matching(dimension_value)
        base_value = self._extract_base_value(dimension_value)
        normalized_base = self._normalize_for_matching(base_value)
        
        best_match = None
        best_score = 0.0
        best_merged_box = None
        
        for ocr in ocr_detections:
            if id(ocr) in used_indices:
                continue
            
            if self._is_modifier_only(ocr.text):
                continue
            
            normalized_ocr = self._normalize_for_matching(ocr.text)
            
            if normalized_dim == normalized_ocr:
                return (ocr, 1.0, None)
            
            if normalized_base == normalized_ocr:
                nearby_modifiers = self._find_nearby_modifiers(ocr, ocr_detections, used_indices)
                if nearby_modifiers:
                    all_boxes = [ocr.bounding_box] + [m.bounding_box for m in nearby_modifiers]
                    merged_box = self._merge_bounding_boxes(all_boxes)
                    return (ocr, 0.95, merged_box)
                else:
                    return (ocr, 0.9, None)
            
            if normalized_ocr in normalized_dim:
                if len(normalized_ocr) >= len(normalized_base) * 0.5:
                    nearby_modifiers = self._find_nearby_modifiers(ocr, ocr_detections, used_indices)
                    score = len(normalized_ocr) / len(normalized_dim)
                    if nearby_modifiers:
                        all_boxes = [ocr.bounding_box] + [m.bounding_box for m in nearby_modifiers]
                        merged_box = self._merge_bounding_boxes(all_boxes)
                        if score > best_score:
                            best_score = score
                            best_match = ocr
                            best_merged_box = merged_box
                    else:
                        if score > best_score:
                            best_score = score
                            best_match = ocr
                            best_merged_box = None
            
            score = self._fuzzy_match_score(normalized_base, normalized_ocr)
            if score > best_score and score > 0.7:
                best_score = score
                best_match = ocr
                best_merged_box = None
        
        if best_match:
            return (best_match, best_score, best_merged_box)
        return None
    
    def _normalize_for_matching(self, text: str) -> str:
        """Normalize text for matching."""
        normalized = text.lower()
        replacements = {"ø": "o", "⌀": "o", "°": "", "±": "+-", " ": "", ",": "."}
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        normalized = re.sub(r'[^\w.\-+/]', '', normalized)
        return normalized
    
    def _fuzzy_match_score(self, s1: str, s2: str) -> float:
        """Calculate fuzzy match score."""
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _sort_reading_order(self, dimensions: List[Dimension]) -> List[Dimension]:
        """Sort dimensions in reading order."""
        if not dimensions:
            return []
        
        band_height = 100
        
        def get_band(dim: Dimension) -> int:
            return int(dim.bounding_box.center_y) // band_height
        
        return sorted(
            dimensions,
            key=lambda d: (get_band(d), d.bounding_box.center_x)
        )


def create_detection_service(
    ocr_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None
) -> DetectionService:
    """Factory function to create detection service."""
    ocr_service = None
    vision_service = None
    
    try:
        if ocr_api_key:
            ocr_service = create_ocr_service(ocr_api_key)
    except ValueError:
        pass
    
    try:
        if gemini_api_key:
            vision_service = create_vision_service(gemini_api_key)
    except ValueError:
        pass
    
    return DetectionService(
        ocr_service=ocr_service,
        vision_service=vision_service
    )
