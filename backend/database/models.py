"""
WATERSCOPE Backend - Declarative SQLAlchemy ORM Models
Defines all 14 core database entities for watershed management, GIS, and ML analytics.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Date, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.database.session import Base

# 1. Users
class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(150), nullable=True)
    role = Column(String(50), default="field_officer") # admin, gis_analyst, field_officer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 2. Watersheds
class Watershed(Base):
    __tablename__ = "watersheds"

    id = Column(String(64), primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    river_basin = Column(String(100), nullable=True)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Maharashtra")
    area_hectares = Column(Float, nullable=True)
    geometry_geojson = Column(JSON, nullable=True) # GeoJSON polygon representation
    created_at = Column(DateTime, default=datetime.utcnow)

    sub_watersheds = relationship("SubWatershed", back_populates="watershed", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="watershed")

# 3. Sub-Watersheds
class SubWatershed(Base):
    __tablename__ = "sub_watersheds"

    id = Column(String(64), primary_key=True)
    watershed_id = Column(String(64), ForeignKey("watersheds.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    drainage_density = Column(Float, nullable=True)
    slope_percentage = Column(Float, nullable=True)
    geometry_geojson = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    watershed = relationship("Watershed", back_populates="sub_watersheds")
    interventions = relationship("Intervention", back_populates="sub_watershed")

# 4. Interventions
class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(String(64), primary_key=True)
    type = Column(String(50), nullable=False) # farm_pond, check_dam, gully_plug, contour_bund, percolation_tank, other
    name = Column(String(150), nullable=False)
    watershed_id = Column(String(64), ForeignKey("watersheds.id", ondelete="SET NULL"), nullable=True)
    sub_watershed_id = Column(String(64), ForeignKey("sub_watersheds.id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_source = Column(String(50), default="GPS") # GPS, DATASET_METADATA, MANUAL
    geometry_geojson = Column(JSON, nullable=True) # GeoJSON Point [lon, lat]
    village = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Maharashtra")
    implementation_date = Column(Date, nullable=True)
    status = Column(String(50), default="active") # proposed, under_construction, active, damaged, demolished
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    watershed = relationship("Watershed", back_populates="interventions")
    sub_watershed = relationship("SubWatershed", back_populates="interventions")
    field_images = relationship("FieldImage", back_populates="intervention")
    analysis_jobs = relationship("AnalysisJob", back_populates="intervention")
    recommendations = relationship("Recommendation", back_populates="intervention")

# 5. Field Images
class FieldImage(Base):
    __tablename__ = "field_images"

    id = Column(String(64), primary_key=True)
    intervention_id = Column(String(64), ForeignKey("interventions.id", ondelete="SET NULL"), nullable=True)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_status = Column(String(50), nullable=False) # GPS_AVAILABLE, GPS_MISSING
    geometry_geojson = Column(JSON, nullable=True)
    capture_date = Column(DateTime, nullable=True)
    image_type = Column(String(20), default="UNKNOWN") # BEFORE, AFTER, UNKNOWN
    exif_metadata = Column(JSON, default={})
    source = Column(String(100), default="field_app")
    created_at = Column(DateTime, default=datetime.utcnow)

    intervention = relationship("Intervention", back_populates="field_images")

# 6. Satellite Scenes
class SatelliteScene(Base):
    __tablename__ = "satellite_scenes"

    id = Column(String(100), primary_key=True)
    provider = Column(String(50), nullable=False) # copernicus, sentinel_hub, bhuvan, demo
    acquisition_date = Column(DateTime, nullable=False)
    cloud_cover = Column(Float, default=0.0)
    resolution_meters = Column(Float, default=10.0)
    geometry_geojson = Column(JSON, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    bands = Column(JSON, default=[])
    file_paths = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

# 7. Analysis Jobs
class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(64), primary_key=True)
    intervention_id = Column(String(64), ForeignKey("interventions.id", ondelete="CASCADE"), nullable=True)
    before_image_id = Column(String(64), ForeignKey("field_images.id", ondelete="SET NULL"), nullable=True)
    after_image_id = Column(String(64), ForeignKey("field_images.id", ondelete="SET NULL"), nullable=True)
    before_scene_id = Column(String(100), ForeignKey("satellite_scenes.id", ondelete="SET NULL"), nullable=True)
    after_scene_id = Column(String(100), ForeignKey("satellite_scenes.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED, GPS_MISMATCH
    mode = Column(String(50), default="satellite") # satellite, field
    location_difference_meters = Column(Float, nullable=True)
    temporal_difference_days = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intervention = relationship("Intervention", back_populates="analysis_jobs")
    ml_predictions = relationship("MLPrediction", back_populates="analysis_job")
    spatial_metrics = relationship("SpatialMetric", back_populates="analysis_job")
    report = relationship("Report", back_populates="analysis_job", uselist=False)

# 8. ML Predictions
class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(String(64), primary_key=True)
    analysis_job_id = Column(String(64), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    change_class = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_derivation_method = Column(String(100), nullable=True)
    pixel_change_percentage = Column(Float, nullable=True)
    changed_area_m2 = Column(Float, nullable=True)
    class_probabilities = Column(JSON, default={})
    class_pixel_counts = Column(JSON, default={})
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis_job = relationship("AnalysisJob", back_populates="ml_predictions")
    change_masks = relationship("ChangeMask", back_populates="ml_prediction")

# 9. Change Masks
class ChangeMask(Base):
    __tablename__ = "change_masks"

    id = Column(String(64), primary_key=True)
    ml_prediction_id = Column(String(64), ForeignKey("ml_predictions.id", ondelete="CASCADE"), nullable=False)
    mask_type = Column(String(50), nullable=False) # binary, multi_class, color_overlay
    file_path = Column(String(500), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ml_prediction = relationship("MLPrediction", back_populates="change_masks")

# 10. Spatial Metrics
class SpatialMetric(Base):
    __tablename__ = "spatial_metrics"

    id = Column(String(64), primary_key=True)
    analysis_job_id = Column(String(64), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    buffer_distance_meters = Column(Integer, nullable=False) # 100, 250, 500, 1000
    mean_ndvi_before = Column(Float, nullable=True)
    mean_ndvi_after = Column(Float, nullable=True)
    delta_ndvi = Column(Float, nullable=True)
    mean_ndwi_before = Column(Float, nullable=True)
    mean_ndwi_after = Column(Float, nullable=True)
    delta_ndwi = Column(Float, nullable=True)
    water_extent_m2_before = Column(Float, nullable=True)
    water_extent_m2_after = Column(Float, nullable=True)
    delta_water_extent_m2 = Column(Float, nullable=True)
    vegetation_extent_m2_before = Column(Float, nullable=True)
    vegetation_extent_m2_after = Column(Float, nullable=True)
    delta_vegetation_extent_m2 = Column(Float, nullable=True)
    methodology = Column(String(100), default="Sentinel-2 Multispectral Raster Calculation")
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis_job = relationship("AnalysisJob", back_populates="spatial_metrics")

# 11. Recommendations
class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(64), primary_key=True)
    intervention_id = Column(String(64), ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False)
    analysis_job_id = Column(String(64), ForeignKey("analysis_jobs.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False) # desiltation, embankment_repair, re_excavation, field_validation_required
    priority = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    rationale = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    intervention = relationship("Intervention", back_populates="recommendations")

# 12. Reports
class Report(Base):
    __tablename__ = "reports"

    id = Column(String(64), primary_key=True)
    analysis_job_id = Column(String(64), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    verdict = Column(String(100), nullable=False) # OBSERVED IMPROVEMENT, OBSERVED DEGRADATION, NO SIGNIFICANT OBSERVED CHANGE, INSUFFICIENT EVIDENCE
    composite_score = Column(Float, nullable=False)
    components_breakdown = Column(JSON, default={})
    scientific_limitation_notice = Column(Text, nullable=False)
    report_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis_job = relationship("AnalysisJob", back_populates="report")

# 13. Data Sources
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False) # satellite, dataset, weather, elevation
    provider = Column(String(100), nullable=False)
    resolution_details = Column(String(100), nullable=True)
    update_frequency = Column(String(50), nullable=True)
    license = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 14. Model Versions
class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(64), primary_key=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    architecture = Column(String(150), nullable=True)
    dataset_name = Column(String(100), nullable=True)
    dataset_version = Column(String(50), nullable=True)
    mIoU = Column(Float, nullable=True)
    pixel_accuracy = Column(Float, nullable=True)
    file_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
