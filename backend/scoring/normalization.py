"""
WATERSCOPE Scoring Engine - Mathematical Normalization Utilities
Provides robust, bounded, deterministic normalization functions for remote sensing,
spectral indices (NDVI/NDWI), pixel change percentages, and multi-sensor data quality.
"""

from typing import Optional

def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamps a floating point value to [min_val, max_val]. Guarantees finite return."""
    if value is None or not isinstance(value, (int, float)):
        return min_val
    import math
    if math.isnan(value) or math.isinf(value):
        return min_val
    return max(min_val, min(max_val, float(value)))

def normalize_linear(value: float, min_val: float, max_val: float) -> float:
    """Linearly scales a value from [min_val, max_val] to [0.0, 100.0]."""
    if max_val <= min_val:
        return 50.0
    scaled = ((value - min_val) / (max_val - min_val)) * 100.0
    return clamp(scaled, 0.0, 100.0)

def normalize_ml_change(
    change_class: str,
    confidence: float,
    pixel_change_pct: float,
    changed_area_m2: float
) -> float:
    """
    Computes normalized ML Change Score (0 - 100).
    Takes into account change taxonomy, spatial extent, and calibrated model confidence.
    
    Positive directions:
      - Constructed: positive intervention (+ earthwork + basin)
      - Wetted: positive hydrological recharge (+ water retention)
    Negative directions:
      - Demolished: structural loss or decommissioning
      - Dried: desiccation / seasonal failure
    Neutral:
      - Background / No Change: baseline stability
    """
    c_class = (change_class or "background").lower()
    conf = clamp(confidence * 100.0 if confidence <= 1.0 else confidence, 0.0, 100.0)
    
    # Area scaling factor (logarithmic saturation around 2,500 m2)
    import math
    area_factor = min(1.0, math.log10(max(10.0, changed_area_m2)) / 3.4) if changed_area_m2 > 0 else 0.0
    
    if "constructed" in c_class:
        # Range: 60.0 to 100.0 based on confidence and extent
        base = 65.0 + (conf * 0.25) + (area_factor * 10.0)
        return clamp(base, 0.0, 100.0)
    elif "wetted" in c_class:
        # Range: 55.0 to 95.0
        base = 60.0 + (conf * 0.25) + (area_factor * 10.0)
        return clamp(base, 0.0, 100.0)
    elif "demolished" in c_class:
        # Structural degradation: lowers score
        base = 35.0 - (conf * 0.20) - (area_factor * 10.0)
        return clamp(base, 0.0, 100.0)
    elif "dried" in c_class:
        # Water loss: lowers score
        base = 40.0 - (conf * 0.20) - (area_factor * 10.0)
        return clamp(base, 0.0, 100.0)
    else:
        # Background / No Change: neutral score centered at 50.0
        return 50.0

def normalize_water_retention(
    delta_water_m2: float,
    delta_ndwi: float,
    before_water_m2: float = 0.0,
    change_class: Optional[str] = None
) -> float:
    """
    Computes site-specific Water Retention Score (0 - 100).
    Uses physical water surface area difference and NDWI spectral response.
    
    - Accounts for zero before-water baseline (new construction).
    - Large positive deltas (+1,240 m2) score higher than minor deltas (+150 m2).
    - Negative deltas (-300 m2) reduce the score significantly.
    """
    delta_w = float(delta_water_m2 or 0.0)
    delta_i = float(delta_ndwi or 0.0)
    before_w = max(0.0, float(before_water_m2 or 0.0))
    
    # 1. Area contribution (baseline 50.0 = zero change)
    # Saturation at +2,000 m2 for +40 points, -1,000 m2 for -40 points
    if delta_w >= 0:
        area_points = min(40.0, (delta_w / 2000.0) * 40.0)
    else:
        area_points = max(-40.0, (delta_w / 1000.0) * 40.0)
        
    # 2. NDWI spectral contribution (-1.0 to 1.0)
    # A +0.20 NDWI shift provides +10 points; negative NDWI penalizes
    ndwi_points = max(-15.0, min(15.0, delta_i * 50.0))
    
    # 3. New pond bonus if before was 0 and positive water observed
    construction_bonus = 5.0 if (before_w == 0.0 and delta_w > 50.0) else 0.0
    
    raw_score = 50.0 + area_points + ndwi_points + construction_bonus
    return clamp(round(raw_score, 2), 0.0, 100.0)

def normalize_vegetation(
    delta_ndvi: float,
    delta_veg_m2: float = 0.0,
    before_ndvi: float = 0.30
) -> float:
    """
    Computes site-specific Vegetation Vigour Score (0 - 100).
    Uses mean perimeter NDVI change and canopy surface area growth.
    
    - Neutral midpoint is 50.0.
    - NDVI +0.18 yields a significantly higher score than +0.02.
    - Negative NDVI reduces the score.
    """
    d_ndvi = float(delta_ndvi or 0.0)
    d_veg = float(delta_veg_m2 or 0.0)
    
    # NDVI delta contribution: +0.25 delta adds +35 points, -0.20 subtracts -35 points
    if d_ndvi >= 0:
        ndvi_points = min(35.0, (d_ndvi / 0.25) * 35.0)
    else:
        ndvi_points = max(-35.0, (d_ndvi / 0.20) * 35.0)
        
    # Spatial canopy extent contribution (up to +/- 15 points)
    if d_veg >= 0:
        veg_points = min(15.0, (d_veg / 1500.0) * 15.0)
    else:
        veg_points = max(-15.0, (d_veg / 1000.0) * 15.0)
        
    raw_score = 50.0 + ndvi_points + veg_points
    return clamp(round(raw_score, 2), 0.0, 100.0)

def normalize_data_quality(
    has_gps: bool = True,
    has_dates: bool = True,
    has_before_image: bool = True,
    has_after_image: bool = True,
    has_satellite_scene: bool = True,
    resolution_m: float = 1.0,
    cloud_cover_pct: float = 0.0,
    image_quality_score: float = 0.95,
    temporal_gap_days: Optional[int] = None
) -> float:
    """
    Computes site-specific Data Quality & Confidence Score (0 - 100).
    Evaluates sensory provenance, spatial resolution, temporal validity, and missing assets.
    """
    score = 100.0
    
    # Missing primary images: severe penalty
    if not has_before_image:
        score -= 35.0
    if not has_after_image:
        score -= 40.0
        
    # Spatial / GPS verification
    if not has_gps:
        score -= 20.0
        
    # EXIF date verification
    if not has_dates:
        score -= 10.0
        
    # Satellite scene availability
    if not has_satellite_scene:
        score -= 10.0
        
    # Sensor resolution penalties (1.0m is standard, >10.0m degrades score)
    if resolution_m > 5.0:
        res_penalty = min(15.0, (resolution_m - 5.0) * 1.5)
        score -= res_penalty
        
    # Cloud coverage penalty (0% = 0, 50% = -20)
    if cloud_cover_pct > 0.0:
        cloud_penalty = min(25.0, (cloud_cover_pct / 50.0) * 25.0)
        score -= cloud_penalty
        
    # Field image optical quality (Laplacian blur / exposure factor, 0.0 to 1.0)
    quality_factor = clamp(image_quality_score if image_quality_score <= 1.0 else image_quality_score / 100.0, 0.0, 1.0)
    score = score * (0.60 + 0.40 * quality_factor)
    
    return clamp(round(score, 2), 0.0, 100.0)
