"""
Vision Service - Enhanced for AS9102/ISO 13485 compliance
Integrates with Gemini Vision API for semantic understanding of manufacturing drawings.

CRITICAL FIX: Prompt now explicitly tells Gemini to NEVER split compound dimensions
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
                "temperature": 0.1,
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
        """Build the prompt for dimension identification."""
        return """You are an expert manufacturing engineer extracting dimensions from technical drawings for AS9102 First Article Inspection.

## YOUR TASK
Extract ALL dimensions from this drawing. Return each dimension EXACTLY as it appears, including all modifiers and tolerances.

## CRITICAL RULES - READ CAREFULLY

### RULE 1: NEVER SPLIT COMPOUND DIMENSIONS
These must be returned as ONE single entry:
- "0.188" Wd. x 7/8" Lg. Key" → ONE entry (not split into "0.188" Wd." and "7/8" Lg.")
- "0.2500in -0.0015 -0.0030" → ONE entry (dimension with tolerances)
- "1.25in Usable Length Range Min." → ONE entry
- "Usable Length Range Max.: 1 3/4"" → ONE entry

### RULE 2: KEEP MIXED FRACTIONS TOGETHER
- "3 1/4"" → ONE entry (not "3" and "1/4"")
- "4 7/8"" → ONE entry
- "3 3/4"" → ONE entry

### RULE 3: INCLUDE TOLERANCE STACKS
When you see a dimension followed by tolerance values on the same line:
- "0.2500in -0.0015 -0.0030" → include ALL of it as ONE dimension
- "15.3 +0.1/-0" → ONE entry
- "25 ±0.5" → ONE entry

### RULE 4: INCLUDE ALL MODIFIERS
- Thread callouts: "6-32 Thread", "3/4"-16 UN/UNF (SAE)", "M8x1.25"
- Quantity markers: "Ø3.4 (2x)", "R5 TYP", "6X 6-32"
- Reference markers: "0.95 REF", "25 NOM", "45° BSC"
- Limit markers: "15 MAX", "3 MIN"
- Depth/through: "Ø6 THRU", "Ø5 ↧10"

### RULE 5: SAME VALUE IN DIFFERENT LOCATIONS = SEPARATE ENTRIES
If "16mm" appears twice in different parts of the drawing, return it TWICE:
["16mm", "16mm"]

## WHAT TO EXTRACT
- Linear dimensions with units (0.75in, 32mm, 1.95in)
- Fractions and mixed fractions (1/4", 3 1/4", 4 7/8")
- Toleranced dimensions (0.2500in -0.0015 -0.0030)
- Compound dimensions (0.188" Wd. x 7/8" Lg. Key)
- Diameters and radii (Ø5, R2.5)
- Thread callouts (6-32, M8x1.25, 3/4"-16 UN/UNF)
- Angles (45°, 89.5°)
- Text notes with dimensions (Usable Length Range Max.: 1 3/4")

## WHAT TO IGNORE
- Part numbers (PN-12345, 91388A212, 6296K81)
- Company names (McMaster-Carr)
- Drawing titles
- Revision marks
- Scale indicators
- Zone letters/numbers at borders

## EXAMPLES

Input drawing shows: "0.188" Wd. x 7/8" Lg. Key"
✓ CORRECT: ["0.188\" Wd. x 7/8\" Lg. Key"]
✗ WRONG: ["0.188\" Wd.", "7/8\" Lg."]

Input drawing shows: "0.2500in" with "-0.0015" and "-0.0030" next to it
✓ CORRECT: ["0.2500in -0.0015 -0.0030"]
✗ WRONG: ["0.2500in", "-0.0015", "-0.0030"]

Input drawing shows: "3 1/4"" dimension
✓ CORRECT: ["3 1/4\""]
✗ WRONG: ["3", "1/4\""]

Input drawing shows "16mm" in two different places
✓ CORRECT: ["16mm", "16mm"]
✗ WRONG: ["16mm"]

## RESPONSE FORMAT
Return ONLY a JSON object:
{
    "dimensions": ["0.75in", "3 1/4\"", "0.2500in -0.0015 -0.0030", "0.188\" Wd. x 7/8\" Lg. Key"]
}

If no dimensions found:
{
    "dimensions": []
}"""
    
    def _parse_dimension_response(self, response: dict) -> list[str]:
        """Parse Gemini's response and extract dimension values"""
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
        """Detect grid reference system on the drawing."""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = """Analyze this engineering drawing and identify the grid reference system if present.

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
