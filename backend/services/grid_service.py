"""
Grid Service
Handles grid zone detection and assignment for AS9102 compliance.

Manufacturing drawings typically have a grid reference system (e.g., A-H columns, 1-4 rows)
that allows inspectors to quickly locate dimensions using zone references like "C4".
"""
from typing import Optional
from dataclasses import dataclass

from services.vision_service import VisionService, create_vision_service
from models import Dimension, GridInfo, BoundingBox
from config import NORMALIZED_COORD_SYSTEM


@dataclass
class ZoneBoundaries:
    """Stores calculated zone boundaries"""
    columns: list[str]
    rows: list[str]
    column_edges: list[int]  # X positions (normalized 0-1000)
    row_edges: list[int]     # Y positions (normalized 0-1000)


class GridService:
    """
    Detects grid reference system and assigns zones to dimensions.
    """
    
    # Default grid configurations for common drawing formats
    DEFAULT_GRIDS = {
        "A_SIZE": {
            "columns": ["A", "B", "C", "D"],
            "rows": ["1", "2", "3", "4"]
        },
        "B_SIZE": {
            "columns": ["A", "B", "C", "D", "E", "F"],
            "rows": ["1", "2", "3", "4"]
        },
        "C_SIZE": {
            "columns": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "rows": ["1", "2", "3", "4", "5", "6"]
        },
        "D_SIZE": {
            "columns": ["A", "B", "C", "D", "E", "F", "G", "H"],
            "rows": ["1", "2", "3", "4"]
        }
    }
    
    def __init__(self, vision_service: Optional[VisionService] = None):
        self.vision_service = vision_service
        self._zone_boundaries: Optional[ZoneBoundaries] = None
    
    async def detect_grid(self, image_bytes: bytes) -> GridInfo:
        """
        Detect the grid reference system on the drawing.
        
        Strategy:
        1. Try visual detection via Gemini
        2. If no grid detected, return GridInfo with detected=False
        
        Args:
            image_bytes: PNG image data
            
        Returns:
            GridInfo object
        """
        grid_info = GridInfo(detected=False)
        
        if not self.vision_service:
            return grid_info
        
        try:
            grid_data = await self.vision_service.detect_grid(image_bytes)
            
            if grid_data:
                columns = grid_data.get("columns", [])
                rows = grid_data.get("rows", [])
                boundaries = grid_data.get("boundaries", {})
                
                if columns and rows:
                    # Store boundaries for zone assignment
                    self._zone_boundaries = ZoneBoundaries(
                        columns=columns,
                        rows=rows,
                        column_edges=boundaries.get("column_edges", self._calculate_edges(len(columns))),
                        row_edges=boundaries.get("row_edges", self._calculate_edges(len(rows)))
                    )
                    
                    grid_info = GridInfo(
                        detected=True,
                        columns=columns,
                        rows=rows,
                        boundaries=boundaries
                    )
        except Exception as e:
            # Grid detection is optional - log and continue
            print(f"Grid detection error (continuing): {e}")
        
        return grid_info
    
    def _calculate_edges(self, count: int) -> list[int]:
        """Calculate evenly distributed edges for a given count"""
        return [
            int(i * NORMALIZED_COORD_SYSTEM / count)
            for i in range(count + 1)
        ]
    
    def set_grid_manually(self, columns: list[str], rows: list[str]) -> None:
        """
        Manually set grid configuration.
        Useful for testing or when auto-detection fails.
        """
        self._zone_boundaries = ZoneBoundaries(
            columns=columns,
            rows=rows,
            column_edges=self._calculate_edges(len(columns)),
            row_edges=self._calculate_edges(len(rows))
        )
    
    def assign_zone(self, bounding_box: BoundingBox) -> Optional[str]:
        """
        Determine which zone a dimension falls into based on its bounding box.
        
        Args:
            bounding_box: The dimension's bounding box (normalized 0-1000)
            
        Returns:
            Zone string (e.g., "C4") or None if no grid configured
        """
        if not self._zone_boundaries:
            return None
        
        # Use center point of bounding box
        center_x = bounding_box.center_x
        center_y = bounding_box.center_y
        
        # Find column
        column_idx = self._find_zone_index(
            center_x, 
            self._zone_boundaries.column_edges
        )
        
        # Find row
        row_idx = self._find_zone_index(
            center_y,
            self._zone_boundaries.row_edges
        )
        
        if column_idx is None or row_idx is None:
            return None
        
        column = self._zone_boundaries.columns[column_idx]
        row = self._zone_boundaries.rows[row_idx]
        
        return f"{column}{row}"
    
    def _find_zone_index(self, position: int, edges: list[int]) -> Optional[int]:
        """
        Find which zone a position falls into based on edge boundaries.
        
        Args:
            position: Normalized position (0-1000)
            edges: List of edge positions (one more than number of zones)
            
        Returns:
            Zone index (0-based) or None if out of bounds
        """
        for i in range(len(edges) - 1):
            if edges[i] <= position < edges[i + 1]:
                return i
        
        # Handle edge case: position exactly at last edge
        if position == edges[-1] and len(edges) > 1:
            return len(edges) - 2
        
        return None
    
    def assign_zones_to_dimensions(self, dimensions: list[Dimension]) -> list[Dimension]:
        """
        Assign zone references to a list of dimensions.
        
        Args:
            dimensions: List of Dimension objects
            
        Returns:
            Same list with zone field populated
        """
        for dim in dimensions:
            dim.zone = self.assign_zone(dim.bounding_box)
        return dimensions
    
    def recalculate_zone(self, new_bounding_box: BoundingBox) -> Optional[str]:
        """
        Recalculate zone for a moved balloon.
        
        Args:
            new_bounding_box: Updated bounding box after user drag
            
        Returns:
            New zone string or None
        """
        return self.assign_zone(new_bounding_box)


def create_grid_service(vision_service: Optional[VisionService] = None) -> GridService:
    """Factory function to create grid service"""
    return GridService(vision_service=vision_service)
