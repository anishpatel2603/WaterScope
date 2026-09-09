"""
WATERSCOPE Backend - Observed Impact Scoring Engine Service
Exposes transparent composite impact scores and provenance for watershed interventions
without making unsupported causal assertions.
Powered by SiteSpecificScoringEngine (v2.0).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.scoring.scoring_engine import default_scoring_engine

class ObservedImpactScoringEngine:
    """
    Transparent scoring engine for watershed interventions.
    Wraps SiteSpecificScoringEngine (v2.0) for unified site scoring and analysis job integration.
    """
    WEIGHTS = default_scoring_engine.WEIGHTS

    def compute_observed_impact(
        self,
        ml_result: Dict[str, Any],
        spatial_metrics: List[Dict[str, Any]],
        acquisition_date: str = None,
        site_id: str = "site-analysis"
    ) -> Dict[str, Any]:
        return default_scoring_engine.compute_site_score(
            site_id=site_id,
            ml_result=ml_result,
            spatial_metrics=spatial_metrics,
            site_metadata={"has_dates": bool(acquisition_date)}
        )
