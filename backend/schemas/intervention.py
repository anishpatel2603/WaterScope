"""
WATERSCOPE Backend - Intervention Pydantic Schemas
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime
from pydantic import BaseModel, Field
from backend.schemas.common import InterventionType

class InterventionBase(BaseModel):
    type: InterventionType = InterventionType.farm_pond
    name: str = Field(..., example="Farm Pond #FP-001 (Akhatwada)")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    village: str = Field(..., example="Akhatwada")
    district: str = Field(..., example="Akola")
    state: str = Field("Maharashtra")
    implementation_date: Optional[date] = None
    status: str = Field("active", example="active")
    description: Optional[str] = None
    watershed_id: Optional[str] = None

class InterventionCreate(InterventionBase):
    pass

class InterventionResponse(InterventionBase):
    id: str
    location_source: str = "GPS"
    geometry_geojson: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    pair_key: Optional[str] = None
    t0_url: Optional[str] = None
    t1_url: Optional[str] = None
    mask_url: Optional[str] = None
    t0_date: Optional[str] = None
    t1_date: Optional[str] = None
    change_class: Optional[str] = None
    observed_impact: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class InterventionListResponse(BaseModel):
    total: int
    items: List[InterventionResponse]
