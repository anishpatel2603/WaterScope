"""
WATERSCOPE Unit Tests - Site-Specific Observed Impact Scoring Engine (v2.0)
Tests:
- Determinism (identical inputs -> identical scores)
- Differentiation (different water/NDVI/ML/Quality -> different scores)
- Boundedness (always 0.0 <= score <= 100.0, no NaN, no Inf)
- Correct weight summation (0.35 + 0.30 + 0.20 + 0.15 = 1.00)
- Edge cases (missing data, negative changes, zero baselines)
- Multi-site comparison test (Site A != Site B != Site C != Site D != Site E)
"""

import pytest
import math
from backend.scoring.scoring_engine import SiteSpecificScoringEngine
from backend.scoring.evidence import SiteEvidence
from backend.scoring.normalization import clamp, normalize_water_retention, normalize_vegetation, normalize_data_quality

@pytest.fixture
def engine():
    return SiteSpecificScoringEngine()

def test_weight_summation(engine):
    """Verifies that the 4 component weights sum precisely to 1.00."""
    total = sum(engine.WEIGHTS.values())
    assert abs(total - 1.0) < 1e-6, f"Weights sum to {total}, must be 1.0"
    assert engine.WEIGHTS["ml_change_weight"] == 0.35
    assert engine.WEIGHTS["water_retention_weight"] == 0.30
    assert engine.WEIGHTS["vegetation_weight"] == 0.20
    assert engine.WEIGHTS["data_quality_weight"] == 0.15

def test_identical_inputs_identical_scores(engine):
    """Verifies that the scoring engine is strictly deterministic."""
    ev = SiteEvidence(
        before_water_area_m2=0.0,
        after_water_area_m2=1240.0,
        water_area_change_m2=1240.0,
        ndvi_change=0.14,
        ndwi_change=0.45,
        ml_confidence=0.88,
        change_class="farm_pond_constructed",
        changed_area_m2=1240.0
    )
    score1 = engine.compute_site_score("SITE-001", evidence=ev)
    score2 = engine.compute_site_score("SITE-001", evidence=ev)
    score3 = engine.compute_site_score("SITE-001", evidence=ev)

    assert score1["composite_index"] == score2["composite_index"] == score3["composite_index"]
    assert score1["ml_change_score"] == score2["ml_change_score"]
    assert score1["water_retention_score"] == score2["water_retention_score"]
    assert score1["vegetation_score"] == score2["vegetation_score"]
    assert score1["data_quality_score"] == score2["data_quality_score"]
    assert score1["verdict"] == score2["verdict"]

def test_different_water_area_different_scores(engine):
    """Verifies that varying water extent delta yields distinct scores."""
    ev_large = SiteEvidence(water_area_change_m2=1800.0, ndwi_change=0.50, change_class="farm_pond_constructed")
    ev_small = SiteEvidence(water_area_change_m2=150.0, ndwi_change=0.10, change_class="farm_pond_constructed")

    score_large = engine.compute_site_score("SITE-LARGE", evidence=ev_large)
    score_small = engine.compute_site_score("SITE-SMALL", evidence=ev_small)

    assert score_large["water_retention_score"] > score_small["water_retention_score"]
    assert score_large["composite_index"] > score_small["composite_index"]

def test_different_ndvi_different_scores(engine):
    """Verifies that varying NDVI change alters the vegetation score accordingly."""
    ev_high_veg = SiteEvidence(ndvi_change=0.22, change_class="farm_pond_constructed")
    ev_low_veg = SiteEvidence(ndvi_change=0.02, change_class="farm_pond_constructed")

    score_high = engine.compute_site_score("SITE-HIGH-VEG", evidence=ev_high_veg)
    score_low = engine.compute_site_score("SITE-LOW-VEG", evidence=ev_low_veg)

    assert score_high["vegetation_score"] > score_low["vegetation_score"]
    assert score_high["composite_index"] > score_low["composite_index"]

def test_negative_change_lower_score(engine):
    """Verifies that desiccation and negative deltas reduce scores and trigger degradation verdict."""
    ev_deg = SiteEvidence(
        water_area_change_m2=-1500.0,
        ndwi_change=-0.45,
        ndvi_change=-0.12,
        change_class="farm_pond_dried",
        ml_confidence=0.85
    )
    score = engine.compute_site_score("SITE-DEG", evidence=ev_deg)

    assert score["water_retention_score"] < 40.0
    assert score["vegetation_score"] < 40.0
    assert score["composite_index"] < 50.0
    assert score["verdict"] == "OBSERVED DEGRADATION"

