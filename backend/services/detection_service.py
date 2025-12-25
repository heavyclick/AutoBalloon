"""
Detection Service
Orchestrates OCR + Gemini Vision fusion for accurate dimension detection.

ARCHITECTURAL FIX: "Geometric Fusion"
1. Identification: Uses Weighted Token Matching to find the "Anchor" box (the numeric value).
2. Geometry: Scans for nearby "Modifier" boxes (e.g., "2x", "TYP") that OCR separated.
3. Fusion: Merges the anchor and modifier bounding boxes into a single semantic zone.
"""
import re
from typing import Optional
from difflib import SequenceMatcher

from services.ocr_service import OCRService, OCRDetection, create_ocr_service
from services.vision_service import VisionService, create_vision_service
from models import Dimension, BoundingBox, ErrorCode

class DetectionServiceError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

class DetectionService:
    def __init__(
        self, 
        ocr_service: Optional[OCRService] = None,
        vision_service: Optional[VisionService] = None
    ):
        self.ocr_service = ocr_service
        self.vision_service = vision_service
    
    async def detect_dimensions(
        self,
        image_bytes: bytes,
        image_width: int,
        image_height: int
    ) -> list[Dimension]:
        
        # 1. Get raw OCR blocks
        ocr_detections = await self._run_ocr(image_bytes, image_width, image_height)
        
        # 2. Get semantic values from Gemini (e.g., "Ø7.5 (2x)")
        dimension_values = await self._run_gemini(image_bytes)
        
        # 3. Match AND Merge (The Fix)
        matched_dimensions = self._match_dimensions(ocr_detections, dimension_values)
        
        # 4. Sort and assign IDs
        sorted_dimensions = self._sort_reading_order(matched_dimensions)
        final_dimensions = []
        for idx, dim in enumerate(sorted_dimensions, start=1):
            dim.id = idx
            final_dimensions.append(dim)
        
        return final_dimensions
    
    async def _run_ocr(self, image_bytes: bytes, image_width: int, image_height: int) -> list[OCRDetection]:
        if not self.ocr_service:
            return []
        try:
            detections = await self.ocr_service.detect_text(image_bytes, image_width, image_height)
            return self.ocr_service.group_adjacent_text(detections)
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    async def _run_gemini(self, image_bytes: bytes) -> list[str]:
        if not self.vision_service:
            return []
        try:
            return await self.vision_service.identify_dimensions(image_bytes)
        except Exception as e:
            print(f"Gemini error: {e}")
            return []
    
    def _match_dimensions(
        self, 
        ocr_detections: list[OCRDetection],
        gemini_dimensions: list[str]
    ) -> list[Dimension]:
        matched = []
        used_ocr_indices = set()
        
        for dim_value in gemini_dimensions:
            # Step A: Find the "Anchor" (The main number, e.g., "7.5")
            # We use Weighted Token matching because it's robust against OCR errors
            match_result = self._find_best_ocr_match(
                dim_value, 
                ocr_detections, 
                used_ocr_indices
            )
            
            if match_result:
                anchor_ocr, match_confidence = match_result
                used_ocr_indices.add(id(anchor_ocr))
                
                # Step B: GEOMETRIC FUSION
                # Check if we left any modifiers (like "2x") behind in nearby boxes
                final_box = self._merge_nearby_modifiers(
                    anchor_ocr, 
                    dim_value, 
                    ocr_detections, 
                    used_ocr_indices
                )
                
                matched.append(Dimension(
                    id=0,
                    value=dim_value, 
                    zone=None,
                    bounding_box=BoundingBox(**final_box),
                    confidence=anchor_ocr.confidence * match_confidence
                ))
            else:
                print(f"No OCR match found for: {dim_value}")
        
        return matched

    def _merge_nearby_modifiers(
        self, 
        anchor: OCRDetection, 
        full_text: str, 
        all_detections: list[OCRDetection], 
        used_indices: set
    ) -> dict:
        """
        Scans for unused OCR boxes near the anchor that look like modifiers 
        present in the full semantic text, and merges their bounding boxes.
        """
        current_box = anchor.bounding_box.copy()
        
        # Quick check: If the anchor text is almost as long as the full text, 
        # we probably don't need to merge anything.
        if len(anchor.text) >= len(full_text) - 1:
            return current_box

        # Define search radius (pixels). 
        # Adjust this based on your coordinate system normalization (usually 1000).
        # 60 units is typically enough to catch a "(2x)" sitting above/below.
        SEARCH_RADIUS_X = 100
        SEARCH_RADIUS_Y = 60 

        # Identify what modifiers we are looking for in the full text
        # e.g., if full_text is "Ø7.5 (2x)", we look for "2x"
        potential_modifiers = self._extract_modifiers(full_text)
        if not potential_modifiers:
            return current_box

        # Scan all UNUSED boxes
        for candidate in all_detections:
            if id(candidate) in used_indices:
                continue
            
            # 1. IS MODIFIER? Does this box contain one of our missing modifiers?
            clean_cand = self._simple_normalize(candidate.text)
            is_modifier = any(m in clean_cand for m in potential_modifiers)
            
            # Also catch generic modifiers even if not explicitly in text (safety net)
            if not is_modifier and self._is_generic_modifier(clean_cand):
                is_modifier = True

            if is_modifier:
                # 2. IS NEARBY? Check geometric proximity
                # We check center-to-center distance
                c_box = candidate.bounding_box
                dx = abs(c_box['left'] + c_box['width']/2 - (current_box['left'] + current_box['width']/2))
                dy = abs(c_box['top'] + c_box['height']/2 - (current_box['top'] + current_box['height']/2))
                
                if dx < SEARCH_RADIUS_X and dy < SEARCH_RADIUS_Y:
                    # MERGE!
                    used_indices.add(id(candidate)) # Mark as consumed
                    
                    # Calculate union of rectangles
                    new_left = min(current_box['left'], c_box['left'])
                    new_top = min(current_box['top'], c_box['top'])
                    new_right = max(current_box['left'] + current_box['width'], c_box['left'] + c_box['width'])
                    new_bottom = max(current_box['top'] + current_box['height'], c_box['top'] + c_box['height'])
                    
                    current_box['left'] = new_left
                    current_box['top'] = new_top
                    current_box['width'] = new_right - new_left
                    current_box['height'] = new_bottom - new_top

        return current_box

    def _extract_modifiers(self, text: str) -> list[str]:
        """Extracts likely modifier strings from the full Gemini text"""
        # Regex for common modifiers: (2x), 2X, TYP, REF, C/C, M8, etc.
        # We strip them to their core for easier matching
        modifiers = re.findall(r'\(?\d+x\)?|typ|ref|bsc|c/c|b\.c\.|max|min|thru|deep', text.lower())
        return [m.replace('(', '').replace(')', '') for m in modifiers]

    def _is_generic_modifier(self, text: str) -> bool:
        """Helper to identify if an isolated OCR box is likely a modifier"""
        return bool(re.fullmatch(r'\(?\d+x\)?|typ|ref|c/c|b\.c\.|max|min|thru|deep', text))

    def _find_best_ocr_match(
        self,
        gemini_text: str,
        ocr_detections: list[OCRDetection],
        used_indices: set
    ) -> Optional[tuple[OCRDetection, float]]:
        """
        Uses Weighted Token Matching to find the 'Anchor' box.
        """
        best_match = None
        best_score = -1.0
        
        gemini_tokens = self._tokenize(gemini_text)
        
        for ocr in ocr_detections:
            if id(ocr) in used_indices:
                continue
            
            ocr_tokens = self._tokenize(ocr.text)
            score = self._calculate_weighted_score(gemini_tokens, ocr_tokens)
            
            # Threshold: 5.0 implies at least one number or significant token matched
            if score > best_score and score >= 5.0:
                best_score = score
                best_match = ocr
        
        # Fallback for severe OCR fragmentation (no clear anchor tokens)
        if not best_match:
            return self._fallback_fuzzy_match(gemini_text, ocr_detections, used_indices)

        normalized_confidence = min(best_score / 20.0, 1.0)
        return (best_match, normalized_confidence)

    def _tokenize(self, text: str) -> list[str]:
        clean_text = text.lower().replace(',', '.')
        tokens = re.split(r'[^a-z0-9.]+', clean_text)
        return [t for t in tokens if t]

    def _calculate_weighted_score(self, gemini_tokens: list[str], ocr_tokens: list[str]) -> float:
        score = 0.0
        for g_token in gemini_tokens:
            if g_token in ocr_tokens:
                if self._is_numeric(g_token):
                    score += 10.0 # It's a number -> Anchor found!
                elif self._is_mixed_code(g_token):
                    score += 8.0  # It's a code (M8) -> Strong match
                else:
                    score += 1.0  # It's a modifier -> Weak match
            else:
                for o_token in ocr_tokens:
                    if g_token in o_token or o_token in g_token:
                        if self._is_numeric(g_token): score += 5.0
                        else: score += 0.5
        return score

    def _is_numeric(self, token: str) -> bool:
        try:
            float(token)
            return True
        except ValueError:
            return False

    def _is_mixed_code(self, token: str) -> bool:
        return any(c.isalpha() for c in token) and any(c.isdigit() for c in token)

    def _fallback_fuzzy_match(self, target, candidates, used_indices):
        best_match = None
        best_score = 0.0
        norm_target = self._simple_normalize(target)
        for ocr in candidates:
            if id(ocr) in used_indices: continue
            score = SequenceMatcher(None, norm_target, self._simple_normalize(ocr.text)).ratio()
            if score > best_score and score > 0.85: # Strict fallback
                best_score = score
                best_match = ocr
        if best_match: return (best_match, best_score)
        return None

    def _simple_normalize(self, text: str) -> str:
        return re.sub(r'\s+', '', text.lower().replace('ø', '').replace('°', ''))

    def _sort_reading_order(self, dimensions: list[Dimension]) -> list[Dimension]:
        if not dimensions: return []
        band_height = 100 
        return sorted(dimensions, key=lambda d: (d.bounding_box.center_y // band_height, d.bounding_box.center_x))

def create_detection_service(ocr_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None) -> DetectionService:
    ocr_service = None if not ocr_api_key else create_ocr_service(ocr_api_key)
    vision_service = None if not gemini_api_key else create_vision_service(gemini_api_key)
    return DetectionService(ocr_service=ocr_service, vision_service=vision_service)
