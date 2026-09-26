"""
WATERSCOPE Backend - Satellite & Field Image Schemas
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from backend.schemas.common import ImageType, GPSStatus

class SatelliteSearchRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, example=20.7002)
    longitude: float = Field(..., ge=-180.0, le=180.0, example=77.0082)
    target_date: datetime = Field(default_factory=datetime.utcnow)
    window_days: int = Field(15, ge=1, le=60, example=15)
    max_cloud_cover: float = Field(30.0, ge=0.0, le=100.0)
    provider: Optional[str] = "demo"

class SatelliteSceneItem(BaseModel):
    scene_id: str
    provider: str
    acquisition_date: str
    cloud_cover: float
    resolution_meters: float
    geometry: Optional[Dict[str, Any]] = None
    thumbnail: Optional[str] = None
    bands: List[str] = []

class SatelliteCompareRequest(BaseModel):
    before_scene_id: str
    after_scene_id: str
    latitude: float
    longitude: float
    buffer_distance_meters: int = 500

class FieldImageResponse(BaseModel):
    id: str
    intervention_id: Optional[str] = None
    file_path: str
    thumbnail_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_status: GPSStatus
    capture_date: Optional[datetime] = None
    image_type: ImageType
    exif_metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True
