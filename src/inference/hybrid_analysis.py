"""
WATERSCOPE ML Engine - Hybrid Analysis & Interpretable Scoring
Synthesizes ML bi-temporal change predictions with remote sensing indices (NDVI, NDWI,
water extent, vegetation extent) to produce an evidence-backed environmental verdict
without making unsupported causal claims.
"""

from typing import Dict, Any

class HybridAnalyzer:
    """
    Combines computer vision change detection with multispectral remote sensing indicators.
    Computes a transparent, weighted composite score and determines observed environmental trends.
    """
    VERSION = "2.1.0"
    
    # Transparent score component weights (Sum = 1.0)
    WEIGHTS = {
        "ml_change_evidence": 0.35,
        "water_extent_evidence": 0.30,
        "vegetation_evidence": 0.20,
        "model_confidence": 0.15
    }

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.WEIGHTS

    def evaluate(
        self,
        ml_prediction: Dict[str, Any],
        spectral_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes ML output and spectral changes into an interpretable score and classification.
        """
        change_class = ml_prediction.get("change_class", "Background")
        confidence = float(ml_prediction.get("confidence", 0.0))
        pixel_change_pct = float(ml_prediction.get("pixel_change_percentage", 0.0))
        
        delta_ndwi = float(spectral_metrics.get("delta_mean_ndwi", 0.0))
        delta_ndvi = float(spectral_metrics.get("delta_mean_ndvi", 0.0))
        water_pct_delta = float(spectral_metrics.get("water_extent_change_pct", 0.0))
        veg_pct_delta = float(spectral_metrics.get("veg_extent_change_pct", 0.0))
        
        # 1. Component Scoring (Normalized 0.0 to 100.0)
        # ML Evidence: Positive for constructed / wetted, negative for demolished / dried
        if change_class in ["Farm Pond Constructed", "Farm Pond Wetted", 1, 4]:
            ml_score = min(100.0, 50.0 + (pixel_change_pct * 3.5))
        elif change_class in ["Farm Pond Demolished", "Farm Pond Dried", 2, 3]:
            ml_score = max(0.0, 40.0 - (pixel_change_pct * 2.0))
        else: # Background / no change
            ml_score = 50.0

        # Water Extent Evidence (0 to 100)
        # Positive water growth indicates increased surface retention
        water_score = max(0.0, min(100.0, 50.0 + (water_pct_delta * 0.5) + (delta_ndwi * 100.0)))
        
        # Vegetation Evidence (0 to 100)
        # Positive vegetation growth around intervention
        veg_score = max(0.0, min(100.0, 50.0 + (veg_pct_delta * 0.4) + (delta_ndvi * 100.0)))
        
        # Confidence Score (0 to 100)
        conf_score = confidence * 100.0

        # 2. Transparent Weighted Composite Score
        composite_score = (
            self.weights["ml_change_evidence"] * ml_score +
            self.weights["water_extent_evidence"] * water_score +
            self.weights["vegetation_evidence"] * veg_score +
            self.weights["model_confidence"] * conf_score
        )
        composite_score = round(composite_score, 2)

        # 3. High-level Environmental Verdict
        # Criteria adheres to scientific limitation: observed state, NOT causal proof.
        if confidence < 0.40:
            verdict = "INSUFFICIENT EVIDENCE"
            rationale = "Model confidence or data quality is insufficient to draw a definitive observation."
        elif change_class in ["Farm Pond Constructed", "Farm Pond Wetted", 1, 4] and composite_score >= 60.0:
            verdict = "OBSERVED IMPROVEMENT"
            rationale = "Satellite and model evidence indicates newly established or replenished water storage structure."
        elif change_class in ["Farm Pond Demolished", "Farm Pond Dried", 2, 3] or composite_score < 40.0:
            verdict = "OBSERVED DEGRADATION"
            rationale = "Evidence indicates disappearance, demolition, or desiccation of water retention feature."
        elif abs(composite_score - 50.0) < 10.0 and pixel_change_pct < 2.0:
            verdict = "NO SIGNIFICANT OBSERVED CHANGE"
            rationale = "Spectral indices and imagery show stable baseline state with no substantial physical alterations."
        else:
            verdict = "NO SIGNIFICANT OBSERVED CHANGE"
            rationale = "Minor fluctuations within normal seasonal hydrological variability."

        components = {
            "ml_change_evidence": {
                "score": round(ml_score, 2),
                "weight": self.weights["ml_change_evidence"],
                "description": f"Detected change class '{change_class}' impacting {pixel_change_pct:.1f}% of target area"
            },
            "water_extent_evidence": {
                "score": round(water_score, 2),
                "weight": self.weights["water_extent_evidence"],
                "description": f"Water index delta (ΔNDWI: {delta_ndwi:+.3f}, Water extent: {water_pct_delta:+.1f}%)"
            },
            "vegetation_evidence": {
                "score": round(veg_score, 2),
                "weight": self.weights["vegetation_evidence"],
                "description": f"Vegetation index delta (ΔNDVI: {delta_ndvi:+.3f}, Veg extent: {veg_pct_delta:+.1f}%)"
            },
            "model_confidence": {
                "score": round(conf_score, 2),
                "weight": self.weights["model_confidence"],
                "description": f"Calibrated neural network certainty: {confidence * 100:.1f}%"
            }
        }

        return {
            "verdict": verdict,
            "rationale": rationale,
            "composite_score": composite_score,
            "components": components,
            "weights": self.weights,
            "scoring_version": self.VERSION,
            "scientific_limitation_notice": (
                "SCIENTIFIC NOTICE: This analysis reports observed bi-temporal optical and spectral changes. "
                "It demonstrates geospatial evidence of structural presence and moisture variations, "
                "but does not establish direct ecological causality without ground-truth hydrological validation."
            )
        }
