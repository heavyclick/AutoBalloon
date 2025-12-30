import re
import csv
import io
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class CMMParserServiceError(Exception):
    """Custom exception for CMM parsing errors"""
    pass

class CMMParserService:
    """
    Production-ready CMM Report Parser.
    Handles unstructured text reports from major CMM brands (PC-DMIS, Calypso, Mitutoyo)
    and standardizes them into a JSON-serializable format.
    """

    def __init__(self):
        # ==========================================
        # PC-DMIS PATTERNS
        # ==========================================
        # Headers like: "DIM LOC1= LOCATION OF HOLE" or "DIM 123= TRUE POSITION"
        self.pcdmis_header = re.compile(
            r'^(?:DIM|DIMENSION)\s+(?P<id>[\w\.\-]+)(?:=| )', 
            re.IGNORECASE
        )
        
        # Data lines. PC-DMIS format is notoriously flexible. 
        # Standard: AX    NOM    MEAS    +TOL    -TOL    DEV     OUTTOL
        # We use a loose pattern to capture the axis and the sequence of numbers.
        self.pcdmis_line = re.compile(
            r'^\s*(?P<axis>[XYZDTPRAMV])\s+'  # Axis indicator
            r'(?P<vals>[\d\.\-\+\s]+)'        # Capture all numbers following
        )

        # ==========================================
        # CALYPSO / ZEISS PATTERNS
        # ==========================================
        # Matches the compact text report format:
        # Feature       Nominal    Upper    Lower    Actual    Deviation
        # Circle1       10.0000    0.1000   -0.1000  10.0020   0.0020
        self.calypso_line = re.compile(
            r'^\s*(?P<id>[\w\.\-\_]+)\s+'     # Feature Name
            r'(?P<nom>[+\-]?\d+\.\d+)\s+'     # Nominal
            r'(?P<up>[+\-]?\d+\.\d+)\s+'      # Upper Tol
            r'(?P<low>[+\-]?\d+\.\d+)\s+'     # Lower Tol
            r'(?P<act>[+\-]?\d+\.\d+)\s+'     # Actual
            r'(?P<dev>[+\-]?\d+\.\d+)',       # Deviation
            re.IGNORECASE
        )

    def parse_file(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Main entry point. Detects encoding and format, then routes to specific parser.
        """
        try:
            # 1. Decode Content (Handle ASCII, UTF-8, Latin-1)
            text = self._decode_content(file_content)
            
            # 2. Detect Format
            format_type = self._detect_format(text, filename)
            logger.info(f"Detected CMM format: {format_type} for file {filename}")

            # 3. Parse
            if format_type == "CSV":
                return self._parse_csv(text)
            elif format_type == "PCDMIS":
                return self._parse_pcdmis(text)
            elif format_type == "CALYPSO":
                return self._parse_calypso(text)
            else:
                # Fallback to generic if structured parsing fails
                logger.warning(f"Unknown format for {filename}, attempting generic parse.")
                return self._parse_generic(text)

        except Exception as e:
            logger.error(f"Failed to parse CMM file {filename}: {str(e)}")
            raise CMMParserServiceError(f"Parsing failed: {str(e)}")

    def _decode_content(self, content: bytes) -> str:
        """Robust decoding strategy."""
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise CMMParserServiceError("Unable to decode file content. Unknown encoding.")

    def _detect_format(self, text: str, filename: str) -> str:
        """Heuristic format detection."""
        header_sample = text[:1000].upper()
        
        if filename.lower().endswith('.csv'):
            return "CSV"
        if "DIMENSION LOCATION" in header_sample or "PC-DMIS" in header_sample:
            return "PCDMIS"
        if "CALYPSO" in header_sample or "ZEISS" in header_sample:
            return "CALYPSO"
        # CSV check by content if extension is missing
        if "," in text.split('\n')[0]:
            return "CSV"
            
        return "UNKNOWN"

    def _calculate_status(self, deviation: float, plus_tol: float, minus_tol: float) -> str:
        """
        Mathematically verify Pass/Fail.
        Note: Minus tolerance is often passed as a positive number in databases 
        but might be negative in reports. We normalize here.
        """
        try:
            # Ensure tolerances are absolute magnitudes for comparison logic
            upper_limit = abs(plus_tol)
            lower_limit = -abs(minus_tol)
            
            # If deviation is outside the range (Lower < Dev < Upper)
            if lower_limit <= deviation <= upper_limit:
                return "PASS"
            return "FAIL"
        except Exception:
            return "UNKNOWN"

    def _clean_float(self, val: Any) -> float:
        """Safe float conversion."""
        if val is None or val == "":
            return 0.0
        try:
            if isinstance(val, str):
                val = val.replace(',', '').replace('"', '').strip()
            return float(val)
        except ValueError:
            return 0.0

    # ==========================================
    # SPECIFIC PARSERS
    # ==========================================

    def _parse_pcdmis(self, text: str) -> List[Dict[str, Any]]:
        """
        Parses PC-DMIS text reports.
        Strategy: State machine. Detect a 'DIM' header, then capture subsequent 'AX' lines.
        """
        results = []
        lines = text.split('\n')
        current_feature_id = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 1. Check for Feature Header
            header_match = self.pcdmis_header.search(line)
            if header_match:
                current_feature_id = header_match.group('id')
                continue

            # 2. Check for Axis Data Line (Must have a feature active)
            if current_feature_id:
                data_match = self.pcdmis_line.search(line)
                if data_match:
                    axis = data_match.group('axis')
                    raw_vals = data_match.group('vals').split()
                    
                    # PC-DMIS columns shift depending on report settings. 
                    # Usually: NOM, MEAS, +TOL, -TOL, DEV, OUTTOL
                    # We assume at least NOM, MEAS, DEV are present if length >= 3
                    if len(raw_vals) >= 3:
                        try:
                            # Heuristic mapping based on standard report layout
                            nom = self._clean_float(raw_vals[0])
                            meas = self._clean_float(raw_vals[1])
                            
                            # If we have 5+ columns, we likely have tolerances
                            plus_tol = 0.0
                            minus_tol = 0.0
                            dev = 0.0
                            
                            if len(raw_vals) >= 5:
                                plus_tol = self._clean_float(raw_vals[2])
                                minus_tol = self._clean_float(raw_vals[3])
                                dev = self._clean_float(raw_vals[4])
                            else:
                                # Fallback for simple reports
                                dev = self._clean_float(raw_vals[2])

                            # Calculate status
                            status = self._calculate_status(dev, plus_tol, minus_tol)
                            
                            # Check if explicitly marked "OUT" (often last column)
                            if len(raw_vals) >= 6 and self._clean_float(raw_vals[-1]) != 0:
                                status = "FAIL"

                            results.append({
                                "feature_id": current_feature_id,
                                "axis": axis,
                                "nominal": nom,
                                "actual": meas,
                                "deviation": dev,
                                "plus_tol": plus_tol,
                                "minus_tol": minus_tol,
                                "status": status
                            })
                        except Exception:
                            # Skip malformed lines silently
                            continue

        return results

    def _parse_calypso(self, text: str) -> List[Dict[str, Any]]:
        """
        Parses Zeiss Calypso compact reports.
        """
        results = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip noise
            if not line or "Nominal" in line or "ZEISS" in line:
                continue
                
            match = self.calypso_line.search(line)
            if match:
                data = match.groupdict()
                try:
                    dev = self._clean_float(data['dev'])
                    plus = self._clean_float(data['up'])
                    minus = self._clean_float(data['low'])
                    
                    status = self._calculate_status(dev, plus, minus)
                    
                    # Calypso sometimes puts a symbol at the start or end for failure
                    if "*" in line or "!" in line:
                        status = "FAIL"

                    results.append({
                        "feature_id": data['id'],
                        "nominal": self._clean_float(data['nom']),
                        "actual": self._clean_float(data['act']),
                        "deviation": dev,
                        "plus_tol": plus,
                        "minus_tol": minus,
                        "status": status
                    })
                except Exception:
                    continue
                    
        return results

    def _parse_csv(self, text: str) -> List[Dict[str, Any]]:
        """
        Parses standard CSV exports.
        Assumes first row is header. Case-insensitive column mapping.
        """
        results = []
        try:
            f = io.StringIO(text)
            reader = csv.DictReader(f)
            
            # Map standard keys
            for row in reader:
                # Lowercase keys for consistent lookup
                r = {k.lower().strip(): v for k, v in row.items() if k}
                
                # Identify ID
                feat_id = r.get('feature') or r.get('id') or r.get('name') or r.get('dim') or r.get('label')
                if not feat_id:
                    continue
                
                # Identify Values
                nom = self._clean_float(r.get('nominal') or r.get('nom') or r.get('target'))
                act = self._clean_float(r.get('actual') or r.get('measured') or r.get('meas'))
                dev = self._clean_float(r.get('deviation') or r.get('dev') or r.get('delta'))
                
                # Tolerances
                plus = self._clean_float(r.get('plus') or r.get('+tol') or r.get('upper_tol'))
                minus = self._clean_float(r.get('minus') or r.get('-tol') or r.get('lower_tol'))
                
                # Status
                status = r.get('status') or r.get('pass/fail')
                if not status:
                    status = self._calculate_status(dev, plus, minus)
                else:
                    status = status.upper().strip()
                    if status in ['1', 'TRUE', 'OK']: status = "PASS"
                    if status in ['0', 'FALSE', 'NOK', 'OUT']: status = "FAIL"

                results.append({
                    "feature_id": feat_id,
                    "nominal": nom,
                    "actual": act,
                    "deviation": dev,
                    "plus_tol": plus,
                    "minus_tol": minus,
                    "status": status
                })
        except Exception as e:
            logger.error(f"CSV Parse error: {e}")
            
        return results

    def _parse_generic(self, text: str) -> List[Dict[str, Any]]:
        """
        Last resort parser for unknown text formats.
        Looks for lines with 3+ distinct floating point numbers.
        """
        results = []
        # Pattern: Word (ID) ... Number ... Number ... Number
        pattern = re.compile(r'(?P<id>[\w\.\-]+).*?(?P<n1>[+\-]?\d+\.\d+).*?(?P<n2>[+\-]?\d+\.\d+).*?(?P<n3>[+\-]?\d+\.\d+)')
        
        lines = text.split('\n')
        for line in lines:
            if len(line) < 10: continue
            
            match = pattern.search(line)
            if match:
                # Assumption: Nominal -> Actual -> Deviation (Most common sequence)
                results.append({
                    "feature_id": match.group('id'),
                    "nominal": float(match.group('n1')),
                    "actual": float(match.group('n2')),
                    "deviation": float(match.group('n3')),
                    "status": "UNKNOWN" # Cannot safely determine without tol
                })
        return results

# Initialize singleton
cmm_parser_service = CMMParserService()
