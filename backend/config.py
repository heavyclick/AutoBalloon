"""
AutoBalloon Configuration
Environment variables and application constants
"""
import os
from pathlib import Path

# API Keys (from environment)
GOOGLE_CLOUD_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# File Processing
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
TARGET_DPI = 400

# Image Processing
NORMALIZED_COORD_SYSTEM = 1000  # Gemini uses 0-1000 normalized coordinates

# Balloon Rendering
BALLOON_RADIUS_RATIO = 0.012  # 1.2% of image width
BALLOON_MIN_RADIUS = 16
BALLOON_MAX_RADIUS = 32

# Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.85
MEDIUM_CONFIDENCE_THRESHOLD = 0.70

# Paths
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# Export
AS9102_COLUMNS = [
    "Char No",
    "Reference Location", 
    "Characteristic Designator",
    "Requirement",
    "Results",
    "Tool Used",
    "Non-Conformance"
]
