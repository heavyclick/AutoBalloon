"""
Region Detection Endpoint - Full Pipeline Integration
POST /api/detect-region

Uses the SAME detection pipeline as full-page detection:
1. OCR Service (Google Vision) - get raw text tokens
2. Intelligent Grouping - combine modifiers, tolerances, compounds
3. Gemini Vision - semantic understanding of what IS a dimension
4. Pattern Library - comprehensive validation

This ensures Add Balloon works as reliably as the main detection.
"""
import base64
import asyncio
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Import existing services - reuse everything
from services.ocr_service import OCRService, OCRDetection, create_ocr_service
from services.vision_service import VisionService, create_vision_service
from services.pattern_library import PATTERNS
from config import GOOGLE_CLOUD_API_KEY, GEMINI_API_KEY


class RegionDetectRequest(BaseModel):
    """Request body for region detection."""
    image: str  # Base64 encoded cropped image
    width: int
    height: int


class RegionDetectResponse(BaseModel):
    """Response with detected text."""
    success: bool
    detected_text: Optional[str] = None
    confidence: Optional[float] = None
    dimensions: Optional[List[dict]] = None
    error: Optional[str] = None
    # Debug info for troubleshooting
    debug: Optional[dict] = None


class RegionDetectionService:
    """
    Handles dimension detection for cropped regions.
    Uses the same pipeline as full-page detection for consistency.
    """
    
    def __init__(
        self,
        ocr_service: Optional[OCRService] = None,
        vision_service: Optional[VisionService] = None
    ):
        self.ocr_service = ocr_service
        self.vision_service = vision_service
    
    async def detect(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        include_debug: bool = False
    ) -> RegionDetectResponse:
        """
        Detect dimension text in a cropped image region.
        
        Pipeline:
        1. Run OCR to get raw tokens
        2. Group tokens intelligently (modifiers, tolerances, compounds)
        3. Run Gemini for semantic understanding
        4. Validate with pattern library
        5. Return best result
        """
        debug_info = {
            "ocr_raw": [],
            "ocr_grouped": [],
            "gemini_result": None,
            "gemini_error": None,
            "pattern_valid": False,
            "selection_reason": None
        }
        
        try:
            # ===== STEP 1: Run OCR =====
            raw_ocr = await self._run_ocr(image_bytes, width, height)
            debug_info["ocr_raw"] = [d.text for d in raw_ocr]
            
            if not raw_ocr:
                return RegionDetectResponse(
                    success=False,
                    error="No text detected in region",
                    debug=debug_info if include_debug else None
                )
            
            # ===== STEP 2: Group OCR tokens intelligently =====
            grouped_ocr = self._group_ocr(raw_ocr)
            debug_info["ocr_grouped"] = [d.text for d in grouped_ocr]
            
            # ===== STEP 3: Run Gemini for semantic understanding =====
            gemini_result = await self._run_gemini(image_bytes)
            debug_info["gemini_result"] = gemini_result
            
            # ===== STEP 4: Select best result =====
            result = self._select_best_result(
                grouped_ocr, 
                gemini_result, 
                debug_info
            )
            
            if result:
                # Validate with pattern library
                is_valid = PATTERNS.is_dimension_text(result["value"])
                debug_info["pattern_valid"] = is_valid
                
                return RegionDetectResponse(
                    success=True,
                    detected_text=result["value"],
                    confidence=result.get("confidence", 0.8),
                    dimensions=[{"value": result["value"]}],
                    debug=debug_info if include_debug else None
                )
            else:
                # No good result - return raw OCR as fallback
                fallback = self._get_fallback(raw_ocr, grouped_ocr)
                if fallback:
                    debug_info["selection_reason"] = "fallback_raw_ocr"
                    return RegionDetectResponse(
                        success=True,
                        detected_text=fallback,
                        confidence=0.5,
                        dimensions=[{"value": fallback}],
                        debug=debug_info if include_debug else None
                    )
                
                return RegionDetectResponse(
                    success=False,
                    error="Could not identify dimension in region",
                    debug=debug_info if include_debug else None
                )
                
        except Exception as e:
            debug_info["error"] = str(e)
            return RegionDetectResponse(
                success=False,
                error=f"Detection failed: {str(e)}",
                debug=debug_info if include_debug else None
            )
    
    async def _run_ocr(
        self, 
        image_bytes: bytes, 
        width: int, 
        height: int
    ) -> List[OCRDetection]:
        """Run OCR on the cropped region."""
        if not self.ocr_service:
            return []
        
        try:
            return await self.ocr_service.detect_text(image_bytes, width, height)
        except Exception as e:
            print(f"OCR error in region detection: {e}")
            return []
    
    async def _run_gemini(self, image_bytes: bytes) -> Optional[str]:
        """
        Run Gemini to semantically identify the dimension.
        Uses a simplified prompt optimized for small cropped regions.
        """
        if not self.vision_service:
            return None
        
        try:
            # Use a custom prompt for cropped regions
            result = await self._call_gemini_for_region(image_bytes)
            return result
        except Exception as e:
            print(f"Gemini error in region detection: {e}")
            return None
    
    async def _call_gemini_for_region(self, image_bytes: bytes) -> Optional[str]:
        """Call Gemini with a region-specific prompt."""
        import httpx
        import json
        
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = """You are extracting a dimension from a cropped region of an engineering drawing.

This small image contains ONE dimension or measurement. Extract it EXACTLY as shown.

RULES:
1. Keep modifiers WITH the dimension: "4X 0.2in" is ONE value, not separate
2. Keep tolerances WITH the dimension: "0.250 +0.005/-0.002" is ONE value  
3. Keep compound dimensions together: "0.188" Wd. x 7/8" Lg. Key" is ONE value
4. Include thread callouts fully: "3/4-16 UNF" or "M8x1.25"
5. Include units if shown: ", ', in, mm

Return ONLY a JSON object with this format:
{"dimension": "THE_EXACT_VALUE_HERE", "confidence": 0.9}

If no dimension is visible, return:
{"dimension": null, "confidence": 0}

Return ONLY the JSON, no other text."""

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
                "maxOutputTokens": 256,
                "responseMimeType": "application/json"
            }
        }
        
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_url}?key={GEMINI_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
        
        # Parse response
        try:
            candidates = result.get("candidates", [])
            if not candidates:
                return None
            
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            # Handle markdown code blocks
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            
            data = json.loads(text.strip())
            dimension = data.get("dimension")
            
            if dimension and isinstance(dimension, str) and dimension.strip():
                return dimension.strip()
            
            return None
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Gemini response parse error: {e}")
            return None
    
    def _group_ocr(self, detections: List[OCRDetection]) -> List[OCRDetection]:
        """
        Group OCR tokens intelligently.
        This is adapted from DetectionService._group_ocr() for consistency.
        """
        if not detections:
            return []
        
        # Sort by Y then X (reading order)
        sorted_dets = sorted(
            detections,
            key=lambda d: (d.bounding_box["ymin"], d.bounding_box["xmin"])
        )
        
        groups = []
        used = set()
        
        for i, det in enumerate(sorted_dets):
            if i in used:
                continue
            
            group = [det]
            used.add(i)
            
            # Expand group with related tokens
            self._expand_group(group, sorted_dets, used, i)
            groups.append(group)
        
        return [self._merge_group(g) for g in groups]
    
    def _expand_group(
        self,
        group: List[OCRDetection],
        all_dets: List[OCRDetection],
        used: set,
        start_idx: int
    ):
        """Expand group by finding related tokens."""
        # Thresholds (in normalized 0-1000 coordinates)
        H_THRESH = 80   # Horizontal - more lenient for cropped regions
        V_THRESH = 40   # Vertical (same line)
        V_STACK = 50    # Vertical stacking
        
        changed = True
        while changed:
            changed = False
            
            for i, det in enumerate(all_dets):
                if i in used:
                    continue
                
                for g_det in list(group):
                    if self._should_group(g_det, det, H_THRESH, V_THRESH, V_STACK):
                        group.append(det)
                        used.add(i)
                        changed = True
                        break
    
    def _should_group(
        self,
        det1: OCRDetection,
        det2: OCRDetection,
        h_thresh: int,
        v_thresh: int,
        v_stack: int
    ) -> bool:
        """Determine if two detections should be grouped."""
        import re
        
        b1 = det1.bounding_box
        b2 = det2.bounding_box
        
        # Calculate positions
        c1_x = (b1["xmin"] + b1["xmax"]) / 2
        c1_y = (b1["ymin"] + b1["ymax"]) / 2
        c2_x = (b2["xmin"] + b2["xmax"]) / 2
        c2_y = (b2["ymin"] + b2["ymax"]) / 2
        
        x_gap = b2["xmin"] - b1["xmax"]
        y_diff = abs(c2_y - c1_y)
        x_diff = abs(c2_x - c1_x)
        
        t1 = det1.text.strip()
        t2 = det2.text.strip()
        
        # Case 1: Horizontal adjacency (same line)
        if y_diff <= v_thresh and -10 <= x_gap <= h_thresh:
            return self._should_merge_horizontal(t1, t2, x_gap)
        
        # Case 2: Vertical stacking (text below)
        if x_diff <= 60 and 0 < (c2_y - c1_y) <= v_stack:
            return self._should_merge_vertical(t1, t2)
        
        return False
    
    def _should_merge_horizontal(self, prev: str, curr: str, gap: float) -> bool:
        """Should horizontally adjacent tokens merge?"""
        import re
        
        # Modifier + dimension: "4X" + "0.2in"
        if self._is_modifier(prev):
            return True
        
        # Dimension + modifier: "0.2in" + "TYP"
        if self._is_modifier(curr):
            return True
        
        # Mixed fraction: "3" + "1/4"
        if prev.isdigit() and re.match(r'^\d+/\d+["\']?$', curr):
            return True
        
        # Fraction + unit: "1/4" + '"'
        if re.match(r'^\d+/\d+$', prev) and curr in ['"', "'", "in", "mm"]:
            return True
        
        # Tolerance: dimension + "+0.005" or "-0.003"
        if PATTERNS.is_tolerance(curr):
            return True
        
        # Compound connectors
        if re.match(r'^(?:x|X|×|Wd\.?|Lg\.?|Key|OD|ID|Pitch|Teeth)$', curr, re.IGNORECASE):
            return True
        
        # After connector
        if prev.lower() in ['x', '×', 'wd.', 'wd', 'lg.', 'lg', 'for', 'pitch', 'teeth']:
            return True
        
        # Thread parts
        if re.match(r'^(?:UN[CF]?|UNF|UNC|NPT|SAE|\(SAE\)|Thread|THD)$', curr, re.IGNORECASE):
            return True
        
        # Continuation chars
        if curr in ['-', '/', '(', ')', ':', '"', "'"]:
            return True
        if prev in ['-', '/', ':', 'For', 'for', '#']:
            return True
        
        # Unit after number
        if re.match(r'^[\d.]+$', prev) and curr.lower() in ['in', 'mm', 'cm', '"', "'", 'deg']:
            return True
        
        # Number after number with small gap (like "0.080" + "in")
        if gap <= 30:
            return True
        
        return gap <= 40
    
    def _should_merge_vertical(self, upper: str, lower: str) -> bool:
        """Should vertically stacked tokens merge?"""
        import re
        
        # Tolerance below dimension
        if PATTERNS.is_tolerance(lower):
            return True
        
        # Descriptive labels
        if re.match(r'^(?:Flange|Tube|OD|ID|Pipe|Thread|Pitch|Teeth|Key|Lg|Wd)\.?$', lower, re.IGNORECASE):
            return True
        
        return False
    
    def _is_modifier(self, text: str) -> bool:
        """Is this a quantity/type modifier?"""
        import re
        text = text.strip()
        patterns = [
            r'^\d+[xX]$',           # 4X, 2X
            r'^[xX]\d+$',           # x4, x2
            r'^\(\d+[xX]\)$',       # (4X)
            r'^TYP\.?$',            # TYP
            r'^REF\.?$',            # REF
            r'^For$',               # For
        ]
        return any(re.match(p, text, re.IGNORECASE) for p in patterns)
    
    def _merge_group(self, group: List[OCRDetection]) -> OCRDetection:
        """Merge a group of detections into one."""
        if len(group) == 1:
            return group[0]
        
        # Sort by position
        group.sort(key=lambda d: (d.bounding_box["ymin"], d.bounding_box["xmin"]))
        
        # Build text with appropriate spacing
        parts = []
        for i, det in enumerate(group):
            text = det.text.strip()
            
            if i > 0:
                prev = group[i-1]
                y_gap = det.bounding_box["ymin"] - prev.bounding_box["ymax"]
                x_gap = det.bounding_box["xmin"] - prev.bounding_box["xmax"]
                prev_text = prev.text.strip()
                
                # Determine if we need a space
                need_space = False
                
                if y_gap > 15:
                    # Vertical gap - add space
                    need_space = True
                elif x_gap > 20:
                    # Horizontal gap - add space
                    need_space = True
                elif prev_text and prev_text[-1] not in '/-(':
                    # No space after certain chars
                    if text and text[0] not in '/"\'-)':
                        need_space = True
                
                if need_space:
                    parts.append(" ")
            
            parts.append(text)
        
        merged_text = "".join(parts)
        
        # Clean up common issues
        merged_text = merged_text.replace("  ", " ").strip()
        
        merged_box = {
            "xmin": min(d.bounding_box["xmin"] for d in group),
            "xmax": max(d.bounding_box["xmax"] for d in group),
            "ymin": min(d.bounding_box["ymin"] for d in group),
            "ymax": max(d.bounding_box["ymax"] for d in group),
        }
        
        return OCRDetection(
            text=merged_text,
            bounding_box=merged_box,
            confidence=sum(d.confidence for d in group) / len(group)
        )
    
    def _select_best_result(
        self,
        grouped_ocr: List[OCRDetection],
        gemini_result: Optional[str],
        debug_info: dict
    ) -> Optional[dict]:
        """
        Select the best result from available candidates.
        
        Priority:
        1. Gemini result (if valid dimension)
        2. Best grouped OCR (if valid dimension)
        3. Longest grouped OCR with digits
        """
        
        # === Priority 1: Gemini result ===
        if gemini_result:
            # Validate with pattern library
            if PATTERNS.is_dimension_text(gemini_result):
                debug_info["selection_reason"] = "gemini_valid_pattern"
                return {"value": gemini_result, "confidence": 0.95}
            
            # Even if pattern doesn't match, if Gemini returned something
            # and it has digits, trust it (Gemini has semantic understanding)
            if any(c.isdigit() for c in gemini_result):
                debug_info["selection_reason"] = "gemini_has_digits"
                return {"value": gemini_result, "confidence": 0.85}
        
        # === Priority 2: Best grouped OCR ===
        valid_ocr = []
        for ocr in grouped_ocr:
            text = ocr.text.strip()
            if PATTERNS.is_dimension_text(text):
                valid_ocr.append({
                    "value": text,
                    "confidence": ocr.confidence,
                    "length": len(text)
                })
        
        if valid_ocr:
            # Sort by confidence, then by length (prefer longer/more complete)
            valid_ocr.sort(key=lambda x: (-x["confidence"], -x["length"]))
            debug_info["selection_reason"] = "ocr_valid_pattern"
            return valid_ocr[0]
        
        # === Priority 3: Any OCR with digits ===
        for ocr in grouped_ocr:
            text = ocr.text.strip()
            if any(c.isdigit() for c in text) and len(text) >= 2:
                debug_info["selection_reason"] = "ocr_has_digits"
                return {"value": text, "confidence": 0.6}
        
        return None
    
    def _get_fallback(
        self,
        raw_ocr: List[OCRDetection],
        grouped_ocr: List[OCRDetection]
    ) -> Optional[str]:
        """Get a fallback value if all else fails."""
        
        # Try grouped first
        for ocr in grouped_ocr:
            text = ocr.text.strip()
            if any(c.isdigit() for c in text):
                return text
        
        # Try raw concatenation
        all_text = " ".join(d.text.strip() for d in raw_ocr if d.text.strip())
        if any(c.isdigit() for c in all_text):
            return all_text
        
        return None


# ===== Singleton instance for reuse =====
_region_service: Optional[RegionDetectionService] = None


def get_region_detection_service() -> RegionDetectionService:
    """Get or create the region detection service."""
    global _region_service
    
    if _region_service is None:
        ocr_service = None
        vision_service = None
        
        if GOOGLE_CLOUD_API_KEY:
            try:
                ocr_service = create_ocr_service(GOOGLE_CLOUD_API_KEY)
            except Exception as e:
                print(f"Failed to create OCR service: {e}")
        
        if GEMINI_API_KEY:
            try:
                vision_service = create_vision_service(GEMINI_API_KEY)
            except Exception as e:
                print(f"Failed to create Vision service: {e}")
        
        _region_service = RegionDetectionService(
            ocr_service=ocr_service,
            vision_service=vision_service
        )
    
    return _region_service


# ===== Main endpoint function =====
async def detect_region(request: RegionDetectRequest) -> RegionDetectResponse:
    """
    Detect dimension text in a cropped image region.
    
    This endpoint is called when a user draws a rectangle in Add Balloon mode.
    It uses the full detection pipeline (OCR + Gemini + Patterns) for accuracy.
    """
    try:
        # Decode the image
        try:
            image_bytes = base64.b64decode(request.image)
        except Exception as e:
            return RegionDetectResponse(
                success=False,
                error=f"Invalid image data: {str(e)}"
            )
        
        # Validate image size
        if len(image_bytes) < 100:
            return RegionDetectResponse(
                success=False,
                error="Image too small - please draw a larger region"
            )
        
        # Get the detection service
        service = get_region_detection_service()
        
        # Check if services are available
        if not service.ocr_service and not service.vision_service:
            return RegionDetectResponse(
                success=False,
                error="Detection services not configured. Check API keys."
            )
        
        # Run detection with debug info for troubleshooting
        result = await service.detect(
            image_bytes=image_bytes,
            width=request.width,
            height=request.height,
            include_debug=True  # Always include for now, can disable in production
        )
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return RegionDetectResponse(
            success=False,
            error=f"Detection error: {str(e)}"
        )


# ===== FastAPI Router (optional - for modular setup) =====
def create_router():
    """Create a FastAPI router for this endpoint."""
    from fastapi import APIRouter
    
    router = APIRouter()
    
    @router.post("/detect-region", response_model=RegionDetectResponse)
    async def detect_region_endpoint(request: RegionDetectRequest):
        return await detect_region(request)
    
    return router
