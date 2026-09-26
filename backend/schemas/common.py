"""
WATERSCOPE Backend - Common Schemas & Enums
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class InterventionType(str, Enum):
    farm_pond = "farm_pond"
    check_dam = "check_dam"
    gully_plug = "gully_plug"
    contour_bund = "contour_bund"
    percolation_tank = "percolation_tank"
    other = "other"

class ImageType(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    UNKNOWN = "UNKNOWN"

class GPSStatus(str, Enum):
    GPS_AVAILABLE = "GPS_AVAILABLE"
    GPS_MISSING = "GPS_MISSING"

class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    GPS_MISMATCH = "GPS_MISMATCH"
    SATELLITE_UNAVAILABLE = "SATELLITE_UNAVAILABLE"
    ML_SERVICE_UNAVAILABLE = "ML_SERVICE_UNAVAILABLE"

class SystemStatusResponse(BaseModel):
    status: str
    backend_online: bool
    database_connected: bool
    postgis_enabled: bool
    ml_service_online: bool
    satellite_provider: str
    active_interventions_count: int
    data_manifest_present: bool
    version: str
