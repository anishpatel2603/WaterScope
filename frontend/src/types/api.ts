/**
 * WATERSCOPE - Shared API & Geospatial Data Contract Types
 */

export type InterventionType = 
  | 'farm_pond'
  | 'check_dam'
  | 'gully_plug'
  | 'contour_bund'
  | 'percolation_tank'
  | 'other';

export type InterventionStatus = 'proposed' | 'under_construction' | 'active' | 'damaged' | 'demolished';

export interface Intervention {
  id: string;
  type: InterventionType;
  name: string;
  latitude: number | null;
  longitude: number | null;
  location_source: 'GPS' | 'DATASET_METADATA' | 'MANUAL';
  geometry_geojson?: {
    type: string;
    coordinates: [number, number];
  };
  village: string;
  district: string;
  state: string;
  implementation_date: string | null;
  status: InterventionStatus;
  watershed_id?: string | null;
  pair_key?: string | null;
  t0_url?: string | null;
  t1_url?: string | null;
  mask_url?: string | null;
  t0_date?: string | null;
  t1_date?: string | null;
  change_class?: string | null;
  observed_impact?: ObservedImpact;
  created_at: string;
  updated_at: string;
}

export interface Watershed {
  id: string;
  code: string;
  name: string;
  river_basin: string;
  district: string;
  state: string;
  area_hectares: number;
  geometry?: {
    type: string;
    coordinates: any;
  };
  sub_watersheds?: Array<{
    id: string;
    code: string;
    name: string;
    drainage_density?: number;
  }>;
}

export interface FieldImage {
  id: string;
  intervention_id?: string | null;
  file_path: string;
  thumbnail_path?: string | null;
  latitude: number | null;
  longitude: number | null;
  gps_status: 'GPS_AVAILABLE' | 'GPS_MISSING';
  capture_date: string | null;
  image_type: 'BEFORE' | 'AFTER' | 'UNKNOWN';
  exif_metadata?: Record<string, any>;
  file_url?: string;
  thumbnail_url?: string;
}

export interface SatelliteScene {
  id: string;
  provider: 'copernicus' | 'sentinel_hub' | 'bhuvan' | 'demo';
  acquisition_date: string;
  cloud_cover: number;
  resolution_meters: number;
  geometry?: any;
  thumbnail_url?: string;
  bands?: string[];
}

export interface SpatialMetric {
  buffer_distance_meters: number;
  mean_ndvi_before: number | null;
  mean_ndvi_after: number | null;
  delta_ndvi: number | null;
  mean_ndwi_before: number | null;
  mean_ndwi_after: number | null;
  delta_ndwi: number | null;
  water_extent_m2_before: number | null;
  water_extent_m2_after: number | null;
  delta_water_extent_m2: number | null;
  vegetation_extent_m2_before: number | null;
  vegetation_extent_m2_after: number | null;
  delta_vegetation_extent_m2: number | null;
  methodology: string;
}

export interface MLPrediction {
  change_class: string;
  confidence: number;
  confidence_derivation_method?: string;
  pixel_change_percentage?: number;
  changed_area_m2?: number;
  class_probabilities?: Record<string, number>;
  model_name: string;
  model_version: string;
}

export interface ObservedImpact {
  site_id?: string;
  scoring_version?: string;
  verdict: string;
  verdict_type?: string;
  composite_score: number;
  composite_index?: number;
  ml_change_score?: number;
  water_retention_score?: number;
  vegetation_score?: number;
  data_quality_score?: number;
  narrative: string;
  confidence?: number;
  components: {
    ml_change: { score: number; weight: number };
    water_extent: { score: number; weight: number };
    vegetation_response: { score: number; weight: number };
    model_confidence?: { score: number; weight: number };
    data_quality?: { score: number; weight: number };
  };
  evidence?: {
    before_water_area_m2?: number;
    after_water_area_m2?: number;
    water_area_change_m2?: number;
    water_area_change_percent?: number;
    ndvi_before?: number;
    ndvi_after?: number;
    ndvi_change?: number;
    ndwi_before?: number;
    ndwi_after?: number;
    ndwi_change?: number;
    ml_confidence?: number;
    quality_score?: number;
  };
  explanation?: {
    ml_change?: string;
    water_retention?: string;
    vegetation?: string;
    data_quality?: string;
  };
  provenance_metrics?: Array<{
    metric_name: string;
    value: any;
    unit: string;
    source: string;
    date: string;
    resolution: string;
    confidence: number;
    methodology: string;
  }>;
  data_sources?: string[];
  model_version?: string;
  scientific_disclaimer?: string;
}

export interface AnalysisJob {
  id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'GPS_MISMATCH';
  mode: 'satellite' | 'field';
  intervention_id?: string | null;
  location_difference_meters?: number | null;
  temporal_difference_days?: number | null;
  ml_prediction?: MLPrediction;
  spatial_metrics: SpatialMetric[];
  observed_impact?: ObservedImpact;
  change_mask_url?: string;
  overlay_url?: string;
  t0_url?: string;
  t1_url?: string;
  created_at: string;
  updated_at: string;
}

export interface SystemStatus {
  status: string;
  backend_online: boolean;
  database_connected: boolean;
  postgis_enabled: boolean;
  ml_service_online: boolean;
  satellite_provider: string;
  active_interventions_count: number;
  data_manifest_present: boolean;
  version: string;
}

export interface PriorityZone {
  recommendation_id: string;
  intervention_id: string;
  intervention_name: string;
  village: string;
  district: string;
  action_type: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  rationale: string;
  created_at: string;
}

export interface DataSourceItem {
  id: string;
  name: string;
  type: string;
  provider: string;
  resolution: string;
  update_frequency: string;
  license: string;
  is_active: boolean;
}

export interface PresetItem {
  code: string;
  pair_key: string;
  district: string;
  village: string;
  ground_truth_class: string;
  t0_date: string;
  t1_date: string;
  t0_url: string;
  t1_url: string;
  mask_url?: string;
}
