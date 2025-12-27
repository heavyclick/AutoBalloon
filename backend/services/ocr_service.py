"""
OCR Service - Enhanced Version
Integrates with Google Cloud Vision API for precise text detection with bounding boxes.

IMPROVEMENTS:
- Enhanced grouping for compound dimensions
- Better tolerance value detection
- Improved handling of small text close together
"""
import base64
import re
import httpx
from typing import Optional, List
from dataclasses import dataclass

from config import GOOGLE_CLOUD_API_KEY, NORMALIZED_COORD_SYSTEM
from models import ErrorCode


class OCRServiceError(Exception):
    """Custom exception for OCR service errors"""
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass
class OCRDetection:
    """A single text detection from OCR"""
    text: str
    bounding_box: dict  # {ymin, xmin, ymax, xmax} normalized to 0-1000
    confidence: float
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "bounding_box": self.bounding_box,
            "confidence": self.confidence
        }


class OCRService:
    """
    Google Cloud Vision OCR integration.
    Detects all text in an image with precise bounding boxes.
    """
    
    VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"
    
    # Pattern to detect dimension-like text
    DIMENSION_LIKE_PATTERN = re.compile(
        r'''(?:
            [Øø⌀]\s*[\d.]+|           # Diameter
            R\s*[\d.]+|               # Radius
            \d+\s*/\s*\d+|            # Fractions
            \d+\s+\d+\s*/\s*\d+|      # Mixed fractions
            [\d.]+\s*(?:mm|in|"|')?|  # Decimals with units
            [+-]\s*[\d.]+|            # Tolerances
            [\d.]+\s*[°]              # Angles
        )''',
        re.VERBOSE | re.IGNORECASE
    )
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GOOGLE_CLOUD_API_KEY
        if not self.api_key:
            raise ValueError("Google Cloud API key not configured")
    
    async def detect_text(
        self, 
        image_bytes: bytes, 
        image_width: int, 
        image_height: int
    ) -> List[OCRDetection]:
        """
        Detect all text in an image using Google Cloud Vision.
        
        Args:
            image_bytes: PNG image data
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            List of OCRDetection objects with normalized bounding boxes
        """
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Build request payload - use DOCUMENT_TEXT_DETECTION for better accuracy
        payload = {
            "requests": [{
                "image": {
                    "content": image_b64
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION",
                        "maxResults": 500
                    },
                    {
                        "type": "DOCUMENT_TEXT_DETECTION",  # Added for better OCR
                        "maxResults": 1
                    }
                ],
                "imageContext": {
                    "languageHints": ["en"],
                    "textDetectionParams": {
                        "enableTextDetectionConfidenceScore": True
                    }
                }
            }]
        }
        
        # Make API request
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.VISION_API_URL}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
        except httpx.TimeoutException:
            raise OCRServiceError(
                ErrorCode.OCR_API_ERROR,
                "Google Cloud Vision API request timed out"
            )
        except httpx.HTTPStatusError as e:
            raise OCRServiceError(
                ErrorCode.OCR_API_ERROR,
                f"Google Cloud Vision API error: {e.response.status_code}"
            )
        except Exception as e:
            raise OCRServiceError(
                ErrorCode.OCR_API_ERROR,
                f"Failed to call Google Cloud Vision API: {str(e)}"
            )
        
        # Parse response
        detections = self._parse_response(result, image_width, image_height)
        return detections
    
    def _parse_response(
        self, 
        response: dict, 
        image_width: int, 
        image_height: int
    ) -> List[OCRDetection]:
        """
        Parse Google Vision API response and normalize bounding boxes.
        
        Google Vision returns vertices as pixel coordinates.
        We normalize to 0-1000 scale to match Gemini's coordinate system.
        """
        detections = []
        
        try:
            responses = response.get("responses", [])
            if not responses:
                return detections
            
            annotations = responses[0].get("textAnnotations", [])
            
            # Skip first annotation (full text block), process individual words
            for annotation in annotations[1:]:  # Skip index 0 (full text)
                text = annotation.get("description", "").strip()
                if not text:
                    continue
                
                # Get bounding polygon vertices
                vertices = annotation.get("boundingPoly", {}).get("vertices", [])
                if len(vertices) < 4:
                    continue
                
                # Calculate bounding box from vertices
                # Vertices are in order: top-left, top-right, bottom-right, bottom-left
                x_coords = [v.get("x", 0) for v in vertices]
                y_coords = [v.get("y", 0) for v in vertices]
                
                xmin_px = min(x_coords)
                xmax_px = max(x_coords)
                ymin_px = min(y_coords)
                ymax_px = max(y_coords)
                
                # Normalize to 0-1000 scale
                bounding_box = {
                    "xmin": int((xmin_px / image_width) * NORMALIZED_COORD_SYSTEM),
                    "xmax": int((xmax_px / image_width) * NORMALIZED_COORD_SYSTEM),
                    "ymin": int((ymin_px / image_height) * NORMALIZED_COORD_SYSTEM),
                    "ymax": int((ymax_px / image_height) * NORMALIZED_COORD_SYSTEM),
                }
                
                # Clamp to valid range
                for key in bounding_box:
                    bounding_box[key] = max(0, min(NORMALIZED_COORD_SYSTEM, bounding_box[key]))
                
                # Google Vision doesn't always provide per-word confidence
                # Use 0.95 as default (Google Vision is generally high accuracy)
                confidence = annotation.get("confidence", 0.95)
                
                detections.append(OCRDetection(
                    text=text,
                    bounding_box=bounding_box,
                    confidence=confidence
                ))
                
        except (KeyError, IndexError, TypeError) as e:
            raise OCRServiceError(
                ErrorCode.PARSE_ERROR,
                f"Failed to parse Google Vision response: {str(e)}"
            )
        
        return detections
    
    def group_adjacent_text(
        self, 
        detections: List[OCRDetection],
        horizontal_threshold: int = 30,  # Increased for compound dimensions
        vertical_threshold: int = 15     # Increased for better line detection
    ) -> List[OCRDetection]:
        """
        Group horizontally adjacent text detections into single entries.
        
        ENHANCED for:
        - Mixed fractions: 3 1/4" should stay together
        - Compound dimensions: 0.188" Wd. x 7/8" Lg. should stay together
        - Tolerance stacks: 0.2500in -0.0015 -0.0030 should stay together
        - BUT separate dimensions that happen to be close should NOT merge
        
        Args:
            detections: List of individual text detections
            horizontal_threshold: Max horizontal gap to consider "adjacent"
            vertical_threshold: Max vertical difference to be on same line
            
        Returns:
            List of grouped detections
        """
        if not detections:
            return []
        
        # Sort by y position, then x position
        sorted_detections = sorted(
            detections, 
            key=lambda d: (d.bounding_box["ymin"], d.bounding_box["xmin"])
        )
        
        grouped = []
        current_group = [sorted_detections[0]]
        
        for detection in sorted_detections[1:]:
            prev = current_group[-1]
            
            # Check if on same line (similar y)
            y_diff = abs(detection.bounding_box["ymin"] - prev.bounding_box["ymin"])
            
            # Check horizontal distance
            x_gap = detection.bounding_box["xmin"] - prev.bounding_box["xmax"]
            
            # Determine if we should group
            should_group = False
            
            if y_diff <= vertical_threshold and 0 <= x_gap <= horizontal_threshold:
                curr_text = detection.text.strip()
                prev_text = prev.text.strip()
                
                # Get the full current group text for context
                group_text = " ".join(d.text.strip() for d in current_group)
                
                # CASE 1: Mixed fraction - whole number followed by fraction
                # e.g., "3" followed by "1/4" or "3/4"
                is_mixed_fraction = (
                    prev_text.isdigit() and 
                    bool(re.match(r'^\d+/\d+["\']?$', curr_text))
                )
                
                # CASE 2: Fraction followed by unit/quote
                # e.g., "1/4" followed by '"'
                is_fraction_unit = (
                    bool(re.match(r'^\d+/\d+$', prev_text)) and
                    curr_text in ['"', "'", "in", "mm"]
                )
                
                # CASE 3: Compound dimension components
                # e.g., "Wd." "x" "7/8" "Lg."
                is_compound_part = bool(re.match(
                    r'^(?:x|X|×|Wd\.?|Lg\.?|Dia\.?|Rad\.?|THK\.?|Key)$', 
                    curr_text, re.IGNORECASE
                ))
                
                # CASE 4: Previous was a modifier, current is a dimension
                # e.g., "x" followed by "7/8"
                prev_is_connector = prev_text.lower() in ['x', '×']
                
                # CASE 5: Tolerance values
                is_tolerance = bool(re.match(r'^[+-±]\s*[\d.]+$', curr_text))
                
                # CASE 6: Dimension followed by modifier
                # e.g., "0.188" followed by "Wd."
                prev_is_dimension = self._looks_like_dimension(prev_text)
                curr_is_modifier = bool(re.match(
                    r'^(?:Wd\.?|Lg\.?|Dia\.?|Rad\.?|THK\.?|TYP\.?|REF\.?|MAX\.?|MIN\.?|Key)$', 
                    curr_text, re.IGNORECASE
                ))
                
                # CASE 7: Very small gap - likely same element
                very_small_gap = x_gap <= 8
                
                # Decide grouping
                if is_mixed_fraction:
                    should_group = True
                elif is_fraction_unit:
                    should_group = True
                elif is_compound_part:
                    should_group = True
                elif prev_is_connector:
                    should_group = True
                elif is_tolerance:
                    should_group = True
                elif prev_is_dimension and curr_is_modifier:
                    should_group = True
                elif very_small_gap:
                    # Very small gap - group unless both are standalone dimensions
                    if self._is_standalone_dimension(prev_text) and self._is_standalone_dimension(curr_text):
                        should_group = False
                    else:
                        should_group = True
                else:
                    # Larger gap - don't group if both look like separate dimensions
                    if self._is_standalone_dimension(prev_text) and self._is_standalone_dimension(curr_text):
                        should_group = False
                    # Don't group if current starts a new dimension pattern
                    elif self._starts_new_dimension(curr_text):
                        should_group = False
                    else:
                        should_group = True
            
            if should_group:
                current_group.append(detection)
            else:
                # Finish current group and start new one
                grouped.append(self._merge_group(current_group))
                current_group = [detection]
        
        # Don't forget last group
        if current_group:
            grouped.append(self._merge_group(current_group))
        
        return grouped
    
    def _looks_like_dimension(self, text: str) -> bool:
        """Check if text looks like a dimension value (may be partial)."""
        text = text.strip()
        # Matches: 0.45, 3.5", Ø5, R2, 1/4, 3, 0.188, etc.
        return bool(re.match(
            r'^(?:[Øø⌀R]?\s*)?[\d]+(?:[./]\d+)?(?:\s*\d+/\d+)?(?:\s*["\']|mm|in)?$',
            text, re.IGNORECASE
        ))
    
    def _is_standalone_dimension(self, text: str) -> bool:
        """Check if text is a complete standalone dimension (not a component)."""
        text = text.strip()
        # Must have a number and typically a unit or be a clear decimal
        # Matches: 0.45", 3 1/4", 4 7/8", 0.094", 1/4", but NOT just "3" or "x"
        return bool(re.match(
            r'^(?:[Øø⌀R]?\s*)?\d+(?:\.\d+)?(?:\s+\d+/\d+|\s*/\s*\d+)?\s*["\']$|'  # With unit: 3 1/4", 0.45"
            r'^(?:[Øø⌀R]?\s*)?\d+\.\d{2,}\s*["\']?$|'  # Decimal: 0.094, 0.188"
            r'^(?:[Øø⌀R])\s*\d+(?:\.\d+)?\s*["\']?$',   # Diameter/Radius: Ø5, R2.5
            text, re.IGNORECASE
        ))
    
    def _starts_new_dimension(self, text: str) -> bool:
        """Check if text starts a new dimension (diameter, radius, etc.)."""
        text = text.strip()
        # Starts with diameter or radius symbol
        return bool(re.match(r'^[Øø⌀R]\s*\d', text, re.IGNORECASE))
    
    def _merge_group(self, group: List[OCRDetection]) -> OCRDetection:
        """Merge a group of adjacent detections into one"""
        if len(group) == 1:
            return group[0]
        
        # Concatenate text with appropriate spacing
        texts = []
        for i, d in enumerate(group):
            if i > 0:
                # Determine if space is needed
                prev = group[i - 1]
                gap = d.bounding_box["xmin"] - prev.bounding_box["xmax"]
                
                # Add space for larger gaps or between certain patterns
                if gap > 10:
                    texts.append(" ")
                elif d.text.startswith(('x', 'X', '×')):
                    texts.append(" ")  # Space before "x" separator
            
            texts.append(d.text)
        
        merged_text = "".join(texts)
        
        # Expand bounding box to encompass all
        merged_box = {
            "xmin": min(d.bounding_box["xmin"] for d in group),
            "xmax": max(d.bounding_box["xmax"] for d in group),
            "ymin": min(d.bounding_box["ymin"] for d in group),
            "ymax": max(d.bounding_box["ymax"] for d in group),
        }
        
        # Average confidence
        avg_confidence = sum(d.confidence for d in group) / len(group)
        
        return OCRDetection(
            text=merged_text,
            bounding_box=merged_box,
            confidence=avg_confidence
        )


# Factory function for creating service with optional mock
def create_ocr_service(api_key: Optional[str] = None) -> OCRService:
    """Create OCR service instance"""
    return OCRService(api_key=api_key)
