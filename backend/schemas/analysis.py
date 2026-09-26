"""
WATERSCOPE Backend - Analysis & Reporting Pydantic Schemas
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from backend.schemas.common import AnalysisStatus

class AnalysisCreateRequest(BaseModel):
    intervention_id: Optional[str] = None
    before_image_id: Optional[str] = None
    after_image_id: Optional[str] = None
    before_image_path: Optional[str] = None
    after_image_path: Optional[str] = None
    mode: str = Field("satellite", example="satellite") # satellite, field
    buffer_distances: List[int] = [100, 250, 500, 1000]

class SpatialMetricItem(BaseModel):
    buffer_distance_meters: int
    mean_ndvi_before: Optional[float]
    mean_ndvi_after: Optional[float]
    delta_ndvi: Optional[float]
    mean_ndwi_before: Optional[float]
    mean_ndwi_after: Optional[float]
    delta_ndwi: Optional[float]
    water_extent_m2_before: Optional[float]
    water_extent_m2_after: Optional[float]
    delta_water_extent_m2: Optional[float]
    vegetation_extent_m2_before: Optional[float]
    vegetation_extent_m2_after: Optional[float]
    delta_vegetation_extent_m2: Optional[float]
    methodology: str

class MLPredictionResponse(BaseModel):
    change_class: str
    confidence: float
    confidence_derivation_method: Optional[str]
    pixel_change_percentage: Optional[float]
    changed_area_m2: Optional[float]
    class_probabilities: Dict[str, float] = {}
    model_name: str
    model_version: str

class ObservedImpactResponse(BaseModel):
    verdict: str
    verdict_type: str = "OBSERVED_CHANGE"
    composite_score: float
    composite_index: Optional[float] = None
    scoring_version: Optional[str] = "v2.0"
    ml_change_score: Optional[float] = None
    water_retention_score: Optional[float] = None
    vegetation_score: Optional[float] = None
    data_quality_score: Optional[float] = None
    narrative: str
    components: Dict[str, Any]
    evidence: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    provenance_metrics: List[Dict[str, Any]] = []
    scientific_disclaimer: Optional[str] = None

class AnalysisJobResponse(BaseModel):
    id: str
    status: AnalysisStatus
    mode: str
    intervention_id: Optional[str] = None
    location_difference_meters: Optional[float] = None
    temporal_difference_days: Optional[int] = None
    ml_prediction: Optional[MLPredictionResponse] = None
    spatial_metrics: List[SpatialMetricItem] = []
    observed_impact: Optional[ObservedImpactResponse] = None
    change_mask_url: Optional[str] = None
    overlay_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ReportGenerateRequest(BaseModel):
    analysis_job_id: str
    title: Optional[str] = None
