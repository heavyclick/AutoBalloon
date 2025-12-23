"""
Export Service
Generates CSV and AS9102 Form 3 Excel exports for inspection data.
"""
import csv
import io
from datetime import datetime
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from models import ExportFormat, ExportTemplate, ExportMetadata
from config import AS9102_COLUMNS


class ExportService:
    """
    Generates export files for inspection data.
    Supports CSV (simple) and XLSX (AS9102 Form 3).
    """
    
    # AS9102 Form 3 styling
    HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
    DATA_FONT = Font(size=10)
    BORDER = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    CENTER_ALIGN = Alignment(horizontal='center', vertical='center')
    LEFT_ALIGN = Alignment(horizontal='left', vertical='center')
    
    def generate_export(
        self,
        dimensions: list[dict],
        format: ExportFormat,
        template: ExportTemplate = ExportTemplate.AS9102_FORM3,
        metadata: Optional[ExportMetadata] = None,
        filename: str = "inspection"
    ) -> tuple[bytes, str, str]:
        """
        Generate export file.
        
        Args:
            dimensions: List of dimension dicts with id, value, zone
            format: Export format (CSV or XLSX)
            template: Export template (SIMPLE or AS9102_FORM3)
            metadata: Optional metadata (part number, revision, etc.)
            filename: Base filename (without extension)
            
        Returns:
            Tuple of (file_bytes, content_type, full_filename)
        """
        if format == ExportFormat.CSV:
            return self._generate_csv(dimensions, filename)
        else:
            if template == ExportTemplate.SIMPLE:
                return self._generate_simple_xlsx(dimensions, filename)
            else:
                return self._generate_as9102_xlsx(dimensions, metadata, filename)
    
    def _generate_csv(
        self, 
        dimensions: list[dict],
        filename: str
    ) -> tuple[bytes, str, str]:
        """Generate simple CSV export"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Char No", "Reference Location", "Requirement"])
        
        # Data
        for dim in dimensions:
            writer.writerow([
                dim.get("id", ""),
                dim.get("zone", "—"),
                dim.get("value", "")
            ])
        
        csv_bytes = output.getvalue().encode('utf-8')
        return (
            csv_bytes,
            "text/csv",
            f"{filename}_inspection.csv"
        )
    
    def _generate_simple_xlsx(
        self,
        dimensions: list[dict],
        filename: str
    ) -> tuple[bytes, str, str]:
        """Generate simple Excel export with just ID, Zone, Value"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Inspection"
        
        # Headers
        headers = ["Char No", "Reference Location", "Requirement"]
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.CENTER_ALIGN
            cell.border = self.BORDER
        
        # Data
        for row_idx, dim in enumerate(dimensions, start=2):
            ws.cell(row=row_idx, column=1, value=dim.get("id", "")).border = self.BORDER
            ws.cell(row=row_idx, column=2, value=dim.get("zone", "—")).border = self.BORDER
            ws.cell(row=row_idx, column=3, value=dim.get("value", "")).border = self.BORDER
        
        # Column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 18
        ws.column_dimensions['C'].width = 25
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        xlsx_bytes = output.getvalue()
        
        return (
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            f"{filename}_inspection.xlsx"
        )
    
    def _generate_as9102_xlsx(
        self,
        dimensions: list[dict],
        metadata: Optional[ExportMetadata],
        filename: str
    ) -> tuple[bytes, str, str]:
        """
        Generate AS9102 Form 3 compliant Excel export.
        
        AS9102 Form 3 columns:
        1. Char No - Balloon/characteristic number
        2. Reference Location - Drawing zone (e.g., "C4")
        3. Characteristic Designator - Optional designator
        4. Requirement - The dimension value/tolerance
        5. Results - Blank for inspector to fill
        6. Tool Used - Blank for inspector to fill
        7. Non-Conformance - Blank for inspector to fill
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "FAI Form 3"
        
        # Build filename from metadata
        parts = []
        if metadata:
            if metadata.part_number:
                parts.append(metadata.part_number)
            if metadata.revision:
                parts.append(f"Rev{metadata.revision}")
        if not parts:
            parts.append(filename)
        parts.append("FAI")
        full_filename = "_".join(parts) + ".xlsx"
        
        # === Header Section ===
        self._add_header_section(ws, metadata)
        
        # === Column Headers (Row 6) ===
        header_row = 6
        for col, header in enumerate(AS9102_COLUMNS, start=1):
            cell = ws.cell(row=header_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.CENTER_ALIGN
            cell.border = self.BORDER
        
        # === Data Rows ===
        for row_idx, dim in enumerate(dimensions, start=header_row + 1):
            # Char No
            ws.cell(row=row_idx, column=1, value=dim.get("id", "")).border = self.BORDER
            ws.cell(row=row_idx, column=1).alignment = self.CENTER_ALIGN
            
            # Reference Location (Zone)
            zone = dim.get("zone", "")
            ws.cell(row=row_idx, column=2, value=zone if zone else "—").border = self.BORDER
            ws.cell(row=row_idx, column=2).alignment = self.CENTER_ALIGN
            
            # Characteristic Designator (typically blank)
            ws.cell(row=row_idx, column=3, value="").border = self.BORDER
            
            # Requirement (dimension value)
            ws.cell(row=row_idx, column=4, value=dim.get("value", "")).border = self.BORDER
            ws.cell(row=row_idx, column=4).alignment = self.LEFT_ALIGN
            
            # Results (blank - inspector fills)
            ws.cell(row=row_idx, column=5, value="").border = self.BORDER
            
            # Tool Used (blank - inspector fills)
            ws.cell(row=row_idx, column=6, value="").border = self.BORDER
            
            # Non-Conformance (blank - inspector fills)
            ws.cell(row=row_idx, column=7, value="").border = self.BORDER
        
        # === Column Widths ===
        column_widths = {
            'A': 10,   # Char No
            'B': 18,   # Reference Location
            'C': 22,   # Characteristic Designator
            'D': 28,   # Requirement
            'E': 15,   # Results
            'F': 18,   # Tool Used
            'G': 18,   # Non-Conformance
        }
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        xlsx_bytes = output.getvalue()
        
        return (
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            full_filename
        )
    
    def _add_header_section(
        self, 
        ws, 
        metadata: Optional[ExportMetadata]
    ) -> None:
        """Add AS9102 Form 3 header section"""
        # Title
        ws.cell(row=1, column=1, value="FIRST ARTICLE INSPECTION - FORM 3")
        ws.cell(row=1, column=1).font = Font(bold=True, size=14)
        ws.merge_cells('A1:G1')
        ws.cell(row=1, column=1).alignment = self.CENTER_ALIGN
        
        # Subtitle
        ws.cell(row=2, column=1, value="Characteristic Accountability & Verification")
        ws.cell(row=2, column=1).font = Font(size=11, italic=True)
        ws.merge_cells('A2:G2')
        ws.cell(row=2, column=1).alignment = self.CENTER_ALIGN
        
        # Metadata row 1
        if metadata:
            ws.cell(row=4, column=1, value="Part Number:")
            ws.cell(row=4, column=1).font = Font(bold=True)
            ws.cell(row=4, column=2, value=metadata.part_number or "")
            
            ws.cell(row=4, column=4, value="Part Name:")
            ws.cell(row=4, column=4).font = Font(bold=True)
            ws.cell(row=4, column=5, value=metadata.part_name or "")
        
        # Metadata row 2
        ws.cell(row=5, column=1, value="Revision:")
        ws.cell(row=5, column=1).font = Font(bold=True)
        if metadata:
            ws.cell(row=5, column=2, value=metadata.revision or "")
        
        ws.cell(row=5, column=4, value="Date:")
        ws.cell(row=5, column=4).font = Font(bold=True)
        ws.cell(row=5, column=5, value=datetime.now().strftime("%Y-%m-%d"))


# Singleton instance
export_service = ExportService()
