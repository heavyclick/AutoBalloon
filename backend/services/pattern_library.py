"""
Pattern Library for Manufacturing Dimension Detection
Utility functions for pattern matching.
"""
import re
from typing import Optional


class ManufacturingPatterns:
    """Pattern matching utilities."""
    
    @classmethod
    def is_dimension_text(cls, text: str) -> bool:
        """Check if text contains dimension-like pattern."""
        text = text.strip()
        
        if not any(c.isdigit() for c in text):
            return False
        
        patterns = [
            r'\d+\.?\d*["\']',           # 0.5", 25'
            r'\d+\.?\d*(?:in|mm|cm)',    # 0.5in, 25mm
            r'\d+/\d+',                   # 1/4
            r'[ØøR]\d+',                  # Ø5, R2
            r'M\d+',                       # M8
            r'\d+-\d+',                   # 6-32
        ]
        
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    @classmethod
    def is_thread_callout(cls, text: str) -> bool:
        """Check if text is a thread callout."""
        patterns = [
            r'\d+/\d+\s*-\s*\d+',         # 1/4-20
            r'#\d+\s*-\s*\d+',            # #8-32
            r'M\d+\s*[xX×]\s*\d+',        # M8x1.25
            r'\d+/\d+\s*NPT',             # 1/4 NPT
            r'UN[CF]',                     # UNC, UNF
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    @classmethod
    def is_tolerance(cls, text: str) -> bool:
        """Check if text is a tolerance value."""
        text = text.strip()
        # Matches: +0.005, -0.003, ±0.01, +.005, -.003
        return bool(re.match(r'^[+\-±]\s*\.?\d+(?:\.\d+)?$', text))
    
    @classmethod
    def is_modifier(cls, text: str) -> bool:
        """Check if text is a quantity/type modifier."""
        text = text.strip().upper()
        patterns = [
            r'^\d+[xX]$',        # 4X
            r'^\(\d+[xX]\)$',    # (4X)
            r'^TYP\.?$',         # TYP
            r'^REF\.?$',         # REF
        ]
        return any(re.match(p, text, re.IGNORECASE) for p in patterns)
    
    @classmethod
    def extract_numeric(cls, text: str) -> Optional[float]:
        """Extract numeric value from dimension."""
        text = text.strip()
        
        # Decimal
        match = re.search(r'-?\d+\.?\d*', text)
        if match:
            try:
                return float(match.group())
            except:
                pass
        
        # Fraction
        match = re.search(r'(\d+)\s*/\s*(\d+)', text)
        if match:
            try:
                return float(match.group(1)) / float(match.group(2))
            except:
                pass
        
        return None


# Singleton instance
PATTERNS = ManufacturingPatterns()
