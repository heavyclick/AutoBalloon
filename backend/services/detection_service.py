"""
Detection Service

Orchestrates OCR + Gemini Vision fusion for accurate dimension detection.

FIXED:
- Supports compound dimensions like "3.5 (2x)", "35 C/C"
- Merges modifier OCR boxes into a single bounding box
- Preserves correct spatial placement and reading order
"""

import re
from typing import Optional
from difflib import SequenceMatcher

from services.ocr_service import OCRService, OCRDetection, create_ocr_service
from services.vision_service import VisionService, create_vision_service
from models import Dimension, BoundingBox, ErrorCode
from config import HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD


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

        ocr_detections = await self._run_ocr(image_bytes, image_width, image_height)
        gemini_dimensions = await self._run_gemini(image_bytes)

        matched_dimensions = self._match_dimensions(
            ocr_detections,
            gemini_dimensions
        )

        sorted_dimensions = self._sort_reading_order(matched_dimensions)

        for idx, dim in enumerate(sorted_dimensions, start=1):
            dim.id = idx

        return sorted_dimensions

    async def _run_ocr(self, image_bytes, image_width, image_height):
        if not self.ocr_service:
            return []

        detections = await self.ocr_service.detect_text(
            image_bytes, image_width, image_height
        )
        return self.ocr_service.group_adjacent_text(detections)

    async def _run_gemini(self, image_bytes):
        if not self.vision_service:
            return []
        return await self.vision_service.identify_dimensions(image_bytes)

    # ------------------------------------------------------------------
    # CORE FIX STARTS HERE
    # ------------------------------------------------------------------

    def _match_dimensions(
        self,
        ocr_detections: list[OCRDetection],
        gemini_dimensions: list[str]
    ) -> list[Dimension]:

        matched = []
        used_ocr_ids = set()

        for dim_value in gemini_dimensions:
            match = self._find_best_ocr_match(
                dim_value,
                ocr_detections,
                used_ocr_ids
            )

            if not match:
                print(f"No OCR match for dimension: {dim_value}")
                continue

            ocr_boxes, match_confidence = match

            for ocr in ocr_boxes:
                used_ocr_ids.add(id(ocr))

            merged_box = self._merge_bounding_boxes(
                [ocr.bounding_box for ocr in ocr_boxes]
            )

            avg_conf = sum(o.confidence for o in ocr_boxes) / len(ocr_boxes)
            combined_confidence = avg_conf * match_confidence

            matched.append(Dimension(
                id=0,
                value=dim_value,
                zone=None,
                bounding_box=merged_box,
                confidence=combined_confidence
            ))

        return matched

    def _find_best_ocr_match(
        self,
        dimension_value: str,
        ocr_detections: list[OCRDetection],
        used_ids: set
    ) -> Optional[tuple[list[OCRDetection], float]]:

        normalized_dim = self._normalize_for_matching(dimension_value)

        best_match = None
        best_score = 0.0

        for ocr in ocr_detections:
            if id(ocr) in used_ids:
                continue

            normalized_ocr = self._normalize_for_matching(ocr.text)

            # Base numeric must match
            if not normalized_dim.startswith(normalized_ocr):
                continue

            # Find nearby modifier boxes
            modifier_boxes = self._find_nearby_modifiers(
                ocr, ocr_detections, used_ids
            )

            combined_text = normalized_ocr + "".join(
                self._normalize_for_matching(m.text) for m in modifier_boxes
            )

            score = SequenceMatcher(None, normalized_dim, combined_text).ratio()

            if score > best_score:
                best_score = score
                best_match = [ocr] + modifier_boxes

        if best_match and best_score > 0.75:
            return (best_match, best_score)

        return None

    def _find_nearby_modifiers(self, base, ocr_detections, used_ids):
        modifiers = []

        for ocr in ocr_detections:
            if id(ocr) in used_ids or ocr is base:
                continue

            if not self._is_modifier_only(ocr.text):
                continue

            if (
                abs(ocr.bounding_box.center_y - base.bounding_box.center_y) < 40
                and abs(ocr.bounding_box.center_x - base.bounding_box.center_x) < 80
            ):
                modifiers.append(ocr)

        return modifiers

    def _is_modifier_only(self, text: str) -> bool:
        t = text.lower().replace(" ", "")
        return bool(re.fullmatch(
            r'\(?\d+x\)?|typ|ref|c/c|c-c|b\.c\.|bc|max|min|thru|nom|bsc',
            t
        ))

    def _merge_bounding_boxes(self, boxes: list[BoundingBox]) -> BoundingBox:
        return BoundingBox(
            x_min=min(b.x_min for b in boxes),
            y_min=min(b.y_min for b in boxes),
            x_max=max(b.x_max for b in boxes),
            y_max=max(b.y_max for b in boxes)
        )

    # ------------------------------------------------------------------
    # CORE FIX ENDS HERE
    # ------------------------------------------------------------------

    def _normalize_for_matching(self, text: str) -> str:
        normalized = text.lower()
        replacements = {
            "ø": "o",
            "⌀": "o",
            "°": "",
            "±": "+-",
            " ": "",
            ",": ".",
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        normalized = re.sub(r'[^\w.\-+/]', '', normalized)
        return normalized

    def _sort_reading_order(self, dimensions: list[Dimension]) -> list[Dimension]:
        if not dimensions:
            return []

        band_height = 100

        def band(dim):
            return dim.bounding_box.center_y // band_height

        return sorted(
            dimensions,
            key=lambda d: (band(d), d.bounding_box.center_x)
        )


def create_detection_service(
    ocr_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None
) -> DetectionService:

    ocr_service = None
    vision_service = None

    if ocr_api_key:
        ocr_service = create_ocr_service(ocr_api_key)

    if gemini_api_key:
        vision_service = create_vision_service(gemini_api_key)

    return DetectionService(
        ocr_service=ocr_service,
        vision_service=vision_service
    )
