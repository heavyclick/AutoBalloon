"""
Vision Service
Integrates with Gemini Vision API for semantic understanding of manufacturing drawings.

MAJOR FIX: Now requests bounding boxes from Gemini so we know WHERE each dimension is,
not just what it says. This prevents misplacement when the same number appears multiple times.
"""
import base64
import json
import re
import httpx
from typing import Optional

from config import GEMINI_API_KEY, NORMALIZED_COORD_SYSTEM
from models import ErrorCode


class VisionServiceError(Exception):
    """Custom exception for vision service errors"""
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class VisionService:
    """
    Gemini Vision API integration for semantic analysis.
    Identifies dimensions on manufacturing drawings WITH their locations.
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
    
    async def identify_dimensions(self, image_bytes: bytes) -> list[str]:
        """
        Legacy method - returns just dimension values.
        Use identify_dimensions_with_locations() for accurate placement.
        """
        result = await self.identify_dimensions_with_locations(image_bytes)
        return [d["value"] for d in result]
    
    async def identify_dimensions_with_locations(self, image_bytes: bytes) -> list[dict]:
        """
        Use Gemini Vision to identify dimensions WITH their approximate locations.
        
        Args:
            image_bytes: PNG image data
            
        Returns:
            List of dicts with:
            {
                "value": "Ø7.5 (2x)",
                "bbox": {"xmin": 0.4, "ymin": 0.3, "xmax": 0.5, "ymax": 0.35}  # normalized 0-1
            }
        """
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = self._build_dimension_with_location_prompt()
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.GEMINI_API_URL}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
        except httpx.TimeoutException:
            raise VisionServiceError(
                ErrorCode.VISION_API_ERROR,
                "Gemini Vision API request timed out"
            )
        except httpx.HTTPStatusError as e:
            raise VisionServiceError(
                ErrorCode.VISION_API_ERROR,
                f"Gemini Vision API error: {e.response.status_code}"
            )
        except Exception as e:
            raise VisionServiceError(
                ErrorCode.VISION_API_ERROR,
                f"Failed to call Gemini Vision API: {str(e)}"
            )
        
        return self._parse_dimension_with_location_response(result)
    
    def _build_dimension_with_location_prompt(self) -> str:
        """Build prompt that requests both dimension values AND their locations"""
        return """You are an expert at reading technical/engineering drawings. Your task is to find ALL dimensions on this drawing and report their VALUES and LOCATIONS.

## CRITICAL: You must provide the LOCATION of each dimension

For each dimension you find, estimate its bounding box as normalized coordinates (0.0 to 1.0):
- xmin: left edge of dimension text (0.0 = left edge of image, 1.0 = right edge)
- ymin: top edge of dimension text (0.0 = top edge of image, 1.0 = bottom edge)
- xmax: right edge of dimension text
- ymax: bottom edge of dimension text

## WHAT TO EXTRACT (dimensions on the actual drawing):
- Linear dimensions (e.g., "35", "50.5", "100")
- Dimensions with modifiers (e.g., "35 C/C", "Ø3.4 (2x)", "7.5 (2x)", "R5 TYP")
- Diameters (e.g., "Ø25", "⌀12.5")
- Radii (e.g., "R5", "R2.5")
- Angles (e.g., "45°", "89.5°")
- Tolerances (e.g., "12.50 ±0.05")
- Thread callouts (e.g., "M8×1.25")
- Any numeric measurement with dimension lines or leaders

## IMPORTANT: Include ALL modifiers with the dimension:
- "(2x)", "(4x)" quantity indicators
- "C/C" (center-to-center)
- "TYP" (typical)
- "REF" (reference)
- Tolerance values

## WHAT TO IGNORE (NOT dimensions):
- Title block text (PRODUCT, MATERIAL, SIZE, SHEET, SCALE, etc.)
- Part numbers and revision letters
- Notes section text
- Grid reference letters and numbers at the borders (A, B, C... 1, 2, 3...)
- Company names and logos
- "FIRST ANGLE PROJECTION" text
- Section labels like "SECTION A-A"
- Component/BOM table content

## OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
    "dimensions": [
        {
            "value": "89.5°",
            "bbox": {"xmin": 0.35, "ymin": 0.18, "xmax": 0.42, "ymax": 0.22}
        },
        {
            "value": "Ø3.4 (2x)",
            "bbox": {"xmin": 0.38, "ymin": 0.28, "xmax": 0.48, "ymax": 0.32}
        },
        {
            "value": "35 C/C",
            "bbox": {"xmin": 0.30, "ymin": 0.25, "xmax": 0.38, "ymax": 0.30}
        }
    ]
}

## RULES:
1. Extract EVERY dimension visible on the drawing (not in title block or notes)
2. Include the COMPLETE dimension value with all modifiers
3. Estimate the bounding box as accurately as possible
4. If the same value appears multiple times, include EACH occurrence with its own location
5. Do NOT include text from the title block, notes section, or border grid references

