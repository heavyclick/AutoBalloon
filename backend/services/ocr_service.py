"""
OCR Service
Integrates with Google Cloud Vision API for precise text detection with bounding boxes.
"""
import base64
import json
import httpx
from typing import Optional
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
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GOOGLE_CLOUD_API_KEY
        if not self.api_key:
            raise ValueError("Google Cloud API key not configured")
    
    async def detect_text(
        self, 
        image_bytes: bytes, 
        image_width: int, 
        image_height: int
    ) -> list[OCRDetection]:
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
        
        # Build request payload
        payload = {
            "requests": [{
                "image": {
                    "content": image_b64
                },
                "features": [{
                    "type": "TEXT_DETECTION",
                    "maxResults": 500
                }],
                "imageContext": {
                    "languageHints": ["en"]
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
    ) -> list[OCRDetection]:
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
                
                # Google Vision doesn't provide per-word confidence
                # Use 0.95 as default (Google Vision is generally high accuracy)
                detections.append(OCRDetection(
                    text=text,
                    bounding_box=bounding_box,
                    confidence=0.95
                ))
                
        except (KeyError, IndexError, TypeError) as e:
            raise OCRServiceError(
                ErrorCode.PARSE_ERROR,
                f"Failed to parse Google Vision response: {str(e)}"
            )
        
        return detections
    
    def group_adjacent_text(
        self, 
        detections: list[OCRDetection],
        horizontal_threshold: int = 20,  # Normalized units (0-1000)
        vertical_threshold: int = 10
    ) -> list[OCRDetection]:
        """
        Group horizontally adjacent text detections into single entries.
        
        Manufacturing dimensions often appear as separate words:
        "12" "." "50" should become "12.50"
        "Ø" "25" should become "Ø25"
        
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
            
            if y_diff <= vertical_threshold and 0 <= x_gap <= horizontal_threshold:
                # Adjacent, add to current group
                current_group.append(detection)
            else:
                # Start new group
                grouped.append(self._merge_group(current_group))
                current_group = [detection]
        
        # Don't forget last group
        if current_group:
            grouped.append(self._merge_group(current_group))
        
        return grouped
    
    def _merge_group(self, group: list[OCRDetection]) -> OCRDetection:
        """Merge a group of adjacent detections into one"""
        if len(group) == 1:
            return group[0]
        
        # Concatenate text
        merged_text = "".join(d.text for d in group)
        
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
