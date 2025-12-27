"""
Pattern Library for Manufacturing Dimension Detection
Comprehensive patterns for aerospace, medical, defense, automotive, and general manufacturing.

This library supports AS9102 FAI across ALL industries:
- Aerospace (AN/MS/NAS parts, MIL-SPEC)
- Medical devices (ISO 13485, biocompatibility)
- Automotive (PPAP, APQP)
- Defense (ITAR/EAR compliant)
- General manufacturing

Thread Standards: UTS, Metric ISO, NPT, BSP, ACME, Trapezoidal, Buttress, SAE
Tolerances: Bilateral, Unilateral, Limits, Stacked, Reference, Basic
GD&T: All 14 geometric characteristics per ASME Y14.5 / ISO 1101
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Result of a pattern match"""
    text: str
    pattern_type: str
    category: str
    confidence: float
    start: int = 0
    end: int = 0


class ManufacturingPatterns:
    """
    Comprehensive pattern matching for manufacturing drawings.
    Designed for multi-industry SaaS use.
    """
    
    # =========================================================================
    # THREAD CALLOUT PATTERNS - All Major Standards
    # =========================================================================
    
    THREAD_PATTERNS = {
        # UTS - Unified Thread Standard (US) - Most common in US manufacturing
        'uts_basic': re.compile(
            r'(?P<size>(?:\#\d+|\d+/\d+|\d+(?:\.\d+)?))'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)'
            r'(?:\s*(?P<class>UN[CEFJ]?(?:-[123][AB]?)?))?'
            r'(?:\s*(?P<hand>LH|RH))?',
            re.IGNORECASE
        ),
        
        # UTS with quantity prefix: 2X 6-32, 4X For 8-32
        'uts_with_prefix': re.compile(
            r'(?P<qty>\d+)\s*[xX]\s*'
            r'(?:For\s+)?'
            r'(?P<size>(?:\#\d+|\d+/\d+|\d+(?:\.\d+)?))'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)'
            r'(?:\s*(?P<class>UN[CEFJ]?)?)?',
            re.IGNORECASE
        ),
        
        # UTS with "For" prefix: For 6-32
        'uts_for_prefix': re.compile(
            r'For\s+'
            r'(?P<size>(?:\#\d+|\d+/\d+|\d+))'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)',
            re.IGNORECASE
        ),
        
        # Metric ISO threads: M6, M8x1.25, M10x1.5-6H
        'metric_iso': re.compile(
            r'M\s*(?P<diameter>\d+(?:\.\d+)?)'
            r'(?:\s*[xX]\s*(?P<pitch>\d+(?:\.\d+)?))?'
            r'(?:\s*[-–]\s*(?P<tolerance>\d+[gGhH]\d*[gGhH]?))?'
            r'(?:\s*(?P<hand>LH|RH))?',
            re.IGNORECASE
        ),
        
        # Metric fine thread: MF8x1.0
        'metric_fine': re.compile(
            r'MF\s*(?P<diameter>\d+(?:\.\d+)?)'
            r'(?:\s*[xX]\s*(?P<pitch>\d+(?:\.\d+)?))?',
            re.IGNORECASE
        ),
        
        # NPT - National Pipe Taper (US pipe threads)
        'npt': re.compile(
            r'(?P<size>\d+/\d+|\d+(?:\.\d+)?)'
            r'(?:\s*[-–]\s*(?P<tpi>\d+))?\s*'
            r'(?P<type>NPT[FSM]?|NPS[LMF]?)',
            re.IGNORECASE
        ),
        
        # BSP - British Standard Pipe
        'bsp': re.compile(
            r'(?P<prefix>[GRr][Pp]?)?\s*'
            r'(?P<size>\d+/\d+|\d+(?:\.\d+)?)'
            r'(?:\s*(?P<type>BSP[TP]?|BSPP))?',
            re.IGNORECASE
        ),
        
        # ACME threads (power transmission)
        'acme': re.compile(
            r'(?P<diameter>\d+(?:\.\d+)?)'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)\s*'
            r'(?P<type>ACME)',
            re.IGNORECASE
        ),
        
        # Trapezoidal threads (metric power transmission)
        'trapezoidal': re.compile(
            r'Tr\s*(?P<diameter>\d+)'
            r'\s*[xX]\s*'
            r'(?P<pitch>\d+)',
            re.IGNORECASE
        ),
        
        # Buttress threads
        'buttress': re.compile(
            r'(?P<diameter>\d+(?:\.\d+)?)'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)\s*'
            r'(?P<type>BUTT(?:RESS)?)',
            re.IGNORECASE
        ),
        
        # SAE thread callouts: 3/4"-16 UN/UNF (SAE)
        'sae_thread': re.compile(
            r'(?P<size>\d+/\d+|\d+(?:\.\d+)?)'
            r'["\']?\s*[-–]\s*'
            r'(?P<tpi>\d+)\s+'
            r'UN/?(?:UNF)?\s*'
            r'\(?\s*SAE\s*\)?',
            re.IGNORECASE
        ),
        
        # Whitworth threads (BSW/BSF)
        'whitworth': re.compile(
            r'(?P<size>\d+/\d+|\d+(?:\.\d+)?)'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)\s*'
            r'(?P<type>BS[WF])',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # TOLERANCE PATTERNS - All Formats
    # =========================================================================
    
    TOLERANCE_PATTERNS = {
        # Bilateral symmetric: +/-0.005, +/- 0.1
        'bilateral_symmetric': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'(?P<symbol>[±]|[+]/?[-–])\s*'
            r'(?P<tolerance>\.?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Bilateral asymmetric: +0.005/-0.010
        'bilateral_asymmetric': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'(?P<plus>[+]\s*\.?\d+(?:\.\d+)?)\s*'
            r'[/]?\s*'
            r'(?P<minus>[-–]\s*\.?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Stacked tolerance (vertical): 0.2500in with -0.0015 and -0.0030 below
        'stacked_tolerance': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*(?:in|mm)?\s*'
            r'(?P<upper>[+]?\s*\.?\d+(?:\.\d+)?)\s*'
            r'(?P<lower>[-–]\s*\.?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Limit dimensions: 0.500/0.495 or 0.500 - 0.495
        'limit_dimension': re.compile(
            r'(?P<upper>-?\d+(?:\.\d+)?)\s*'
            r'[/\-–]\s*'
            r'(?P<lower>-?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Unilateral plus: +0.005/-0 or +0.005/0
        'unilateral_plus': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'[+](?P<plus>\.?\d+(?:\.\d+)?)\s*'
            r'[/]?\s*[-–]?0(?:\.0+)?',
            re.IGNORECASE
        ),
        
        # Unilateral minus: +0/-0.005 or 0/-0.005
        'unilateral_minus': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'[+]?0(?:\.0+)?\s*'
            r'[/]?\s*[-–](?P<minus>\.?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Reference dimension: (25.4) or 25.4 REF
        'reference': re.compile(
            r'(?:\(\s*(?P<value1>-?\d+(?:\.\d+)?)\s*\)|'
            r'(?P<value2>-?\d+(?:\.\d+)?)\s+REF(?:ERENCE)?)',
            re.IGNORECASE
        ),
        
        # Basic dimension: [25.4] or 25.4 BSC
        'basic': re.compile(
            r'(?:\[\s*(?P<value1>-?\d+(?:[.,]\d+)?)\s*\]|'
            r'(?P<value2>-?\d+(?:[.,]\d+)?)\s+(?:BSC|BASIC))',
            re.IGNORECASE
        ),
        
        # Maximum: 25.4 MAX
        'maximum': re.compile(
            r'(?P<value>-?\d+(?:\.\d+)?)\s*'
            r'(?P<type>MAX(?:IMUM)?)',
            re.IGNORECASE
        ),
        
        # Minimum: 25.4 MIN
        'minimum': re.compile(
            r'(?P<value>-?\d+(?:\.\d+)?)\s*'
            r'(?P<type>MIN(?:IMUM)?)',
            re.IGNORECASE
        ),
        
        # Nominal: 25 NOM
        'nominal': re.compile(
            r'(?P<value>-?\d+(?:\.\d+)?)\s*'
            r'NOM(?:INAL)?',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # GD&T PATTERNS - ASME Y14.5 / ISO 1101
    # =========================================================================
    
    GDT_PATTERNS = {
        # Diameter symbols
        'diameter': re.compile(
            r'[Øø]\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Radius
        'radius': re.compile(
            r'(?<![A-Za-z])R\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Spherical diameter: SR10
        'spherical_diameter': re.compile(
            r'S[Øø]\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Spherical radius: SR5
        'spherical_radius': re.compile(
            r'SR\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Controlled radius: CR3
        'controlled_radius': re.compile(
            r'CR\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Counterbore: CBORE O10
        'counterbore': re.compile(
            r'(?:CBORE|C-?BORE|COUNTERBORE)\s*'
            r'[Øø]?\s*(?P<diameter>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Countersink: CSINK O8 x 90
        'countersink': re.compile(
            r'(?:CSINK|C-?SINK|COUNTERSINK)\s*'
            r'[Øø]?\s*(?P<diameter>\d+(?:\.\d+)?)'
            r'(?:\s*[xX]\s*(?P<angle>\d+(?:\.\d+)?))?',
            re.IGNORECASE
        ),
        
        # Depth: DEPTH 10
        'depth': re.compile(
            r'(?:DEPTH|DEEP|DP)\s*'
            r'(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Through: THRU
        'through': re.compile(
            r'(?P<feature>[Øø]?\s*\d+(?:\.\d+)?)\s*'
            r'(?P<through>THRU|THROUGH)',
            re.IGNORECASE
        ),
        
        # Chamfer: 0.03 x 45 or C0.5
        'chamfer': re.compile(
            r'(?:(?P<size1>\d+(?:\.\d+)?)\s*[xX]\s*(?P<angle>\d+(?:\.\d+)?)|'
            r'C\s*(?P<size2>\d+(?:\.\d+)?))',
            re.IGNORECASE
        ),
        
        # Position tolerance
        'position': re.compile(
            r'(?:TRUE\s*)?POS(?:ITION)?\s*'
            r'[Øø]?\s*(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Flatness
        'flatness': re.compile(
            r'FLAT(?:NESS)?\s*(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Perpendicularity
        'perpendicularity': re.compile(
            r'PERP(?:ENDICULARITY)?\s*(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Parallelism
        'parallelism': re.compile(
            r'PARALLEL(?:ISM)?\s*(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Concentricity
        'concentricity': re.compile(
            r'CONC(?:ENTRICITY)?\s*(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Runout
        'runout': re.compile(
            r'(?:TOTAL\s*)?RUNOUT\s*(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Profile
        'profile': re.compile(
            r'PROFILE\s*(?:OF\s*(?:LINE|SURFACE))?\s*(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # DIMENSION PATTERNS - Imperial, Metric, Angular
    # =========================================================================
    
    DIMENSION_PATTERNS = {
        # Mixed fraction: 3 1/4"
        'mixed_fraction': re.compile(
            r'(?P<whole>\d+)\s+'
            r'(?P<num>\d+)\s*/\s*(?P<denom>\d+)\s*'
            r'["\']?',
            re.IGNORECASE
        ),
        
        # Simple fraction: 1/4"
        'simple_fraction': re.compile(
            r'(?<!\d\s)(?P<num>\d+)\s*/\s*(?P<denom>\d+)\s*'
            r'["\']?',
            re.IGNORECASE
        ),
        
        # Decimal inches: 0.250in, 0.250", .250"
        'decimal_inch': re.compile(
            r'(?P<value>-?\d*\.?\d+)\s*'
            r'(?P<unit>in(?:ch(?:es)?)?|["\'])',
            re.IGNORECASE
        ),
        
        # Decimal mm: 25mm, 25.4mm
        'metric_mm': re.compile(
            r'(?P<value>-?\d+(?:[.,]\d+)?)\s*'
            r'(?P<unit>mm)',
            re.IGNORECASE
        ),
        
        # Decimal cm: 2.5cm
        'metric_cm': re.compile(
            r'(?P<value>-?\d+(?:[.,]\d+)?)\s*'
            r'(?P<unit>cm)',
            re.IGNORECASE
        ),
        
        # Decimal m: 1.5m
        'metric_m': re.compile(
            r'(?P<value>-?\d+(?:[.,]\d+)?)\s*'
            r'(?P<unit>m)(?!m)',
            re.IGNORECASE
        ),
        
        # Angle degrees: 45deg, 45 deg
        'angle_degrees': re.compile(
            r'(?P<value>-?\d+(?:\.\d+)?)\s*'
            r'(?P<unit>deg(?:rees?)?)',
            re.IGNORECASE
        ),
        
        # Angle DMS: 45deg 30min 15sec
        'angle_dms': re.compile(
            r'(?P<deg>\d+)\s*(?:deg|d)\s*'
            r'(?P<min>\d+)\s*(?:min|m|\')\s*'
            r'(?:(?P<sec>\d+(?:\.\d+)?)\s*(?:sec|s|"))?',
            re.IGNORECASE
        ),
        
        # Generic decimal (no unit): 0.250, 25.4
        'decimal_generic': re.compile(
            r'(?<![a-zA-Z])(?P<value>-?\d+\.\d{2,})',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # COMPOUND DIMENSION PATTERNS
    # =========================================================================
    
    COMPOUND_PATTERNS = {
        # Key dimensions: 0.188" Wd. x 7/8" Lg. Key
        'key_dimension': re.compile(
            r'(?P<width>\d+(?:\.\d+)?)["\']?\s*'
            r'(?:Wd\.?|Width)\s*'
            r'[xX]\s*'
            r'(?P<length>\d+(?:\s+\d+)?(?:/\d+)?(?:\.\d+)?)["\']?\s*'
            r'(?:Lg\.?|Length|Long)'
            r'(?:\s*Key)?',
            re.IGNORECASE
        ),
        
        # Slot dimensions: 0.25 x 1.00
        'slot_dimension': re.compile(
            r'(?P<width>\d+(?:\.\d+)?)\s*'
            r'[xX]\s*'
            r'(?P<length>\d+(?:\.\d+)?)'
            r'(?:\s*(?:SLOT|SLT))?',
            re.IGNORECASE
        ),
        
        # Usable length range
        'usable_range': re.compile(
            r'(?:Usable\s+)?(?:Length\s+)?Range\s*'
            r'(?P<type>Min\.?|Max\.?|Minimum|Maximum)?\s*'
            r'[:.]\s*'
            r'(?P<value>\d+(?:\s+\d+/\d+|\.\d+)?)["\']?',
            re.IGNORECASE
        ),
        
        # Travel length
        'travel_length': re.compile(
            r'(?P<value>\d+(?:\.\d+)?)\s*(?:in|mm)?\s*'
            r'[-–]?\s*Travel(?:\s+Length)?',
            re.IGNORECASE
        ),
        
        # For X Flange/Tube OD
        'for_od': re.compile(
            r'For\s+'
            r'(?P<value>\d+(?:\.\d+)?)\s*(?:in)?\s*'
            r'(?P<type>Flange|Tube)?\s*OD',
            re.IGNORECASE
        ),
        
        # For Tube OD: 2 1/2"
        'for_tube_od': re.compile(
            r'For\s+Tube\s+OD\s*:\s*'
            r'(?P<value>\d+(?:\s+\d+/\d+)?)["\']?',
            re.IGNORECASE
        ),
        
        # Specification notes with dimensions
        'spec_note': re.compile(
            r'(?P<spec>[A-Za-z\s]+):\s*'
            r'(?P<value>\d+(?:\.\d+)?)\s*'
            r'(?P<unit>in|mm)?',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # MODIFIER PATTERNS
    # =========================================================================
    
    MODIFIER_PATTERNS = {
        # Quantity: 4X, (4X), 4 PLACES
        'quantity': re.compile(
            r'(?P<qty>\d+)\s*[xX]\s*|'
            r'\(\s*(?P<qty2>\d+)\s*[xX]?\s*\)|'
            r'(?P<qty3>\d+)\s*(?:PL(?:ACES?)?|HOLES?)',
            re.IGNORECASE
        ),
        
        # Typical
        'typical': re.compile(r'TYP(?:ICAL)?\.?', re.IGNORECASE),
        
        # Reference
        'reference': re.compile(r'REF(?:ERENCE)?\.?', re.IGNORECASE),
        
        # Equally spaced
        'equally_spaced': re.compile(r'EQ(?:UALLY)?\s*SP(?:ACED)?', re.IGNORECASE),
        
        # Both sides
        'both_sides': re.compile(r'BOTH\s*SIDES?', re.IGNORECASE),
        
        # Far side
        'far_side': re.compile(r'FAR\s*SIDE', re.IGNORECASE),
    }
    
    # =========================================================================
    # INDUSTRY-SPECIFIC PATTERNS
    # =========================================================================
    
    AEROSPACE_PATTERNS = {
        # AN parts
        'an_part': re.compile(r'AN\s*\d+[A-Z]?(?:-\d+[A-Z]?)?', re.IGNORECASE),
        
        # MS parts
        'ms_part': re.compile(r'MS\s*\d+[A-Z]?(?:-\d+)?', re.IGNORECASE),
        
        # NAS parts
        'nas_part': re.compile(r'NAS\s*\d+[A-Z]?(?:-\d+)?', re.IGNORECASE),
        
        # MIL-SPEC
        'mil_spec': re.compile(r'MIL[-–]?[A-Z]{1,4}[-–]?\d+[A-Z]?', re.IGNORECASE),
        
        # BAC (Boeing)
        'bac_spec': re.compile(r'BAC\s*\d+', re.IGNORECASE),
    }
    
    SURFACE_FINISH_PATTERNS = {
        # Ra value: Ra 32, Ra 0.8
        'ra': re.compile(
            r'Ra\s*(?P<value>\d+(?:\.\d+)?)\s*'
            r'(?P<unit>uin|um|RMS)?',
            re.IGNORECASE
        ),
        
        # Rz value
        'rz': re.compile(
            r'Rz\s*(?P<value>\d+(?:\.\d+)?)\s*'
            r'(?P<unit>uin|um)?',
            re.IGNORECASE
        ),
        
        # RMS value
        'rms': re.compile(
            r'(?P<value>\d+(?:\.\d+)?)\s*RMS',
            re.IGNORECASE
        ),
        
        # N-grade: N6, N7
        'n_grade': re.compile(r'N\s*(?P<grade>\d+)', re.IGNORECASE),
    }
    
    MEDICAL_PATTERNS = {
        # ISO biocompatibility
        'iso_biocompat': re.compile(r'ISO\s*10993', re.IGNORECASE),
        
        # USP Class
        'usp_class': re.compile(r'USP\s*(?:CLASS\s*)?[VI]+', re.IGNORECASE),
        
        # Sterilization methods
        'sterilization': re.compile(
            r'(?:ETO|GAMMA|AUTOCLAVE|STERILE)',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    @classmethod
    def identify_patterns(cls, text: str) -> List[PatternMatch]:
        """Identify ALL patterns in text string."""
        matches = []
        text = text.strip()
        
        # Check all pattern categories
        pattern_sets = [
            (cls.THREAD_PATTERNS, 'thread'),
            (cls.TOLERANCE_PATTERNS, 'tolerance'),
            (cls.GDT_PATTERNS, 'gdt'),
            (cls.DIMENSION_PATTERNS, 'dimension'),
            (cls.COMPOUND_PATTERNS, 'compound'),
            (cls.MODIFIER_PATTERNS, 'modifier'),
            (cls.SURFACE_FINISH_PATTERNS, 'surface_finish'),
            (cls.AEROSPACE_PATTERNS, 'aerospace'),
        ]
        
        for patterns, category in pattern_sets:
            for name, pattern in patterns.items():
                for match in pattern.finditer(text):
                    matches.append(PatternMatch(
                        text=match.group(0),
                        pattern_type=name,
                        category=category,
                        confidence=0.85,
                        start=match.start(),
                        end=match.end()
                    ))
        
        # Sort by confidence, then by match length
        matches.sort(key=lambda m: (-m.confidence, -(m.end - m.start)))
        return matches
    
    @classmethod
    def is_dimension_text(cls, text: str) -> bool:
        """Quick check if text contains any dimension-like pattern."""
        text = text.strip()
        
        # Must have at least one digit
        if not any(c.isdigit() for c in text):
            return False
        
        # Quick patterns
        quick_patterns = [
            r'\d+\.?\d*["\']',           # 0.5", 25'
            r'\d+\.?\d*(?:in|mm|cm)',    # 0.5in, 25mm
            r'\d+/\d+',                   # 1/4
            r'[ØøR]\d+',                  # O5, R2
            r'M\d+',                       # M8
            r'\d+\s*[-–]\s*\d+',          # 6-32, 1/4-20
            r'[±]\s*\.?\d+',              # +/-0.005
            r'\d+\s*[xX]\s*\d*',          # 4x, 2X
            r'\d+\s*(?:deg)',             # 45deg
        ]
        
        return any(re.search(p, text, re.IGNORECASE) for p in quick_patterns)
    
    @classmethod
    def is_thread_callout(cls, text: str) -> bool:
        """Check if text is a thread callout."""
        for pattern in cls.THREAD_PATTERNS.values():
            if pattern.search(text):
                return True
        return False
    
    @classmethod
    def is_tolerance(cls, text: str) -> bool:
        """Check if text is a tolerance value."""
        text = text.strip()
        # Matches: +0.005, -0.003, +/-0.01, +.005, -.003
        if re.match(r'^[+\-±]\s*\.?\d+(?:\.\d+)?$', text):
            return True
        # Also check tolerance patterns
        for pattern in cls.TOLERANCE_PATTERNS.values():
            if pattern.fullmatch(text):
                return True
        return False
    
    @classmethod
    def is_modifier(cls, text: str) -> bool:
        """Check if text is a quantity/type modifier."""
        text = text.strip()
        patterns = [
            r'^\d+[xX]$',        # 4X
            r'^[xX]\d+$',        # x4
            r'^\(\d+[xX]\)$',    # (4X)
            r'^TYP\.?$',         # TYP
            r'^REF\.?$',         # REF
            r'^\d+\s*PL(?:ACES?)?$',  # 4 PLACES
        ]
        return any(re.match(p, text, re.IGNORECASE) for p in patterns)
    
    @classmethod
    def is_gdt_symbol(cls, text: str) -> bool:
        """Check if text contains GD&T symbols."""
        gdt_symbols = ['Ø', 'ø', '⌀', '⌖', '◎', '⌯', '⏊', '∥', '∠', '↗', '○', 
                       '⏤', '⏥', '⌭', '⌒', '⌓', '⌴', '⌵', '↧', '□', '◻']
        return any(sym in text for sym in gdt_symbols)
    
    @classmethod
    def extract_numeric_value(cls, text: str) -> Optional[float]:
        """Extract numeric value from dimension text."""
        text = text.strip()
        
        # Try decimal first
        match = re.search(r'-?\d+\.?\d*', text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        # Try fraction
        match = re.search(r'(\d+)\s*/\s*(\d+)', text)
        if match:
            try:
                return float(match.group(1)) / float(match.group(2))
            except (ValueError, ZeroDivisionError):
                pass
        
        # Try mixed fraction
        match = re.search(r'(\d+)\s+(\d+)\s*/\s*(\d+)', text)
        if match:
            try:
                whole = float(match.group(1))
                frac = float(match.group(2)) / float(match.group(3))
                return whole + frac
            except (ValueError, ZeroDivisionError):
                pass
        
        return None
    
    @classmethod
    def get_unit(cls, text: str) -> Optional[str]:
        """Extract unit from dimension text."""
        text = text.strip().lower()
        
        if 'mm' in text:
            return 'mm'
        if 'cm' in text:
            return 'cm'
        if 'in' in text or '"' in text:
            return 'in'
        if "'" in text:
            return 'ft'
        if 'deg' in text:
            return 'deg'
        
        return None
    
    @classmethod
    def classify_dimension(cls, text: str) -> str:
        """Classify dimension type."""
        text = text.strip()
        
        if cls.is_thread_callout(text):
            return 'thread'
        if cls.is_tolerance(text):
            return 'tolerance'
        if cls.is_gdt_symbol(text):
            return 'gdt'
        if cls.is_modifier(text):
            return 'modifier'
        if re.search(r'[ØøR]\d+', text, re.IGNORECASE):
            return 'diameter_or_radius'
        if re.search(r'\d+/\d+', text):
            return 'fraction'
        if re.search(r'\d+\.\d+', text):
            return 'decimal'
        if re.search(r'\d+\s*deg', text, re.IGNORECASE):
            return 'angle'
        
        return 'linear'


# Singleton instance for easy import
PATTERNS = ManufacturingPatterns()
