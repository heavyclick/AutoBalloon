"""
Detection Service - AS9102 Compliant Dimension Detection (REPAIRED)
Orchestrates OCR + Gemini Vision fusion for accurate dimension detection.

FIXES APPLIED:
1. Relaxed distance matching (100 -> 150) to catch fuzzy Gemini coordinates.
2. Lowered fallback confidence (0.9 -> 0.75) so unmatched Gemini items are kept.
3. Smarter Vertical Grouping: Prevents merging distinct features like "21 Teeth" and "0.080in Pitch".
"""
import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from datetime import datetime

from services.ocr_service import OCRService, OCRDetection, create_ocr_service
from services.vision_service import VisionService, create_vision_service
from services.file_service import FileService, PageImage, FileProcessingResult
from services.pattern_library import PATTERNS
from models.schemas import Dimension, BoundingBox, ErrorCode


# Debug storage
DEBUG_LOG = []
MAX_DEBUG_ENTRIES = 10


def get_debug_log():
    return DEBUG_LOG


def add_debug_entry(entry: dict):
    global DEBUG_LOG
    entry['timestamp'] = datetime.utcnow().isoformat()
    DEBUG_LOG.append(entry)
    if len(DEBUG_LOG) > MAX_DEBUG_ENTRIES:
        DEBUG_LOG = DEBUG_LOG[-MAX_DEBUG_ENTRIES:]


@dataclass
class GeminiDimension:
    """Dimension from Gemini with location."""
    value: str
    x_percent: float
    y_percent: float
    confidence: float


@dataclass
class PageDetectionResult:
    page_number: int
    dimensions: List[Dimension]
    grid_detected: bool
    image_base64: str
    width: int
    height: int


@dataclass
class MultiPageDetectionResult:
    success: bool
    total_pages: int
    pages: List[PageDetectionResult]
    all_dimensions: List[Dimension]
    error_message: Optional[str] = None


