"""
WATERSCOPE ML Engine - Satellite Pair Mode (SATELLITE_PAIR_MODE)
Processes multispectral satellite pairs (Sentinel-2 bands: RGB, NIR, Red, Green, SWIR),
computes normalized vegetation, water, and built-up indices, and quantifies surface hydrology.
"""

from typing import Dict, Any, Optional
import numpy as np
from src.dataset.satellite import (
    compute_ndvi,
    compute_ndwi,
    compute_ndbi,
    estimate_spectral_indices_from_rgb,
    analyze_bitemporal_spectral_change
)

class SatellitePairAnalyzer:
    """
    Analyzes bi-temporal satellite image pairs with multi-spectral band support.
    """
    def __init__(self, water_threshold: float = 0.05, veg_threshold: float = 0.20):
        self.water_threshold = water_threshold
        self.veg_threshold = veg_threshold

    def process_pair(
        self,
        t0_rgb: np.ndarray,
        t1_rgb: np.ndarray,
        t0_nir: Optional[np.ndarray] = None,
        t1_nir: Optional[np.ndarray] = None,
        t0_swir: Optional[np.ndarray] = None,
        t1_swir: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Calculates spectral indices across T0 and T1.
        """
        has_nir = (t0_nir is not None) and (t1_nir is not None)
        
        t0_bands = {"rgb": t0_rgb}
        t1_bands = {"rgb": t1_rgb}
        
        if has_nir:
            t0_bands["nir"] = t0_nir
            t0_bands["red"] = t0_rgb[:, :, 0]
            t0_bands["green"] = t0_rgb[:, :, 1]
            t1_bands["nir"] = t1_nir
            t1_bands["red"] = t1_rgb[:, :, 0]
            t1_bands["green"] = t1_rgb[:, :, 1]
            
        spectral_metrics = analyze_bitemporal_spectral_change(
            t0_bands,
            t1_bands,
            water_threshold=self.water_threshold,
            veg_threshold=self.veg_threshold
        )
        
        # Classify spectral tendency
        delta_water = spectral_metrics["water_extent_change_pct"]
        delta_veg = spectral_metrics["veg_extent_change_pct"]
        
        if delta_water > 15.0 or delta_veg > 15.0:
            spectral_verdict = "POSITIVE_HYDROLOGICAL_RESPONSE"
        elif delta_water < -15.0:
            spectral_verdict = "DECREASED_WATER_RETENTION"
        else:
            spectral_verdict = "STABLE_SPECTRAL_STATE"
            
        spectral_metrics["spectral_verdict"] = spectral_verdict
        return spectral_metrics