Return ONLY the JSON object."""
    
    def _parse_dimension_with_location_response(self, response: dict) -> list[dict]:
        """Parse Gemini's response with locations"""
        try:
            candidates = response.get("candidates", [])
            if not candidates:
                return []
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return []
            
            text = parts[0].get("text", "")
            
            # Handle markdown code blocks
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            
            data = json.loads(text)
            dimensions = data.get("dimensions", [])
            
            # Validate and normalize
            clean_dimensions = []
            for dim in dimensions:
                if not isinstance(dim, dict):
                    continue
                
                value = dim.get("value", "")
                bbox = dim.get("bbox", {})
                
                if not value or not isinstance(value, str):
                    continue
                
                # Normalize the value
                value = self._normalize_dimension_value(value.strip())
                
                # Validate and normalize bbox
                try:
                    xmin = float(bbox.get("xmin", 0))
                    ymin = float(bbox.get("ymin", 0))
                    xmax = float(bbox.get("xmax", 0))
                    ymax = float(bbox.get("ymax", 0))
                    
                    # Clamp to valid range
                    xmin = max(0, min(1, xmin))
                    ymin = max(0, min(1, ymin))
                    xmax = max(0, min(1, xmax))
                    ymax = max(0, min(1, ymax))
                    
                    # Ensure max > min
                    if xmax <= xmin:
                        xmax = xmin + 0.05
                    if ymax <= ymin:
                        ymax = ymin + 0.03
                    
                    clean_dimensions.append({
                        "value": value,
                        "bbox": {
                            "xmin": xmin,
                            "ymin": ymin,
                            "xmax": xmax,
                            "ymax": ymax
                        }
                    })
                except (ValueError, TypeError):
                    # Skip dimensions with invalid bbox
                    continue
            
            return clean_dimensions
            
        except json.JSONDecodeError as e:
            raise VisionServiceError(
                ErrorCode.PARSE_ERROR,
                f"Gemini returned invalid JSON: {str(e)}"
            )
        except (KeyError, IndexError, TypeError) as e:
            raise VisionServiceError(
                ErrorCode.PARSE_ERROR,
                f"Failed to parse Gemini response structure: {str(e)}"
            )
    
    def _normalize_dimension_value(self, value: str) -> str:
        """Normalize dimension value formatting for consistency"""
        # Standardize diameter symbols
        value = re.sub(r'⌀|Φ|φ|DIA\s*', 'Ø', value)
        
        # Standardize multiplication symbol for threads
        value = re.sub(r'(\d)\s*[xX]\s*(\d)', r'\1×\2', value)
        
        # Standardize plus/minus
        value = re.sub(r'\+/-|±', '±', value)
        
        # Standardize quantity notation spacing
        value = re.sub(r'\(\s*(\d+)\s*[xX]\s*\)', r'(\1x)', value)
        
        # Standardize C/C notation
        value = re.sub(r'C-C|c-c|C\.C\.|c\.c\.', 'C/C', value)
        
        # Ensure degree symbol is attached
        value = re.sub(r'(\d)\s*°', r'\1°', value)
        
        return value
    
    async def detect_grid(self, image_bytes: bytes) -> Optional[dict]:
        """Use Gemini Vision to detect the grid reference system on the drawing."""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = self._build_grid_detection_prompt()
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.GEMINI_API_URL}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
        except Exception:
            return None
        
        return self._parse_grid_response(result)
    
    def _build_grid_detection_prompt(self) -> str:
        """Build the prompt for grid detection"""
        return """Analyze this engineering drawing and identify the grid reference system if present.

Look for:
1. Column letters (typically A-H or A-J) along the top or bottom edge
2. Row numbers (typically 1-4 or 1-6) along the left or right edge
3. Grid lines dividing the drawing into zones

Return a JSON object:
{
    "has_grid": true,
    "columns": ["A", "B", "C", "D", "E", "F", "G", "H"],
    "rows": ["1", "2", "3", "4"],
    "column_count": 8,
    "row_count": 4
}

If no grid is found:
{
    "has_grid": false
}

Return ONLY the JSON object."""
    
    def _parse_grid_response(self, response: dict) -> Optional[dict]:
        """Parse Gemini's grid detection response"""
        try:
            candidates = response.get("candidates", [])
            if not candidates:
                return None
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return None
            
            text = parts[0].get("text", "").strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            
            data = json.loads(text)
            
            if not data.get("has_grid", False):
                return None
            
            columns = data.get("columns", [])
            rows = data.get("rows", [])
            
            if not columns or not rows:
                return None
            
            col_count = len(columns)
            row_count = len(rows)
            
            column_edges = [
                int(i * NORMALIZED_COORD_SYSTEM / col_count) 
                for i in range(col_count + 1)
            ]
            row_edges = [
                int(i * NORMALIZED_COORD_SYSTEM / row_count) 
                for i in range(row_count + 1)
            ]
            
            return {
                "columns": columns,
                "rows": rows,
                "boundaries": {
                    "column_edges": column_edges,
                    "row_edges": row_edges
                }
            }
            
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return None


def create_vision_service(api_key: Optional[str] = None) -> VisionService:
    """Create vision service instance"""
    return VisionService(api_key=api_key)