class DetectionService:
    """AS9102-compliant dimension detection."""
    
    STANDARD_GRID_COLUMNS = ['H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
    STANDARD_GRID_ROWS = ['4', '3', '2', '1']
    
    # Patterns for dimension modifiers that should stay attached
    MODIFIER_PATTERNS = [
        r'^\d+[xX]$',           # 4X, 2X
        r'^[xX]\d+$',           # x4, x2
        r'^\(\d+[xX]\)$',       # (4X)
        r'^TYP\.?$',            # TYP
        r'^REF\.?$',            # REF
    ]
    
    # FIX: Descriptive phrase starters
    DESCRIPTION_STARTERS = ['for', 'max', 'min', 'typ', 'ref', 'approx', 'nominal']
    
    # FIX: Phrase terminators
    PHRASE_TERMINATORS = ['width', 'length', 'diameter', 'depth', 'height', 'od', 'id', 
                          'dia', 'thk', 'thickness', 'travel', 'shaft', 'bore', 'thread']
    
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
        """Detect dimensions from PDF or image."""
        debug_entry = {'filename': filename, 'pages': []}
        
        file_result = self.file_service.process_file(file_bytes, filename)
        
        if not file_result.success:
            debug_entry['error'] = file_result.error_message
            add_debug_entry(debug_entry)
            return MultiPageDetectionResult(
                success=False, total_pages=0, pages=[], all_dimensions=[],
                error_message=file_result.error_message
            )
        
        page_results = []
        current_id = 1
        
        for page_image in file_result.pages:
            page_debug = {'page_number': page_image.page_number}
            
            dimensions, debug_info = await self._detect_on_page(
                page_image.image_bytes,
                page_image.width,
                page_image.height
            )
            
            page_debug.update(debug_info)
            
            for dim in dimensions:
                dim.zone = self._calculate_zone(
                    dim.bounding_box.center_x,
                    dim.bounding_box.center_y
                )
                dim.id = current_id
                dim.page = page_image.page_number
                current_id += 1
            
            page_debug['final_dimensions'] = [
                {'id': d.id, 'value': d.value, 'zone': d.zone} 
                for d in dimensions
            ]
            debug_entry['pages'].append(page_debug)
            
            page_results.append(PageDetectionResult(
                page_number=page_image.page_number,
                dimensions=dimensions,
                grid_detected=True,
                image_base64=page_image.base64_image,
                width=page_image.width,
                height=page_image.height
            ))
        
        all_dims = []
        for pr in page_results:
            all_dims.extend(pr.dimensions)
        
        debug_entry['total_dimensions'] = len(all_dims)
        add_debug_entry(debug_entry)
        
        return MultiPageDetectionResult(
            success=True,
            total_pages=file_result.total_pages,
            pages=page_results,
            all_dimensions=all_dims
        )
    
    async def _detect_on_page(
        self,
        image_bytes: bytes,
        width: int,
        height: int
    ) -> Tuple[List[Dimension], dict]:
        """Detect dimensions on single page."""
        debug = {}
        
        # 1. Get raw OCR
        raw_ocr = await self._run_ocr(image_bytes, width, height)
        debug['raw_ocr_count'] = len(raw_ocr)
        
        # Calculate dynamic metrics
        avg_height = self._calculate_avg_char_height(raw_ocr)
        debug['avg_char_height'] = avg_height
        
        # 2. Group OCR intelligently
        grouped_ocr = self._group_ocr(raw_ocr, avg_height)
        debug['grouped_ocr_count'] = len(grouped_ocr)
        debug['grouped_ocr'] = [d.text for d in grouped_ocr]
        
        # 3. Get Gemini dimensions with locations
        gemini_dims = await self._run_gemini(image_bytes)
        debug['gemini_dimensions'] = [
            {'value': d.value, 'x': d.x_percent, 'y': d.y_percent}
            for d in gemini_dims
        ]
        
        # 4. Match using LOCATION-FIRST strategy
        matched = self._match_by_location(grouped_ocr, raw_ocr, gemini_dims, avg_height)
        debug['matched_count'] = len(matched)
        
        # 5. Sort reading order
        sorted_dims = self._sort_reading_order(matched)
        
        return sorted_dims, debug
    
    def _calculate_avg_char_height(self, detections: List[OCRDetection]) -> float:
        """Calculate the average height of text characters on the page."""
        if not detections:
            return 10.0
            
        heights = []
        for d in detections:
            h = d.bounding_box["ymax"] - d.bounding_box["ymin"]
            if 5 < h < 200:
                heights.append(h)
        
        if not heights:
            return 10.0
            
        return sum(heights) / len(heights)

    async def _run_ocr(self, image_bytes: bytes, w: int, h: int) -> List[OCRDetection]:
        """Run OCR."""
        if not self.ocr_service:
            return []
        try:
            return await self.ocr_service.detect_text(image_bytes, w, h)
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    async def _run_gemini(self, image_bytes: bytes) -> List[GeminiDimension]:
        """Run Gemini with locations."""
        if not self.vision_service:
            return []
        try:
            results = await self.vision_service.identify_dimensions_with_locations(image_bytes)
            return [
                GeminiDimension(
                    value=d['value'],
                    x_percent=d.get('x', 50),
                    y_percent=d.get('y', 50),
                    confidence=d.get('confidence', 0.8)
                )
                for d in results
            ]
        except Exception as e:
            print(f"Gemini error: {e}")
            return []
    
    def _group_ocr(self, detections: List[OCRDetection], avg_height: float = 10.0) -> List[OCRDetection]:
        """
        Group OCR tokens using dynamic thresholds based on text size.
        """
        if not detections:
            return []
        
        # Sort by Y then X
        sorted_dets = sorted(
            detections,
            key=lambda d: (d.bounding_box["ymin"], d.bounding_box["xmin"])
        )
        
        # Dynamic thresholds
        H_THRESH = max(40, int(avg_height * 3.0))    
        V_THRESH = int(avg_height * 0.6)    
        V_STACK = int(avg_height * 2.5)     
        
        groups = []
        used = set()
        
        for i, det in enumerate(sorted_dets):
            if i in used:
                continue
            
            group = [det]
            used.add(i)
            
            self._expand_group_with_phrases(group, sorted_dets, used, H_THRESH, V_THRESH, V_STACK)
            groups.append(group)
        
        return [self._merge_group(g) for g in groups]
    
    def _expand_group_with_phrases(
        self,
        group: List[OCRDetection],
        all_dets: List[OCRDetection],
        used: set,
        h_thresh: int,
        v_thresh: int,
        v_stack: int
    ):
        """Expand group by finding related tokens."""
        changed = True
        in_description_phrase = False 
        
        while changed:
            changed = False
            
            for i, det in enumerate(all_dets):
                if i in used:
                    continue
                
                for g_det in list(group):
                    should_merge, starts_phrase = self._should_group_improved(
                        g_det, det, h_thresh, v_thresh, v_stack, in_description_phrase
                    )
                    
                    if should_merge:
                        group.append(det)
                        used.add(i)
                        changed = True
                        
                        if starts_phrase:
                            in_description_phrase = True
                        
                        if self._ends_description_phrase(det.text):
                            in_description_phrase = False
                        
                        break
    
    def _should_group_improved(
        self,
        det1: OCRDetection,
        det2: OCRDetection,
        h_thresh: int,
        v_thresh: int,
        v_stack: int,
        in_description_phrase: bool
    ) -> Tuple[bool, bool]:
        """Determine if two detections should be grouped."""
        b1 = det1.bounding_box
        b2 = det2.bounding_box
        
        c1_x = (b1["xmin"] + b1["xmax"]) / 2
        c1_y = (b1["ymin"] + b1["ymax"]) / 2
        c2_x = (b2["xmin"] + b2["xmax"]) / 2
        c2_y = (b2["ymin"] + b2["ymax"]) / 2
        
        x_gap = b2["xmin"] - b1["xmax"]
        y_diff = abs(c2_y - c1_y)
        x_diff = abs(c2_x - c1_x)
        
        t1 = det1.text.strip()
        t2 = det2.text.strip()
        
        # Horizontal adjacency
        if y_diff <= v_thresh and -5 <= x_gap <= h_thresh:
            merge, starts = self._should_merge_horizontal_improved(t1, t2, x_gap, in_description_phrase)
            return merge, starts
        
        # Vertical stacking
        if x_diff <= h_thresh * 1.5 and 0 < (c2_y - c1_y) <= v_stack:
            merge, starts = self._should_merge_vertical_improved(t1, t2, in_description_phrase)
            return merge, starts
        
        return False, False
    
    def _should_merge_horizontal_improved(
        self, 
        prev: str, 
        curr: str, 
        gap: float,
        in_description_phrase: bool
    ) -> Tuple[bool, bool]:
        """Should horizontally adjacent tokens merge?"""
        prev_last = prev.strip().split()[-1] if prev.strip() else ""
        curr_first = curr.strip().split()[0] if curr.strip() else ""
        curr_lower = curr.lower().strip()
        
        if in_description_phrase:
            if self._ends_description_phrase(curr):
                return True, False
            if gap <= 50: # Allow relaxed gap in phrases
                return True, False
        
        if curr_lower in self.DESCRIPTION_STARTERS:
            if self._looks_like_dimension(prev_last) or self._is_measurement_related(prev_last):
                return True, True
        
        # Modifier check
        if self._is_modifier(prev_last) and self._looks_like_dimension(curr):
            return True, False
        
        if self._looks_like_dimension(prev_last) and self._is_modifier(curr):
            return True, False
            
        # Connectors & Pitch Diameter
        connectors = ['x', '×', 'wd', 'lg', 'pitch', 'teeth', 'diameter', 'dia', 'major', 'minor']
        if prev_last.lower() in connectors:
            return True, False
            
        if re.match(r'^(?:x|X|×|Wd\.?|Lg\.?|Key|OD|ID|Pitch|Teeth|Diameter|Dia\.?|Major|Minor)$', curr, re.IGNORECASE):
            return True, False
        
        # Units
        if re.match(r'^[\d.]+$', prev_last) and curr.lower() in ['in', 'mm', '"', "'", "deg"]:
            return True, False
        
        # Small gap simple merge (but don't merge two complete dims)
        if gap <= 15:
            if not (self._is_complete_dim(prev) and self._is_complete_dim(curr)):
                return True, False
        
        return False, False
    
    def _should_merge_vertical_improved(
        self, 
        upper: str, 
        lower: str,
        in_description_phrase: bool
    ) -> Tuple[bool, bool]:
        """Should vertically stacked tokens merge?"""
        upper_clean = upper.strip()
        lower_first = lower.strip().split()[0].lower() if lower.strip() else ""
        
        # FIX: Don't merge if upper is ALREADY a complete feature (e.g. "21 Teeth")
        # unless lower explicitly connects (e.g. "Pitch")
        if self._is_complete_feature(upper_clean):
            # Only merge if lower is a tolerance or "For" context
            if PATTERNS.is_tolerance(lower):
                return True, False
            # If upper is "21 Teeth", don't merge "Pitch" below it arbitrarily
            # Only merge if it's "For..."
            if lower_first in ['for']:
                return True, True
            return False, False

        # Tolerance
        if PATTERNS.is_tolerance(lower):
            return True, False
        
        # Descriptive labels
        if re.match(r'^(?:Flange|Tube|OD|ID|Pipe|Thread|For|Pitch|Teeth|Max|Min|Typ|Diameter|Dia\.?|Major|Minor)$', lower, re.IGNORECASE):
            return True, False
        
        return False, False
    
    def _is_measurement_related(self, text: str) -> bool:
        text = text.lower().strip()
        measurement_words = [
            'teeth', 'tooth', 'pitch', 'places', 'holes', 'slots',
            'threads', 'flange', 'tube', 'shaft', 'bore', 'key',
            'od', 'id', 'dia', 'diameter', 'depth', 'width', 'length',
            'height', 'thk', 'thickness', 'travel', 'max', 'min'
        ]
        return text in measurement_words
    
    def _ends_description_phrase(self, text: str) -> bool:
        text_clean = re.sub(r'[.,;:]+$', '', text.lower().strip())
        for terminator in self.PHRASE_TERMINATORS:
            if text_clean == terminator or text_clean.endswith(terminator):
                return True
        return False
    
    def _is_modifier(self, text: str) -> bool:
        text = text.strip()
        for pat in self.MODIFIER_PATTERNS:
            if re.match(pat, text, re.IGNORECASE):
                return True
        return False
    
    def _looks_like_dimension(self, text: str) -> bool:
        text = text.strip()
        patterns = [
            r'^\d+\.?\d*["\']?$', r'^\d+/\d+["\']?$', 
            r'^\d+\.?\d*(?:in|mm)$', r'^[ØøR]\d+'
        ]
        return any(re.match(p, text, re.IGNORECASE) for p in patterns)
    
    def _is_complete_dim(self, text: str) -> bool:
        text = text.strip()
        patterns = [
            r'^\d+\s+\d+/\d+["\']$', r'^\d+/\d+["\']$', r'^\d+\.?\d*["\']$', 
            r'^\d+\.\d{2,}(?:in|mm)?$', r'^[ØøR]\d+\.?\d*["\']?$', r'^\d+(?:\.\d+)?\s*mm$'
        ]
        return any(re.match(p, text, re.IGNORECASE) for p in patterns)

    def _is_complete_feature(self, text: str) -> bool:
        """Check if text is a standalone feature like '21 Teeth' or '0.500 in'."""
        if self._is_complete_dim(text): return True
        # Check for Number + Noun (e.g. 21 Teeth)
        if re.match(r'^\d+\s+(?:Teeth|Places|Holes|Slots|Plcs)$', text, re.IGNORECASE):
            return True
        return False
    
    def _merge_group(self, group: List[OCRDetection]) -> OCRDetection:
        if len(group) == 1: return group[0]
        group.sort(key=lambda d: (d.bounding_box["ymin"], d.bounding_box["xmin"]))
        parts = []
        for i, det in enumerate(group):
            if i > 0:
                prev = group[i-1]
                y_gap = det.bounding_box["ymin"] - prev.bounding_box["ymax"]
                x_gap = det.bounding_box["xmin"] - prev.bounding_box["xmax"]
                if y_gap > 8 or x_gap > 10: parts.append(" ")
            parts.append(det.text)
        merged_text = "".join(parts)
        merged_box = {
            "xmin": min(d.bounding_box["xmin"] for d in group),
            "xmax": max(d.bounding_box["xmax"] for d in group),
            "ymin": min(d.bounding_box["ymin"] for d in group),
            "ymax": max(d.bounding_box["ymax"] for d in group),
        }
        return OCRDetection(text=merged_text, bounding_box=merged_box, confidence=sum(d.confidence for d in group) / len(group))
    
    def _match_by_location(
        self,
        grouped_ocr: List[OCRDetection],
        raw_ocr: List[OCRDetection],
        gemini_dims: List[GeminiDimension],
        avg_height: float = 10.0
    ) -> List[Dimension]:
        matched = []
        used_ocr_ids = set()
        
        for gem in gemini_dims:
            target_x = gem.x_percent * 10
            target_y = gem.y_percent * 10
            
            # FIX: Widened search distance (was 100, now 150 min)
            max_dist = max(150, avg_height * 5.0) 
            
            best_match = None
            best_score = 0
            
            # Strategy 1: Combined
            for ocr in grouped_ocr:
                if id(ocr) in used_ocr_ids: continue
                box = ocr.bounding_box
                ocr_x = (box["xmin"] + box["xmax"]) / 2
                ocr_y = (box["ymin"] + box["ymax"]) / 2
                distance = ((ocr_x - target_x) ** 2 + (ocr_y - target_y) ** 2) ** 0.5
                text_score = self._text_similarity(gem.value, ocr.text)
                
                if text_score < 0.15: continue
                location_score = max(0, 1 - (distance / max_dist))
                
                if location_score > 0.3 and text_score > 0.3:
                    combined = (location_score * 0.6) + (text_score * 0.4)
                    if combined > best_score:
                        best_score = combined
                        best_match = ocr
            
            # Strategy 2: Text Match
            if not best_match or best_score < 0.5:
                text_candidates = []
                for ocr in grouped_ocr:
                    if id(ocr) in used_ocr_ids: continue
                    text_score = self._text_similarity(gem.value, ocr.text)
                    if text_score >= 0.5:
                        box = ocr.bounding_box
                        ocr_x = (box["xmin"] + box["xmax"]) / 2
                        ocr_y = (box["ymin"] + box["ymax"]) / 2
                        distance = ((ocr_x - target_x) ** 2 + (ocr_y - target_y) ** 2) ** 0.5
                        max_allowed = max_dist * 1.5 if text_score > 0.8 else max_dist
                        if distance < max_allowed:
                            text_candidates.append((ocr, text_score, distance))
                
                if text_candidates:
                    text_candidates.sort(key=lambda x: (x[2], -x[1]))
                    best_match = text_candidates[0][0]
                    best_score = text_candidates[0][1]
            
            # Strategy 3: Raw OCR
            if not best_match or best_score < 0.5:
                combined_match = self._try_combine_nearby(gem, raw_ocr, target_x, target_y, used_ocr_ids, max_dist)
                if combined_match:
                    verify_score = self._text_similarity(gem.value, combined_match.text)
                    if verify_score > 0.5:
                        best_match = combined_match
                        best_score = verify_score
            
            # FIX: Fallback confidence lowered to 0.75 (from 0.9)
            if not best_match and gem.confidence > 0.75:
                virtual_box = {
                    "xmin": target_x - 30, "xmax": target_x + 30,
                    "ymin": target_y - 15, "ymax": target_y + 15
                }
                matched.append(Dimension(id=0, value=gem.value, zone=None, bounding_box=BoundingBox(**virtual_box), confidence=gem.confidence, page=1))
                continue

            if best_match:
                used_ocr_ids.add(id(best_match))
                matched.append(Dimension(id=0, value=gem.value, zone=None, bounding_box=BoundingBox(**best_match.bounding_box), confidence=best_score, page=1))
        
        return matched
    
    def _text_similarity(self, s1: str, s2: str) -> float:
        n1 = self._normalize(s1)
        n2 = self._normalize(s2)
        if n1 == n2: return 1.0
        if n1 in n2 or n2 in n1: return 0.8
        return SequenceMatcher(None, n1, n2).ratio()
    
    def _normalize(self, text: str) -> str:
        if not text: return ""
        n = text.lower()
        for old, new in [('ø', 'o'), ('"', ''), ("'", ''), (' ', ''), ('–', '-')]:
            n = n.replace(old, new)
        return re.sub(r'[^\w.\-+/]', '', n)
    
    def _try_combine_nearby(self, gem, raw_ocr, target_x, target_y, used, max_dist):
        nearby = []
        for ocr in raw_ocr:
            if id(ocr) in used: continue
            box = ocr.bounding_box
            cx = (box["xmin"] + box["xmax"]) / 2
            cy = (box["ymin"] + box["ymax"]) / 2
            dist = ((cx - target_x) ** 2 + (cy - target_y) ** 2) ** 0.5
            if dist < max_dist: nearby.append((ocr, dist))
        
        if not nearby: return None
        nearby.sort(key=lambda x: x[1])
        candidates = [n[0] for n in nearby[:6]]
        target_norm = self._normalize(gem.value)
        
        for size in range(len(candidates), 0, -1):
            for combo in self._combinations(candidates, size):
                combo_sorted = sorted(combo, key=lambda d: (d.bounding_box["ymin"], d.bounding_box["xmin"]))
                combo_text = " ".join(d.text for d in combo_sorted)
                similarity = SequenceMatcher(None, target_norm, self._normalize(combo_text)).ratio()
                if similarity > 0.7:
                    return OCRDetection(
                        text=combo_text,
                        bounding_box={
                            "xmin": min(d.bounding_box["xmin"] for d in combo_sorted),
                            "xmax": max(d.bounding_box["xmax"] for d in combo_sorted),
                            "ymin": min(d.bounding_box["ymin"] for d in combo_sorted),
                            "ymax": max(d.bounding_box["ymax"] for d in combo_sorted),
                        },
                        confidence=0.7
                    )
        return None
    
    def _combinations(self, items: list, size: int):
        if size == 0: yield []
        elif items:
            for i, item in enumerate(items):
                for combo in self._combinations(items[i+1:], size-1):
                    yield [item] + combo
    
    def _calculate_zone(self, center_x: float, center_y: float) -> str:
        cols = self.STANDARD_GRID_COLUMNS
        rows = self.STANDARD_GRID_ROWS
        col_idx = min(int(center_x / (1000 / len(cols))), len(cols) - 1)
        row_idx = min(int(center_y / (1000 / len(rows))), len(rows) - 1)
        return f"{cols[col_idx]}{rows[row_idx]}"
    
    def _sort_reading_order(self, dims: List[Dimension]) -> List[Dimension]:
        if not dims: return []
        band = 100
        return sorted(dims, key=lambda d: (int(d.bounding_box.center_y) // band, d.bounding_box.center_x))


def create_detection_service(ocr_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None) -> DetectionService:
    ocr = None
    vision = None
    if ocr_api_key:
        try: ocr = create_ocr_service(ocr_api_key)
        except: pass
    if gemini_api_key:
        try: vision = create_vision_service(gemini_api_key)
        except: pass
    return DetectionService(ocr_service=ocr, vision_service=vision)
