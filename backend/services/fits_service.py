"""
Fits Service - ISO 286 / ANSI Support
Provides tolerance lookups for standard hole and shaft fits.
"""
from typing import Tuple, Optional

class FitsService:
    """
    Lookup service for engineering fits (ISO 286).
    """
    
    # Simplified lookup table for common fits.
    # In a full production env, this would be a complete database covering all diameter ranges.
    # Format: "CLASS": { "range_max": (upper_tol, lower_tol) }
    # Using a simplified model where values are approximated for standard sizes < 30mm for demo purposes.
    
    ISO_FITS = {
        # Hole Fits (Capital Letters) - Usually + / 0
        "H7": {"upper": 0.015, "lower": 0.000},  # mm approx for small range
        "H8": {"upper": 0.022, "lower": 0.000},
        "H9": {"upper": 0.036, "lower": 0.000},
        "G7": {"upper": 0.020, "lower": 0.005},
        
        # Shaft Fits (Lowercase Letters) - Usually negative for clearance
        "g6": {"upper": -0.005, "lower": -0.014},
        "f7": {"upper": -0.010, "lower": -0.025},
        "h6": {"upper": 0.000, "lower": -0.009},
        "h7": {"upper": 0.000, "lower": -0.015},
    }

    def get_fit_limits(self, nominal: float, fit_class: str, units: str = "mm") -> Tuple[float, float]:
        """
        Returns (upper_limit, lower_limit) for a given nominal size and fit class.
        """
        # 1. Normalize Class
        fit_key = fit_class.strip()
        
        # 2. Lookup standard tolerance
        # In a real engine, we would check if 'nominal' falls into specific diameter ranges (0-3, 3-6, 6-10...)
        # Here we return the standard reference values defined above.
        limits = self.ISO_FITS.get(fit_key)
        
        if not limits:
            # Fallback: If unknown fit, return 0 tolerance (Basic Dimension)
            return nominal, nominal

        upper_tol = limits["upper"]
        lower_tol = limits["lower"]

        # 3. Unit Conversion (Table is in mm, convert if drawing is inches)
        if units.lower() in ["in", "inch", "\""]:
            upper_tol = upper_tol / 25.4
            lower_tol = lower_tol / 25.4

        # 4. Calculate Limits
        max_limit = nominal + upper_tol
        min_limit = nominal + lower_tol
        
        return max_limit, min_limit

    def get_tolerances(self, fit_class: str, units: str = "mm") -> Tuple[float, float]:
        """Returns just the tolerance values (upper, lower)."""
        limits = self.ISO_FITS.get(fit_class.strip())
        if not limits:
            return 0.0, 0.0
            
        upper = limits["upper"]
        lower = limits["lower"]
        
        if units.lower() in ["in", "inch", "\""]:
            upper /= 25.4
            lower /= 25.4
            
        return upper, lower

# Singleton
fits_service = FitsService()
