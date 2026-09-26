-- ==========================================================
-- WATERSCOPE - PostGIS Database Schema
-- Version: 1.0.0
-- Dialect: PostgreSQL 14+ with PostGIS 3+
-- ==========================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(150),
    role VARCHAR(50) DEFAULT 'field_officer', -- 'admin', 'gis_analyst', 'field_officer'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Watersheds Table
CREATE TABLE IF NOT EXISTS watersheds (
    id VARCHAR(64) PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    river_basin VARCHAR(100),
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL DEFAULT 'Maharashtra',
    area_hectares DOUBLE PRECISION,
    geometry GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_watersheds_geom ON watersheds USING GIST (geometry);

-- 3. Sub-Watersheds Table
CREATE TABLE IF NOT EXISTS sub_watersheds (
    id VARCHAR(64) PRIMARY KEY,
    watershed_id VARCHAR(64) REFERENCES watersheds(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    drainage_density DOUBLE PRECISION,
    slope_percentage DOUBLE PRECISION,
    geometry GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sub_watersheds_geom ON sub_watersheds USING GIST (geometry);

-- 4. Interventions Table
CREATE TABLE IF NOT EXISTS interventions (
    id VARCHAR(64) PRIMARY KEY,
    type VARCHAR(50) NOT NULL, -- farm_pond, check_dam, gully_plug, contour_bund, percolation_tank, other
    name VARCHAR(150) NOT NULL,
    watershed_id VARCHAR(64) REFERENCES watersheds(id) ON DELETE SET NULL,
    sub_watershed_id VARCHAR(64) REFERENCES sub_watersheds(id) ON DELETE SET NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location_source VARCHAR(50) DEFAULT 'GPS', -- 'GPS', 'DATASET_METADATA', 'MANUAL'
    geometry GEOMETRY(Point, 4326),
    village VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL DEFAULT 'Maharashtra',
    implementation_date DATE,
    status VARCHAR(50) DEFAULT 'active', -- 'proposed', 'under_construction', 'active', 'damaged', 'demolished'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_interventions_geom ON interventions USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_interventions_type ON interventions(type);
CREATE INDEX IF NOT EXISTS idx_interventions_district ON interventions(district);

-- 5. Field Images Table
CREATE TABLE IF NOT EXISTS field_images (
    id VARCHAR(64) PRIMARY KEY,
    intervention_id VARCHAR(64) REFERENCES interventions(id) ON DELETE SET NULL,
    file_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    gps_status VARCHAR(50) NOT NULL, -- 'GPS_AVAILABLE', 'GPS_MISSING'
    geometry GEOMETRY(Point, 4326),
    capture_date TIMESTAMP WITH TIME ZONE,
    image_type VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN', -- 'BEFORE', 'AFTER', 'UNKNOWN'
    exif_metadata JSONB DEFAULT '{}'::jsonb,
    source VARCHAR(100) DEFAULT 'field_app',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_field_images_geom ON field_images USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_field_images_intervention ON field_images(intervention_id);

-- 6. Satellite Scenes Table
CREATE TABLE IF NOT EXISTS satellite_scenes (
    id VARCHAR(100) PRIMARY KEY, -- Sentinel / STAC scene identifier
    provider VARCHAR(50) NOT NULL, -- 'copernicus', 'sentinel_hub', 'bhuvan', 'demo'
    acquisition_date TIMESTAMP WITH TIME ZONE NOT NULL,
    cloud_cover DOUBLE PRECISION DEFAULT 0.0,
    resolution_meters DOUBLE PRECISION DEFAULT 10.0,
    geometry GEOMETRY(Polygon, 4326),
    thumbnail_url VARCHAR(500),
    bands JSONB DEFAULT '[]'::jsonb,
    file_paths JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_satellite_scenes_geom ON satellite_scenes USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_satellite_scenes_date ON satellite_scenes(acquisition_date);

-- 7. Analysis Jobs Table
CREATE TABLE IF NOT EXISTS analysis_jobs (
    id VARCHAR(64) PRIMARY KEY,
    intervention_id VARCHAR(64) REFERENCES interventions(id) ON DELETE CASCADE,
    before_image_id VARCHAR(64) REFERENCES field_images(id) ON DELETE SET NULL,
    after_image_id VARCHAR(64) REFERENCES field_images(id) ON DELETE SET NULL,
    before_scene_id VARCHAR(100) REFERENCES satellite_scenes(id) ON DELETE SET NULL,
    after_scene_id VARCHAR(100) REFERENCES satellite_scenes(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED, GPS_MISMATCH
    mode VARCHAR(50) DEFAULT 'satellite', -- 'satellite', 'field'
    location_difference_meters DOUBLE PRECISION,
    temporal_difference_days INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. ML Predictions Table
CREATE TABLE IF NOT EXISTS ml_predictions (
    id VARCHAR(64) PRIMARY KEY,
    analysis_job_id VARCHAR(64) REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    change_class VARCHAR(100) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    confidence_derivation_method VARCHAR(100),
    pixel_change_percentage DOUBLE PRECISION,
    changed_area_m2 DOUBLE PRECISION,
    class_probabilities JSONB DEFAULT '{}'::jsonb,
    class_pixel_counts JSONB DEFAULT '{}'::jsonb,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Change Masks Table
CREATE TABLE IF NOT EXISTS change_masks (
    id VARCHAR(64) PRIMARY KEY,
    ml_prediction_id VARCHAR(64) REFERENCES ml_predictions(id) ON DELETE CASCADE,
    mask_type VARCHAR(50) NOT NULL, -- 'binary', 'multi_class', 'color_overlay'
    file_path VARCHAR(500) NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Spatial Metrics Table
CREATE TABLE IF NOT EXISTS spatial_metrics (
    id VARCHAR(64) PRIMARY KEY,
    analysis_job_id VARCHAR(64) REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    buffer_distance_meters INTEGER NOT NULL, -- 100, 250, 500, 1000
    mean_ndvi_before DOUBLE PRECISION,
    mean_ndvi_after DOUBLE PRECISION,
    delta_ndvi DOUBLE PRECISION,
    mean_ndwi_before DOUBLE PRECISION,
    mean_ndwi_after DOUBLE PRECISION,
    delta_ndwi DOUBLE PRECISION,
    water_extent_m2_before DOUBLE PRECISION,
    water_extent_m2_after DOUBLE PRECISION,
    delta_water_extent_m2 DOUBLE PRECISION,
    vegetation_extent_m2_before DOUBLE PRECISION,
    vegetation_extent_m2_after DOUBLE PRECISION,
    delta_vegetation_extent_m2 DOUBLE PRECISION,
    methodology VARCHAR(100) DEFAULT 'Sentinel-2 Multispectral Raster Calculation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id VARCHAR(64) PRIMARY KEY,
    intervention_id VARCHAR(64) REFERENCES interventions(id) ON DELETE CASCADE,
    analysis_job_id VARCHAR(64) REFERENCES analysis_jobs(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL, -- 'desiltation', 'embankment_repair', 're_excavation', 'field_validation_required'
    priority VARCHAR(20) DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    rationale TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(64) PRIMARY KEY,
    analysis_job_id VARCHAR(64) REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    verdict VARCHAR(100) NOT NULL, -- 'OBSERVED IMPROVEMENT', 'OBSERVED DEGRADATION', 'NO SIGNIFICANT OBSERVED CHANGE', 'INSUFFICIENT EVIDENCE'
    composite_score DOUBLE PRECISION NOT NULL,
    components_breakdown JSONB DEFAULT '{}'::jsonb,
    scientific_limitation_notice TEXT NOT NULL,
    report_file_path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. Data Sources Table
CREATE TABLE IF NOT EXISTS data_sources (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'satellite', 'dataset', 'weather', 'elevation'
    provider VARCHAR(100) NOT NULL,
    resolution_details VARCHAR(100),
    update_frequency VARCHAR(50),
    license VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. Model Versions Table
CREATE TABLE IF NOT EXISTS model_versions (
    id VARCHAR(64) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    architecture VARCHAR(150),
    dataset_name VARCHAR(100),
    dataset_version VARCHAR(50),
    mIoU DOUBLE PRECISION,
    pixel_accuracy DOUBLE PRECISION,
    file_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
