"""
WATERSCOPE Backend - Configuration Management
Loads application settings, provider credentials, database URIs, and storage directories.
"""

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

class Settings(BaseModel):
    PROJECT_NAME: str = "WATERSCOPE"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'waterscope.db'}")
    
    # Storage
    DATA_DIR: Path = PROJECT_ROOT / "data"
    UPLOAD_DIR: Path = PROJECT_ROOT / "data" / "uploads"
    THUMBNAIL_DIR: Path = PROJECT_ROOT / "data" / "uploads" / "thumbnails"
    REPORT_DIR: Path = PROJECT_ROOT / "data" / "reports"
    CACHE_DIR: Path = PROJECT_ROOT / "data" / "cache"
    FPCD_LOCAL_PATH: Path = PROJECT_ROOT / "data" / "fpcd"
    
    # ML Service Contract
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8000")
    FPCD_DATASET_ID: str = os.getenv("FPCD_DATASET_ID", "ctundia/FPCD")
    DATASET_AUTO_SYNC: bool = os.getenv("DATASET_AUTO_SYNC", "true").lower() == "true"
    
    # Satellite Providers
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"
    COPERNICUS_CLIENT_ID: str = os.getenv("COPERNICUS_CLIENT_ID", "")
    COPERNICUS_CLIENT_SECRET: str = os.getenv("COPERNICUS_CLIENT_SECRET", "")
    COPERNICUS_STAC_URL: str = os.getenv("COPERNICUS_STAC_URL", "https://catalogue.dataspace.copernicus.eu/stac")
    SENTINEL_HUB_CLIENT_ID: str = os.getenv("SENTINEL_HUB_CLIENT_ID", "")
    SENTINEL_HUB_CLIENT_SECRET: str = os.getenv("SENTINEL_HUB_CLIENT_SECRET", "")
    SENTINEL_HUB_INSTANCE_ID: str = os.getenv("SENTINEL_HUB_INSTANCE_ID", "")
    BHUVAN_API_TOKEN: str = os.getenv("BHUVAN_API_TOKEN", "")
    SRISHTI_DRISHTI_ENABLED: bool = os.getenv("SRISHTI_DRISHTI_ENABLED", "false").lower() == "true"
    SRISHTI_DRISHTI_BASE_URL: str = os.getenv("SRISHTI_DRISHTI_BASE_URL", "")
    SRISHTI_DRISHTI_API_KEY: str = os.getenv("SRISHTI_DRISHTI_API_KEY", "")
    NASA_POWER_BASE_URL: str = os.getenv("NASA_POWER_BASE_URL", "")
    IMD_API_BASE_URL: str = os.getenv("IMD_API_BASE_URL", "")
    
    # GIS Parameters
    BUFFER_DISTANCES: list = [100, 250, 500, 1000] # meters
    MAX_LOCATION_DIFF_METERS: float = 1000.0 # Flag GPS mismatch if delta > 1km

settings = Settings()

# Ensure directories exist
for p in [settings.DATA_DIR, settings.UPLOAD_DIR, settings.THUMBNAIL_DIR, settings.REPORT_DIR, settings.CACHE_DIR]:
    p.mkdir(parents=True, exist_ok=True)
