"""
Pattern Library for Manufacturing Dimension Detection
Comprehensive patterns for aerospace, medical, defense, and general manufacturing drawings.

Standards Covered:
- ASME Y14.5 (US)
- ISO 1101 (International)
- DIN (German)
- JIS (Japanese)
- AS9100 (Aerospace)
- ISO 13485 (Medical Devices)
- MIL-STD (Military/Defense)
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Result of a pattern match"""
    text: str
    pattern_type: str
    category: str
    confidence: float
    normalized: str  # Standardized form


class ManufacturingPatterns:
    """
    Comprehensive pattern matching for manufacturing drawings.
    """
    
    # =========================================================================
    # THREAD CALLOUT PATTERNS
    # =========================================================================
    
    THREAD_PATTERNS = {
        # UTS - Unified Thread Standard (US)
        'uts_basic': re.compile(
            r'(?P<size>(?:\#\d+|\d+/\d+|\d+(?:\.\d+)?))'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)'
            r'(?:\s*(?P<class>UN[CEFJ]?(?:-[123][AB]?)?))?'
            r'(?:\s*(?P<hand>LH|RH))?',
            re.IGNORECASE
        ),
        # Examples: 1/4-20, #8-32, 10-24 UNC, 1/4-20 UNC-2B, 3/8-16 LH
        
        # UTS with prefix
        'uts_with_prefix': re.compile(
            r'(?P<qty>\d+[xX]?\s*)?'
            r'(?:For\s+|Tap\s+|Thread\s+)?'
            r'(?P<size>(?:\#\d+|\d+/\d+|\d+(?:\.\d+)?))'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)'
            r'(?:\s*(?P<class>UN[CEFJ]?(?:-[123][AB]?)?))?',
            re.IGNORECASE
        ),
        # Examples: 2X For 6-32, Tap 1/4-20, 6X 8-32
        
        # Metric ISO threads
        'metric_iso': re.compile(
            r'M\s*(?P<diameter>\d+(?:\.\d+)?)'
            r'(?:\s*[xX×]\s*(?P<pitch>\d+(?:\.\d+)?))?'
            r'(?:\s*[-–]\s*(?P<tolerance>\d+[gGhH]\d*[gGhH]?))?'
            r'(?:\s*(?P<hand>LH|RH))?',
            re.IGNORECASE
        ),
        # Examples: M6, M8x1.25, M10x1.5-6H, M12x1.75 LH
        
        # Metric fine thread
        'metric_fine': re.compile(
            r'MF\s*(?P<diameter>\d+(?:\.\d+)?)'
            r'(?:\s*[xX×]\s*(?P<pitch>\d+(?:\.\d+)?))?',
            re.IGNORECASE
        ),
        
        # NPT - National Pipe Taper (US)
        'npt': re.compile(
            r'(?P<size>\d+/\d+|\d+(?:\.\d+)?)'
            r'\s*[-–]?\s*'
            r'(?P<tpi>\d+)?\s*'
            r'(?P<type>NPT|NPTF|NPSC|NPSM|NPSL|NPS)',
            re.IGNORECASE
        ),
        # Examples: 1/4-18 NPT, 3/8 NPTF, 1/2 NPS
        
        # BSP - British Standard Pipe
        'bsp': re.compile(
            r'(?P<size>\d+/\d+|\d+(?:\.\d+)?)'
            r'\s*[-–]?\s*'
            r'(?P<type>BSPT|BSPP|BSP|G|R|Rp|Rc)',
            re.IGNORECASE
        ),
        # Examples: 1/4 BSPT, G1/2, R3/4
        
        # ACME threads (power transmission)
        'acme': re.compile(
            r'(?P<diameter>\d+(?:\.\d+)?)'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)\s*'
            r'(?P<type>ACME|STUB\s*ACME)',
            re.IGNORECASE
        ),
        
        # Trapezoidal threads (ISO metric equivalent of ACME)
        'trapezoidal': re.compile(
            r'Tr\s*(?P<diameter>\d+(?:\.\d+)?)'
            r'\s*[xX×]\s*'
            r'(?P<pitch>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        # Examples: Tr20x4, Tr30x6
        
        # Buttress threads
        'buttress': re.compile(
            r'(?P<diameter>\d+(?:\.\d+)?)'
            r'\s*[-–]\s*'
            r'(?P<tpi>\d+)\s*'
            r'(?P<type>BUTT|BUT)',
            re.IGNORECASE
        ),
        
        # Thread with depth/through
        'thread_depth': re.compile(
            r'(?P<thread>(?:M|UNC|UNF|\d+/\d+[-–]\d+)[^↧⌵]*)'
            r'(?:\s*(?P<depth_symbol>[↧⌵])\s*(?P<depth>\d+(?:\.\d+)?)|'
            r'\s+(?P<thru>THRU|THROUGH))',
            re.IGNORECASE
        ),
        
        # SAE thread callouts (automotive)
        'sae_thread': re.compile(
            r'(?P<size>\d+/\d+|\d+(?:\.\d+)?)'
            r'["\']?\s*[-–]\s*'
            r'(?P<tpi>\d+)\s+'
            r'UN/?UNF?\s*'
            r'\(?\s*SAE\s*\)?',
            re.IGNORECASE
        ),
        # Examples: 3/4"-16 UN/UNF (SAE), 7/8"-14 UN/UNF (SAE)
    }
    
    # =========================================================================
    # TOLERANCE PATTERNS
    # =========================================================================
    
    TOLERANCE_PATTERNS = {
        # Bilateral symmetric: ±0.005
        'bilateral_symmetric': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'(?P<symbol>[±])\s*'
            r'(?P<tolerance>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Bilateral asymmetric: +0.005/-0.010 or +.005 -.010
        'bilateral_asymmetric': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'(?P<plus>[+]\s*\.?\d+(?:\.\d+)?)\s*'
            r'[/]?\s*'
            r'(?P<minus>[-–]\s*\.?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Stacked tolerances (vertical): value followed by +tol and -tol on separate tokens
        'stacked_tolerance': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*(?:in|mm)?\s*'
            r'(?P<plus>[+]\s*\.?\d+(?:\.\d+)?)\s*'
            r'(?P<minus>[-–]\s*\.?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Limit dimensions: 0.500/0.495 or 0.500 - 0.495
        'limit_dimensions': re.compile(
            r'(?P<upper>-?\d+(?:\.\d+)?)\s*'
            r'[/\-–]\s*'
            r'(?P<lower>-?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Unilateral plus: +0.005/-0 or +0.005/0
        'unilateral_plus': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'(?P<plus>[+]\s*\.?\d+(?:\.\d+)?)\s*'
            r'[/]?\s*'
            r'(?:[-–]?\s*0(?:\.0+)?)',
            re.IGNORECASE
        ),
        
        # Unilateral minus: +0/-0.005 or 0/-0.005
        'unilateral_minus': re.compile(
            r'(?P<nominal>-?\d+(?:\.\d+)?)\s*'
            r'(?:[+]?\s*0(?:\.0+)?)\s*'
            r'[/]?\s*'
            r'(?P<minus>[-–]\s*\.?\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Reference dimension: (25.4) or 25.4 REF
        'reference': re.compile(
            r'(?:\(\s*(?P<value1>-?\d+(?:\.\d+)?)\s*\)|'
            r'(?P<value2>-?\d+(?:\.\d+)?)\s+REF(?:ERENCE)?)',
            re.IGNORECASE
        ),
        
        # Basic dimension: [25.4] or 25.4 BSC/BASIC
        'basic': re.compile(
            r'(?:\[\s*(?P<value1>-?\d+(?:\.\d+)?)\s*\]|'
            r'(?P<value2>-?\d+(?:\.\d+)?)\s+(?:BSC|BASIC))',
            re.IGNORECASE
        ),
        
        # Maximum/Minimum: 25.4 MAX or 25.4 MIN
        'max_min': re.compile(
            r'(?P<value>-?\d+(?:\.\d+)?)\s*'
            r'(?P<type>MAX(?:IMUM)?|MIN(?:IMUM)?)',
            re.IGNORECASE
        ),
        
        # Nominal: 25 NOM or 25 NOMINAL
        'nominal': re.compile(
            r'(?P<value>-?\d+(?:\.\d+)?)\s*'
            r'NOM(?:INAL)?',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # GD&T SYMBOLS AND PATTERNS
    # =========================================================================
    
    GDT_SYMBOLS = {
        # Form tolerances
        'straightness': ('⏤', '—', 'STRAIGHTNESS'),
        'flatness': ('⏥', '▱', 'FLATNESS'),
        'circularity': ('○', '◯', 'CIRCULARITY', 'ROUNDNESS'),
        'cylindricity': ('⌭', 'CYLINDRICITY'),
        
        # Profile tolerances
        'profile_line': ('⌒', 'PROFILE OF A LINE'),
        'profile_surface': ('⌓', 'PROFILE OF A SURFACE'),
        
        # Orientation tolerances
        'angularity': ('∠', 'ANGULARITY'),
        'perpendicularity': ('⏊', '⊥', 'PERPENDICULARITY', 'SQUARENESS'),
        'parallelism': ('∥', '//', 'PARALLELISM'),
        
        # Location tolerances
        'position': ('⌖', '⊕', 'POSITION', 'TRUE POSITION'),
        'concentricity': ('◎', 'CONCENTRICITY'),
        'symmetry': ('⌯', 'SYMMETRY'),
        
        # Runout tolerances
        'circular_runout': ('↗', 'CIRCULAR RUNOUT', 'RUNOUT'),
        'total_runout': ('↗↗', 'TOTAL RUNOUT'),
    }
    
    GDT_PATTERNS = {
        # Feature control frame pattern
        'fcf': re.compile(
            r'(?P<symbol>[⏤⏥○⌭⌒⌓∠⏊⊥∥⌖⊕◎⌯↗])\s*'
            r'(?P<diameter>[Øø⌀])?\s*'
            r'(?P<tolerance>\d+(?:\.\d+)?)\s*'
            r'(?P<modifier>[ⓂⓁⓈⓅⓊ]|MMC|LMC|RFS)?\s*'
            r'(?:\|\s*(?P<primary>[A-Z]))?'
            r'(?:\s*\|\s*(?P<secondary>[A-Z]))?'
            r'(?:\s*\|\s*(?P<tertiary>[A-Z]))?',
            re.IGNORECASE
        ),
        
        # Diameter symbol
        'diameter': re.compile(
            r'[Øø⌀]\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Radius
        'radius': re.compile(
            r'R\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Spherical diameter
        'spherical_diameter': re.compile(
            r'S[Øø⌀]\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Spherical radius
        'spherical_radius': re.compile(
            r'SR\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Controlled radius
        'controlled_radius': re.compile(
            r'CR\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Counterbore
        'counterbore': re.compile(
            r'(?P<symbol>[⌴]|C[\'']?BORE)\s*'
            r'[Øø⌀]?\s*(?P<diameter>\d+(?:\.\d+)?)\s*'
            r'(?:[↧⌵]|[xX×])?\s*(?P<depth>\d+(?:\.\d+)?)?',
            re.IGNORECASE
        ),
        
        # Countersink
        'countersink': re.compile(
            r'(?P<symbol>[⌵]|C[\'']?SINK)\s*'
            r'[Øø⌀]?\s*(?P<diameter>\d+(?:\.\d+)?)\s*'
            r'[xX×]?\s*(?P<angle>\d+(?:\.\d+)?)?[°]?',
            re.IGNORECASE
        ),
        
        # Depth
        'depth': re.compile(
            r'(?P<symbol>[↧]|DEEP|DP)\s*'
            r'(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Through
        'through': re.compile(
            r'(?P<value>[Øø⌀]?\s*\d+(?:\.\d+)?)\s*'
            r'(?P<through>THRU|THROUGH)',
            re.IGNORECASE
        ),
        
        # Square symbol
        'square': re.compile(
            r'[◻□]\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Arc length
        'arc_length': re.compile(
            r'[⌒]\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # DIMENSION PATTERNS
    # =========================================================================
    
    DIMENSION_PATTERNS = {
        # Imperial with unit
        'imperial_inch': re.compile(
            r'(?P<whole>\d+)?\s*'
            r'(?P<fraction>\d+\s*/\s*\d+)?\s*'
            r'(?P<decimal>\.\d+)?\s*'
            r'["\"]|(?:in(?:ch(?:es)?)?)',
            re.IGNORECASE
        ),
        
        # Mixed fraction: 3 1/4"
        'mixed_fraction': re.compile(
            r'(?P<whole>\d+)\s+'
            r'(?P<num>\d+)\s*/\s*(?P<denom>\d+)\s*'
            r'["\"]?',
            re.IGNORECASE
        ),
        
        # Simple fraction: 1/4"
        'simple_fraction': re.compile(
            r'(?P<num>\d+)\s*/\s*(?P<denom>\d+)\s*'
            r'["\"]?',
            re.IGNORECASE
        ),
        
        # Decimal inches: 0.250in, .250", 0.250
        'decimal_inch': re.compile(
            r'(?P<value>-?\d*\.?\d+)\s*'
            r'(?P<unit>in(?:ch(?:es)?)?|["\"])',
            re.IGNORECASE
        ),
        
        # Metric: 25mm, 25.4 mm, 25,4mm (European decimal)
        'metric_mm': re.compile(
            r'(?P<value>-?\d+(?:[.,]\d+)?)\s*'
            r'(?P<unit>mm|millimeter|millimetre)',
            re.IGNORECASE
        ),
        
        # Metric cm
        'metric_cm': re.compile(
            r'(?P<value>-?\d+(?:[.,]\d+)?)\s*'
            r'(?P<unit>cm|centimeter|centimetre)',
            re.IGNORECASE
        ),
        
        # Metric m (meters)
        'metric_m': re.compile(
            r'(?P<value>-?\d+(?:[.,]\d+)?)\s*'
            r'(?P<unit>m(?:eter|etre)?)\b',
            re.IGNORECASE
        ),
        
        # Angle degrees: 45°, 45 deg, 45 degrees
        'angle_degrees': re.compile(
            r'(?P<value>-?\d+(?:\.\d+)?)\s*'
            r'(?P<unit>[°]|deg(?:rees?)?)',
            re.IGNORECASE
        ),
        
        # Angle with minutes/seconds: 45°30'15"
        'angle_dms': re.compile(
            r'(?P<degrees>-?\d+)\s*[°]\s*'
            r'(?:(?P<minutes>\d+)\s*[\'']\s*)?'
            r'(?:(?P<seconds>\d+(?:\.\d+)?)\s*["\"])?',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # MODIFIER PATTERNS
    # =========================================================================
    
    MODIFIER_PATTERNS = {
        # Quantity multipliers
        'quantity': re.compile(
            r'(?P<qty>\d+)\s*[xX×]\s*|'
            r'\(\s*(?P<qty2>\d+)\s*[xX×]?\s*\)|'
            r'(?P<qty3>\d+)\s*(?:PL(?:ACES?)?|HOLES?)',
            re.IGNORECASE
        ),
        
        # Typical
        'typical': re.compile(
            r'TYP(?:ICAL)?\.?',
            re.IGNORECASE
        ),
        
        # Reference
        'reference': re.compile(
            r'REF(?:ERENCE)?\.?',
            re.IGNORECASE
        ),
        
        # Basic
        'basic': re.compile(
            r'BSC|BASIC',
            re.IGNORECASE
        ),
        
        # Maximum/Minimum
        'max_min': re.compile(
            r'MAX(?:IMUM)?|MIN(?:IMUM)?',
            re.IGNORECASE
        ),
        
        # Nominal
        'nominal': re.compile(
            r'NOM(?:INAL)?',
            re.IGNORECASE
        ),
        
        # Equally spaced
        'equally_spaced': re.compile(
            r'EQ(?:UALLY)?\s*SP(?:ACED)?|'
            r'EQUALLY\s+SPACED',
            re.IGNORECASE
        ),
        
        # Center-to-center
        'center_to_center': re.compile(
            r'C\s*/\s*C|C\s*-\s*C|CTR\s*-?\s*CTR|'
            r'CENTER\s*TO\s*CENTER',
            re.IGNORECASE
        ),
        
        # Bolt circle
        'bolt_circle': re.compile(
            r'B\.?\s*C\.?|BC|PCD|'
            r'BOLT\s*CIRCLE|'
            r'PITCH\s*CIRCLE\s*DIA(?:METER)?',
            re.IGNORECASE
        ),
        
        # Both sides / far side / near side
        'side_indicator': re.compile(
            r'BOTH\s*SIDES?|'
            r'FAR\s*SIDE|'
            r'NEAR\s*SIDE|'
            r'THIS\s*SIDE|'
            r'OTHER\s*SIDE|'
            r'OPP(?:OSITE)?\s*SIDE',
            re.IGNORECASE
        ),
        
        # Material condition modifiers
        'material_condition': re.compile(
            r'[ⓂⓁⓈⓅⓊ]|'
            r'MMC|LMC|RFS|'
            r'REGARDLESS\s*OF\s*FEATURE\s*SIZE|'
            r'MAXIMUM\s*MATERIAL\s*CONDITION|'
            r'LEAST\s*MATERIAL\s*CONDITION',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # INDUSTRY-SPECIFIC PATTERNS
    # =========================================================================
    
    AEROSPACE_PATTERNS = {
        # AN/MS/NAS part numbers
        'an_ms_nas': re.compile(
            r'(?P<type>AN|MS|NAS)\s*(?P<number>\d+[A-Z]?\d*)',
            re.IGNORECASE
        ),
        
        # Mil-spec references
        'mil_spec': re.compile(
            r'MIL\s*-?\s*'
            r'(?P<type>[A-Z]+)\s*-?\s*'
            r'(?P<number>\d+[A-Z]?)',
            re.IGNORECASE
        ),
        
        # AS (Aerospace Standard)
        'as_standard': re.compile(
            r'AS\s*(?P<number>\d+[A-Z]?\d*)',
            re.IGNORECASE
        ),
        
        # BAC (Boeing)
        'bac': re.compile(
            r'BAC\s*(?P<number>\d+[A-Z]?\d*)',
            re.IGNORECASE
        ),
        
        # Airbus specifications
        'airbus': re.compile(
            r'AIMS\s*(?P<number>\d+-\d+)',
            re.IGNORECASE
        ),
    }
    
    MEDICAL_PATTERNS = {
        # Biocompatibility references
        'biocompat': re.compile(
            r'ISO\s*10993|'
            r'USP\s*CLASS\s*(?P<class>VI|V|IV|III|II|I)|'
            r'BIOCOMPAT(?:IBLE|IBILITY)?',
            re.IGNORECASE
        ),
        
        # Sterilization
        'sterilization': re.compile(
            r'STERILE|'
            r'ETO|ETHYLENE\s*OXIDE|'
            r'GAMMA|'
            r'AUTOCLAVE|'
            r'STEAM\s*STERIL',
            re.IGNORECASE
        ),
        
        # Medical grade materials
        'medical_material': re.compile(
            r'(?:MEDICAL|MED)\s*GRADE|'
            r'IMPLANT\s*GRADE|'
            r'(?:316L|Ti6Al4V|PEEK|UHMWPE)',
            re.IGNORECASE
        ),
    }
    
    SURFACE_FINISH_PATTERNS = {
        # Ra (arithmetic average)
        'ra': re.compile(
            r'Ra\s*(?P<value>\d+(?:\.\d+)?)\s*'
            r'(?P<unit>μin|μm|uin|um|microinch|micron)?',
            re.IGNORECASE
        ),
        
        # Rz (average maximum height)
        'rz': re.compile(
            r'Rz\s*(?P<value>\d+(?:\.\d+)?)\s*'
            r'(?P<unit>μin|μm|uin|um)?',
            re.IGNORECASE
        ),
        
        # RMS
        'rms': re.compile(
            r'(?P<value>\d+(?:\.\d+)?)\s*'
            r'RMS',
            re.IGNORECASE
        ),
        
        # Surface finish symbol with value
        'finish_symbol': re.compile(
            r'[√✓∨]\s*(?P<value>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # N-grade (ISO)
        'n_grade': re.compile(
            r'N\s*(?P<grade>\d+)',
            re.IGNORECASE
        ),
        
        # Machining allowance
        'machining_allowance': re.compile(
            r'(?P<value>\d+(?:\.\d+)?)\s*'
            r'(?:STOCK|ALLOWANCE|REMOVE)',
            re.IGNORECASE
        ),
    }
    
    WELD_PATTERNS = {
        # AWS weld symbols
        'fillet_weld': re.compile(
            r'(?P<size>\d+(?:\.\d+)?)\s*'
            r'(?:FILLET|FIL)',
            re.IGNORECASE
        ),
        
        # Groove weld
        'groove_weld': re.compile(
            r'(?P<type>V|U|J|BEVEL|SQUARE)\s*'
            r'(?:GROOVE|GRV)',
            re.IGNORECASE
        ),
        
        # Weld all around
        'weld_all_around': re.compile(
            r'WELD\s*ALL\s*AROUND|WAA|[○◯]',
            re.IGNORECASE
        ),
        
        # Field weld
        'field_weld': re.compile(
            r'FIELD\s*WELD|[▶►]',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # COMPOUND DIMENSION PATTERNS
    # =========================================================================
    
    COMPOUND_PATTERNS = {
        # Key dimensions: 0.188" Wd. x 7/8" Lg.
        'key_dimension': re.compile(
            r'(?P<width>\d+(?:\.\d+)?)["\']?\s*'
            r'(?:Wd\.?|Width)\s*'
            r'[xX×]\s*'
            r'(?P<length>\d+(?:\s+\d+)?(?:/\d+)?(?:\.\d+)?)["\']?\s*'
            r'(?:Lg\.?|Length|Long)',
            re.IGNORECASE
        ),
        
        # Slot dimensions: 0.25 x 1.00
        'slot_dimension': re.compile(
            r'(?P<width>\d+(?:\.\d+)?)\s*'
            r'[xX×]\s*'
            r'(?P<length>\d+(?:\.\d+)?)\s*'
            r'(?:SLOT)?',
            re.IGNORECASE
        ),
        
        # Chamfer: 0.03 x 45°
        'chamfer': re.compile(
            r'(?P<size>\d+(?:\.\d+)?)\s*'
            r'[xX×]\s*'
            r'(?P<angle>\d+(?:\.\d+)?)\s*[°]?|'
            r'C\s*(?P<size2>\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        
        # Usable length range
        'usable_range': re.compile(
            r'(?:Usable\s+)?Length\s+Range\s*'
            r'(?P<type>Min\.?|Max\.?|Minimum|Maximum)?\s*'
            r'[:.]?\s*'
            r'(?P<value>\d+(?:\s+\d+/\d+|\.\d+)?)["\']?',
            re.IGNORECASE
        ),
        
        # Travel length
        'travel_length': re.compile(
            r'(?P<value>\d+(?:\.\d+)?)\s*(?:in|mm)?\s*'
            r'[-–]?\s*Travel(?:\s+Length)?',
            re.IGNORECASE
        ),
    }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    @classmethod
    def identify_pattern(cls, text: str) -> List[PatternMatch]:
        """
        Identify all patterns in a text string.
        Returns list of PatternMatch objects sorted by confidence.
        """
        matches = []
        text = text.strip()
        
        # Check thread patterns
        for name, pattern in cls.THREAD_PATTERNS.items():
            match = pattern.search(text)
            if match:
                matches.append(PatternMatch(
                    text=match.group(0),
                    pattern_type=name,
                    category='thread',
                    confidence=0.9,
                    normalized=cls._normalize_thread(match, name)
                ))
        
        # Check tolerance patterns
        for name, pattern in cls.TOLERANCE_PATTERNS.items():
            match = pattern.search(text)
            if match:
                matches.append(PatternMatch(
                    text=match.group(0),
                    pattern_type=name,
                    category='tolerance',
                    confidence=0.85,
                    normalized=match.group(0)
                ))
        
        # Check GD&T patterns
        for name, pattern in cls.GDT_PATTERNS.items():
            match = pattern.search(text)
            if match:
                matches.append(PatternMatch(
                    text=match.group(0),
                    pattern_type=name,
                    category='gdt',
                    confidence=0.9,
                    normalized=match.group(0)
                ))
        
        # Check dimension patterns
        for name, pattern in cls.DIMENSION_PATTERNS.items():
            match = pattern.search(text)
            if match:
                matches.append(PatternMatch(
                    text=match.group(0),
                    pattern_type=name,
                    category='dimension',
                    confidence=0.8,
                    normalized=match.group(0)
                ))
        
        # Check compound patterns
        for name, pattern in cls.COMPOUND_PATTERNS.items():
            match = pattern.search(text)
            if match:
                matches.append(PatternMatch(
                    text=match.group(0),
                    pattern_type=name,
                    category='compound',
                    confidence=0.95,
                    normalized=match.group(0)
                ))
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda m: m.confidence, reverse=True)
        
        return matches
    
    @classmethod
    def _normalize_thread(cls, match: re.Match, pattern_type: str) -> str:
        """Normalize thread callout to standard format."""
        groups = match.groupdict()
        
        if pattern_type in ('uts_basic', 'uts_with_prefix'):
            size = groups.get('size', '')
            tpi = groups.get('tpi', '')
            thread_class = groups.get('class', '')
            qty = groups.get('qty', '')
            
            result = f"{size}-{tpi}"
            if thread_class:
                result += f" {thread_class}"
            if qty:
                result = f"{qty} {result}"
            return result
        
        elif pattern_type == 'metric_iso':
            diameter = groups.get('diameter', '')
            pitch = groups.get('pitch', '')
            tolerance = groups.get('tolerance', '')
            
            result = f"M{diameter}"
            if pitch:
                result += f"x{pitch}"
            if tolerance:
                result += f"-{tolerance}"
            return result
        
        return match.group(0)
    
    @classmethod
    def is_dimension_text(cls, text: str) -> bool:
        """Quick check if text contains any dimension-like pattern."""
        text = text.strip()
        
        # Quick numeric check
        if not any(c.isdigit() for c in text):
            return False
        
        # Check against all dimension patterns
        for pattern in cls.DIMENSION_PATTERNS.values():
            if pattern.search(text):
                return True
        
        # Check for diameter/radius
        if re.search(r'[ØøR]\s*\d', text, re.IGNORECASE):
            return True
        
        # Check for fractions
        if re.search(r'\d+\s*/\s*\d+', text):
            return True
        
        return False
    
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
        # Simple tolerance: +0.005, -0.003, ±0.01
        return bool(re.match(r'^[+\-±]\s*\.?\d+(?:\.\d+)?$', text))
    
    @classmethod
    def extract_numeric_value(cls, text: str) -> Optional[float]:
        """Extract numeric value from dimension text."""
        text = text.strip()
        
        # Try decimal
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


# Export for easy import
PATTERNS = ManufacturingPatterns()
