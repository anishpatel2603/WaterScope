"""
WATERSCOPE Demo Sites Specification (v2.0)
Defines 5 deterministic, realistic benchmark demonstration sites.
Crucial: Final Composite Index scores are NEVER hardcoded.
Each site defines its own raw bi-temporal telemetry, which is then
processed through the SiteSpecificScoringEngine to dynamically generate
site-specific scores, narratives, and scientific verdicts.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Dict, Any
from backend.scoring.evidence import SiteEvidence
from backend.scoring.scoring_engine import default_scoring_engine

RAW_DEMO_TELEMETRY: Dict[str, Dict[str, Any]] = {
    "demo_site_001": {
        "name": "Farm Pond Akola East (FP-001)",
        "village": "Akhatwada",
        "district": "Akola",
        "evidence": SiteEvidence(
            before_water_area_m2=0.0,
            after_water_area_m2=1650.0,
            water_area_change_m2=1650.0,
            water_area_change_percent=100.0,
            ndvi_before=0.28,
            ndvi_after=0.44,
            ndvi_change=0.16,
            ndwi_before=-0.18,
            ndwi_after=0.30,
            ndwi_change=0.48,
            change_class="farm_pond_constructed",
            changed_area_m2=1650.0,
            ml_confidence=0.92,
            quality_score=0.96,
            resolution_m=1.0,
            cloud_cover_pct=0.0,
            has_gps=True,
            has_valid_dates=True
        )
    },
    "demo_site_002": {
        "name": "Check Dam Reservoir Takarkheda (CD-042)",
        "village": "Takarkheda",
        "district": "Amravati",
        "evidence": SiteEvidence(
            before_water_area_m2=120.0,
            after_water_area_m2=540.0,
            water_area_change_m2=420.0,
            water_area_change_percent=350.0,
            ndvi_before=0.34,
            ndvi_after=0.41,
            ndvi_change=0.07,
            ndwi_before=-0.05,
            ndwi_after=0.17,
            ndwi_change=0.22,
            change_class="farm_pond_wetted",
            changed_area_m2=420.0,
            ml_confidence=0.86,
            quality_score=0.90,
            resolution_m=1.0,
            cloud_cover_pct=2.0,
            has_gps=True,
            has_valid_dates=True
        )
    },
    "demo_site_003": {
        "name": "Contour Bund Baseline Parcel (CB-108)",
        "village": "Dabhadi",
        "district": "Washim",
        "evidence": SiteEvidence(
            before_water_area_m2=0.0,
            after_water_area_m2=0.0,
            water_area_change_m2=0.0,
            water_area_change_percent=0.0,
            ndvi_before=0.31,
            ndvi_after=0.33,
            ndvi_change=0.02,
            ndwi_before=-0.14,
            ndwi_after=-0.15,
            ndwi_change=-0.01,
            change_class="background",
            changed_area_m2=0.0,
            ml_confidence=0.89,
            quality_score=0.92,
            resolution_m=1.0,
            cloud_cover_pct=0.0,
            has_gps=True,
            has_valid_dates=True
        )
    },
    "demo_site_004": {
        "name": "Seasonal Basin Drying (FP-215)",
        "village": "Ghusar",
        "district": "Akola",
        "evidence": SiteEvidence(
            before_water_area_m2=980.0,
            after_water_area_m2=0.0,
            water_area_change_m2=-980.0,
            water_area_change_percent=-100.0,
            ndvi_before=0.38,
            ndvi_after=0.29,
            ndvi_change=-0.09,
            ndwi_before=0.25,
            ndwi_after=-0.17,
            ndwi_change=-0.42,
            change_class="farm_pond_dried",
            changed_area_m2=980.0,
            ml_confidence=0.88,
            quality_score=0.91,
            resolution_m=1.0,
            cloud_cover_pct=1.0,
            has_gps=True,
            has_valid_dates=True
        )
    },
    "demo_site_005": {
        "name": "Degraded Embankment Cloud Obscured (UNV-901)",
        "village": "Babhali",
        "district": "Washim",
        "evidence": SiteEvidence(
            before_water_area_m2=1200.0,
            after_water_area_m2=0.0,
            water_area_change_m2=-1200.0,
            water_area_change_percent=-100.0,
            ndvi_before=0.35,
            ndvi_after=0.21,
            ndvi_change=-0.14,
            ndwi_before=0.20,
            ndwi_after=-0.28,
            ndwi_change=-0.48,
            change_class="farm_pond_demolished",
            changed_area_m2=1200.0,
            ml_confidence=0.45,
            quality_score=0.38,
            resolution_m=10.0,
            cloud_cover_pct=35.0,
            has_gps=False,
            has_valid_dates=True,
            missing_fields=["gps_coordinates", "cloud_free_imagery"]
        )
    }
}

def get_demo_site_scores() -> Dict[str, Dict[str, Any]]:
    """
    Computes and returns the generated scores for all demo sites.
    Ensures identical scoring pipeline is used for demo and production data.
    """
    results = {}
    for site_key, data in RAW_DEMO_TELEMETRY.items():
        score_obj = default_scoring_engine.compute_site_score(
            site_id=site_key,
            evidence=data["evidence"]
        )
        score_obj["site_name"] = data["name"]
        score_obj["village"] = data["village"]
        score_obj["district"] = data["district"]
        results[site_key] = score_obj
    return results

if __name__ == "__main__":
    scores = get_demo_site_scores()
    print("==================================================")
    print("DEMO SITES GENERATED VIA SCORING ENGINE (v2.0)")
    print("==================================================")
    for sid, s in scores.items():
        print(f"[{sid}] {s['site_name']}")
        print(f"  Composite Index:       {s['composite_index']} / 100")
        print(f"  Verdict:               {s['verdict']}")
        print(f"  ML Change:             {s['ml_change_score']}%")
        print(f"  Water Retention:       {s['water_retention_score']}%")
        print(f"  Vegetation:            {s['vegetation_score']}%")
        print(f"  Data Quality:          {s['data_quality_score']}%")
        print(f"  Narrative:             {s['narrative']}")
        print()
