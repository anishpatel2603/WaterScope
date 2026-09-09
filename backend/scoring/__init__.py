"""
WATERSCOPE Scoring Engine Package
"""

from backend.scoring.scoring_engine import SiteSpecificScoringEngine, default_scoring_engine
from backend.scoring.evidence import SiteEvidence, extract_site_evidence
from backend.scoring.normalization import (
    clamp,
    normalize_ml_change,
    normalize_water_retention,
    normalize_vegetation,
    normalize_data_quality
)
from backend.scoring.verdict import evaluate_verdict

__all__ = [
    "SiteSpecificScoringEngine",
    "default_scoring_engine",
    "SiteEvidence",
    "extract_site_evidence",
    "clamp",
    "normalize_ml_change",
    "normalize_water_retention",
    "normalize_vegetation",
    "normalize_data_quality",
    "evaluate_verdict"
]
