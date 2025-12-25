"""
Vision Service
Integrates with Gemini Vision API for semantic understanding of manufacturing drawings.
Used to identify which text elements are dimensions vs. labels, notes, part numbers, etc.
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
        """Build the prompt for dimension identification"""
        return """You are analyzing a manufacturing/engineering drawing. Your task is to identify ALL numeric dimensions shown on the drawing.

WHAT TO EXTRACT (dimensions):
- Linear dimensions (e.g., "12.50", "25.4", "100")
- Diameters (e.g., "Ø25", "⌀12.5", "DIA 10")
- Radii (e.g., "R5", "R2.5")
- Angles (e.g., "45°", "90°")
- Tolerances (e.g., "12.50 ±0.05", "25.0 +0.1/-0.05")
- Thread callouts (e.g., "M8x1.25", "1/4-20")
- Depth callouts (e.g., "↧10", "DEPTH 5")
- Chamfers (e.g., "C1", "45° x 2")

WHAT TO IGNORE (not dimensions):
- Part numbers (e.g., "PN-12345", "PART NO.")
- Revision letters (e.g., "REV A", "REV B")  
- Drawing numbers
- Scale indicators (e.g., "SCALE 2:1")
- Company names
- Title block text
- Notes and annotations that are not measurements
- Zone/grid references (e.g., "A1", "B3", "ZONE C")
- Material specifications
- Surface finish symbols without dimensions

RULES:
1. Extract the EXACT text as it appears on the drawing
2. Include any symbols (Ø, R, ±, °) that are part of the dimension
3. Include tolerance values if they are attached to the dimension
4. Do NOT infer or calculate any values
5. If you cannot clearly read a dimension, do not include it

Return a JSON object with this exact structure:
{
    "dimensions": ["12.50", "Ø25.00 ±0.05", "R5", "45°", "M8x1.25"]
}

If no dimensions are found, return:
{
    "dimensions": []
}

Return ONLY the JSON object, no other text."""
    
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
            Grid info dict or None if no grid detected:
            {
                "columns": ["A", "B", "C", "D", "E", "F", "G", "H"],
                "rows": ["1", "2", "3", "4"],
                "boundaries": {
                    "column_edges": [0, 125, 250, ...],  # Normalized x positions
                    "row_edges": [0, 250, 500, ...]      # Normalized y positions
                }
            }
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
