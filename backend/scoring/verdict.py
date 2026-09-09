"""
WATERSCOPE Scoring Engine - Non-Causal Verdict & Explanation Generator
Determines scientific verdicts, human-readable explanations, and dynamic evidence narratives
based strictly on measured bi-temporal indicators and sensor data quality.
"""

from typing import Dict, Any, Tuple
from backend.scoring.evidence import SiteEvidence

# Configurable Thresholds
THRESHOLD_IMPROVEMENT = 75.0
THRESHOLD_MODERATE = 50.0
THRESHOLD_MIN_DATA_QUALITY = 45.0
THRESHOLD_MIN_CONFIDENCE = 0.40

def evaluate_verdict(
    composite_score: float,
    evidence: SiteEvidence,
    data_quality_score: float
) -> Tuple[str, str, Dict[str, str]]:
    """
    Evaluates observed bi-temporal verdict, dynamic narrative, and per-component explanations.
    Uses strictly non-causal scientific terminology:
      - 'OBSERVED IMPROVEMENT'
      - 'MODERATE OBSERVED CHANGE'
      - 'NO SIGNIFICANT OBSERVED CHANGE'
      - 'OBSERVED DEGRADATION'
      - 'INSUFFICIENT EVIDENCE'
    """
    c_class = (evidence.change_class or "").lower()
    delta_w = evidence.water_area_change_m2
    delta_ndvi = evidence.ndvi_change
    conf = evidence.ml_confidence

    # 1. Missing evidence or low data quality triggers INSUFFICIENT EVIDENCE
    if data_quality_score < THRESHOLD_MIN_DATA_QUALITY or conf < THRESHOLD_MIN_CONFIDENCE or len(evidence.missing_fields) >= 2:
        verdict = "INSUFFICIENT EVIDENCE"
        narrative = (
            f"Sensor quality ({data_quality_score:.1f}/100) or visual evidence is insufficient to confirm structural intervention. "
            f"Field verification is required due to missing {', '.join(evidence.missing_fields) if evidence.missing_fields else 'optical bands'}."
        )
    # 2. Negative evidence across multiple indicators triggers OBSERVED DEGRADATION
    elif ("demolished" in c_class or "dried" in c_class) or (delta_w < -100.0 and delta_ndvi < -0.05) or composite_score < 40.0:
        verdict = "OBSERVED DEGRADATION"
        if delta_w < 0:
            narrative = f"Observed reduction in localized water surface retention ({delta_w:+,.0f} m²) and desiccation trend detected between acquisitions."
        else:
            narrative = f"Observed structural degradation or demolition of basin detected with reduced moisture presence."
    # 3. Strong positive composite score triggers OBSERVED IMPROVEMENT
    elif composite_score >= THRESHOLD_IMPROVEMENT:
        verdict = "OBSERVED IMPROVEMENT"
        narrative = (
            f"Observed {c_class.replace('_', ' ')} with surface water retention expanding by {delta_w:+,.0f} m² "
            f"and perimeter vegetative vigour shifting by {delta_ndvi:+.2f} NDVI within the 250m analysis buffer."
        )
    # 4. Moderate change
    elif composite_score >= THRESHOLD_MODERATE:
        verdict = "MODERATE OBSERVED CHANGE"
        narrative = (
            f"Moderate observed surface change detected ({delta_w:+,.0f} m² water extent delta, {delta_ndvi:+.2f} NDVI shift). "
            f"Subtle hydrological response observed; routine seasonal monitoring advised."
        )
    # 5. Baseline stable / No significant change
    else:
        verdict = "NO SIGNIFICANT OBSERVED CHANGE"
        narrative = "No significant bi-temporal surface water or structural alterations observed within the intervention perimeter."

    # 2. Component Explanations (Site-Specific)
    explanations = {
        "ml_change": _explain_ml(c_class, conf, evidence.changed_area_m2),
        "water_retention": _explain_water(delta_w, evidence.ndwi_change, evidence.before_water_area_m2),
        "vegetation": _explain_veg(delta_ndvi),
        "data_quality": _explain_quality(data_quality_score, evidence)
    }

    return verdict, narrative, explanations

def _explain_ml(c_class: str, conf: float, area_m2: float) -> str:
    conf_pct = conf * 100.0 if conf <= 1.0 else conf
    clean_cls = c_class.replace("_", " ").title()
    if area_m2 > 0:
        return f"{conf_pct:.1f}% confidence detection of {clean_cls} spanning ~{area_m2:,.0f} m²"
    return f"{conf_pct:.1f}% confidence detection of {clean_cls}"

def _explain_water(delta_w: float, delta_ndwi: float, before_w: float) -> str:
    if delta_w > 0:
        return f"Water extent expanded by +{delta_w:,.0f} m² (NDWI shift: {delta_ndwi:+.2f})"
    elif delta_w < 0:
        return f"Water extent contracted by {delta_w:,.0f} m² (NDWI shift: {delta_ndwi:+.2f})"
    else:
        return f"No net water area change detected (NDWI baseline: {delta_ndwi:+.2f})"

def _explain_veg(delta_ndvi: float) -> str:
    if delta_ndvi > 0.05:
        return f"Perimeter canopy vigour increased by +{delta_ndvi:.2f} NDVI"
    elif delta_ndvi < -0.05:
        return f"Perimeter canopy vigour decreased by {delta_ndvi:.2f} NDVI"
    else:
        return f"Perimeter vegetation stable (NDVI delta: {delta_ndvi:+.2f})"

def _explain_quality(score: float, ev: SiteEvidence) -> str:
    reasons = []
    if ev.has_gps:
        reasons.append("verified GPS")
    if ev.cloud_cover_pct <= 5.0:
        reasons.append("cloud-free")
    if ev.resolution_m <= 1.5:
        reasons.append(f"{ev.resolution_m}m resolution")
    if ev.missing_fields:
        reasons.append(f"missing {', '.join(ev.missing_fields)}")
    return f"Score {score:.0f}/100 based on {', '.join(reasons)}"