def test_missing_evidence_insufficient_verdict(engine):
    """Verifies that missing critical images/GPS triggers INSUFFICIENT EVIDENCE verdict."""
    ev_missing = SiteEvidence(
        has_before_image=False,
        has_after_image=True,
        has_gps=False,
        missing_fields=["before_image", "gps_coordinates"],
        ml_confidence=0.30
    )
    score = engine.compute_site_score("SITE-MISSING", evidence=ev_missing)

    assert score["data_quality_score"] < 50.0
    assert score["verdict"] == "INSUFFICIENT EVIDENCE"

def test_boundedness_and_no_nan(engine):
    """Verifies that all scores are strictly clamped between 0 and 100 with no NaN or Inf."""
    extreme_cases = [
        SiteEvidence(water_area_change_m2=1e8, ndvi_change=5.0, ndwi_change=5.0, ml_confidence=10.0),
        SiteEvidence(water_area_change_m2=-1e8, ndvi_change=-5.0, ndwi_change=-5.0, ml_confidence=-2.0),
        SiteEvidence(water_area_change_m2=0.0, before_water_area_m2=0.0)
    ]
    for ev in extreme_cases:
        score = engine.compute_site_score("SITE-EXTREME", evidence=ev)
        for key in ["composite_index", "ml_change_score", "water_retention_score", "vegetation_score", "data_quality_score"]:
            val = score[key]
            assert 0.0 <= val <= 100.0, f"{key} out of bounds: {val}"
            assert not math.isnan(val), f"{key} is NaN"
            assert not math.isinf(val), f"{key} is Inf"

def test_site_comparison_five_sites(engine):
    """
    Mandatory Section 19 Verification:
    SITE A: high water increase, high NDVI increase, high ML confidence, excellent data quality
    SITE B: small water increase, small NDVI increase, medium ML confidence
    SITE C: no water change, no vegetation change (baseline background)
    SITE D: negative vegetation change, water decrease (demolished/dried)
    SITE E: missing before image / poor data quality
    
    Verifies:
    A != B, B != C, C != D, D != E
    and Ranking: A > B > C > D
    """
    site_a = engine.compute_site_score(
        "SITE-A",
        evidence=SiteEvidence(
            water_area_change_m2=1500.0,
            ndwi_change=0.45,
            ndvi_change=0.18,
            ml_confidence=0.92,
            change_class="farm_pond_constructed",
            changed_area_m2=1500.0,
            quality_score=0.96
        )
    )

    site_b = engine.compute_site_score(
        "SITE-B",
        evidence=SiteEvidence(
            water_area_change_m2=350.0,
            ndwi_change=0.12,
            ndvi_change=0.04,
            ml_confidence=0.75,
            change_class="farm_pond_constructed",
            changed_area_m2=350.0,
            quality_score=0.85
        )
    )

    site_c = engine.compute_site_score(
        "SITE-C",
        evidence=SiteEvidence(
            water_area_change_m2=0.0,
            ndwi_change=0.0,
            ndvi_change=0.0,
            ml_confidence=0.85,
            change_class="background",
            changed_area_m2=0.0,
            quality_score=0.90
        )
    )

    site_d = engine.compute_site_score(
        "SITE-D",
        evidence=SiteEvidence(
            water_area_change_m2=-1200.0,
            ndwi_change=-0.40,
            ndvi_change=-0.10,
            ml_confidence=0.88,
            change_class="farm_pond_dried",
            changed_area_m2=1200.0,
            quality_score=0.85
        )
    )

    site_e = engine.compute_site_score(
        "SITE-E",
        evidence=SiteEvidence(
            has_before_image=False,
            has_gps=False,
            missing_fields=["before_image", "gps"],
            quality_score=0.30,
            ml_confidence=0.35
        )
    )

    # 1. Verification of strict differentiation
    assert site_a["composite_index"] != site_b["composite_index"]
    assert site_b["composite_index"] != site_c["composite_index"]
    assert site_c["composite_index"] != site_d["composite_index"]
    assert site_d["composite_index"] != site_e["composite_index"]

    # 2. Verification of rational ranking
    assert site_a["composite_index"] > site_b["composite_index"]
    assert site_b["composite_index"] > site_c["composite_index"]
    assert site_c["composite_index"] > site_d["composite_index"]

    # 3. Verdict verification
    assert site_a["verdict"] == "OBSERVED IMPROVEMENT"
    assert site_d["verdict"] == "OBSERVED DEGRADATION"
    assert site_e["verdict"] == "INSUFFICIENT EVIDENCE"
