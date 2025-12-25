"""
Vision Service
Integrates with Gemini Vision API for semantic understanding of manufacturing drawings.
Used to identify which text elements are dimensions vs. labels, notes, part numbers, etc.

ENHANCED: Captures ALL dimension modifiers like (2x), C/C, REF, TYP
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
    Identifies dimensions on manufacturing drawings.
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
    
    async def identify_dimensions(self, image_bytes: bytes) -> list[str]:
        """
        Use Gemini Vision to identify which text values are dimensions.
        
        Args:
            image_bytes: PNG image data
            
        Returns:
            List of dimension values (strings) that Gemini identified
        """
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = self._build_dimension_identification_prompt()
        
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
                "temperature": 0.1,  # Low temperature for consistency
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
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
        
        return self._parse_dimension_response(result)
    
    def _build_dimension_identification_prompt(self) -> str:
        """Build the prompt for dimension identification - captures ALL modifiers"""
        return """You are an expert manufacturing engineer analyzing a technical drawing. Extract ALL dimensions with their COMPLETE values including modifiers.

## CRITICAL: Include these modifiers WITH the dimension value:

QUANTITY MULTIPLIERS:
- "(2x)", "(4x)", "(6x)" - e.g., "Ø3.4 (2x)" NOT just "Ø3.4"
- "TYP" or "TYPICAL" - e.g., "R5 TYP" NOT just "R5"

SPACING NOTATIONS:
- "C/C" (Center-to-Center) - e.g., "35 C/C" NOT just "35"
- "B.C." or "PCD" (Bolt Circle)

REFERENCE MARKERS:
- "REF" - e.g., "0.95 REF" NOT just "0.95"
- "NOM", "BSC", "MAX", "MIN"

## CORRECT vs WRONG:

✓ "35 C/C"       ✗ "35"
✓ "Ø3.4 (2x)"    ✗ "Ø3.4"
✓ "Ø7.5 (2x)"    ✗ "Ø7.5"
✓ "0.95 REF"     ✗ "0.95"
✓ "R5 TYP"       ✗ "R5"
✓ "89.5°"        ✗ "89.5"
✓ "2×.5 (2x)"    ✗ "2×.5"

## WHAT TO EXTRACT:
- Linear dimensions (e.g., "12.50", "35 C/C")
- Diameters (e.g., "Ø25", "Ø3.4 (2x)")
- Radii (e.g., "R5", "R2.5 TYP")
- Angles (e.g., "45°", "89.5°")
- Tolerances (e.g., "12.50 ±0.05")
- Thread callouts (e.g., "M8×1.25")
- Reference dimensions (e.g., "15.3 REF")

## WHAT TO IGNORE:
- Part numbers, revision letters, drawing numbers
- Scale indicators (e.g., "SCALE 2:1")
- Title block text (PRODUCT, MATERIAL, SIZE, SHEET)
- Company names and logos
- Zone/grid references (A, B, C... 1, 2, 3...)
- Section labels (e.g., "SECTION A-A")
- Notes that are not measurements

## RULES:
1. Extract EXACT text as shown INCLUDING all modifiers
2. Include symbols (Ø, R, ±, °) that are part of the dimension
3. Include quantity multipliers (2x) that appear near the dimension
4. Include spacing notations (C/C) that appear with the dimension
5. Do NOT split modifiers from their dimensions

Return JSON:
{
    "dimensions": ["35 C/C", "Ø3.4 (2x)", "Ø7.5 (2x)", "89.5°", "0.95 REF"]
}

Return ONLY the JSON object."""
    
    def _parse_dimension_response(self, response: dict) -> list[str]:
        """Parse Gemini's response and extract dimension values"""
        try:
            # Navigate Gemini response structure
            candidates = response.get("candidates", [])
            if not candidates:
                return []
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return []
            
            text = parts[0].get("text", "")
            
            # Parse JSON from response
            # Handle potential markdown code blocks
            text = text.strip()
            if text.startswith("```"):
                # Remove markdown code block
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            
            data = json.loads(text)
            dimensions = data.get("dimensions", [])
            
            # Validate and clean
            clean_dimensions = []
            for dim in dimensions:
                if isinstance(dim, str) and dim.strip():
                    clean_dimensions.append(dim.strip())
            
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
    
    async def detect_grid(self, image_bytes: bytes) -> Optional[dict]:
        """
        Use Gemini Vision to detect the grid reference system on the drawing.
        
        Returns:
            Grid info dict or None if no grid detected
        """
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
            # Grid detection is optional - return None on any error
            return None
        
        return self._parse_grid_response(result)
    
    def _build_grid_detection_prompt(self) -> str:
        """Build the prompt for grid detection"""
        return """Analyze this engineering drawing and identify the grid reference system if present.

Look for:
1. Column letters (typically A-H or A-J) along the top or bottom edge
2. Row numbers (typically 1-4 or 1-6) along the left or right edge
3. Grid lines dividing the drawing into zones

If a grid system is present, estimate the boundaries of each zone.

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
            
            # Calculate evenly-distributed boundaries
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


# Factory function
def create_vision_service(api_key: Optional[str] = None) -> VisionService:
    """Create vision service instance"""
    return VisionService(api_key=api_key)
