"""
WATERSCOPE ML Engine - Remote Sensing & Spectral Index Processing
Calculates Normalized Difference Vegetation Index (NDVI), Normalized Difference
Water Index (NDWI), and Normalized Difference Built-Up Index (NDBI) for Sentinel-2
and simulated/optical multispectral pairs.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np

def compute_ndvi(nir: np.ndarray, red: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """
    NDVI = (NIR - Red) / (NIR + Red)
    Values range from -1.0 to 1.0 (Higher values indicate denser green vegetation).
    """
    denominator = nir.astype(np.float32) + red.astype(np.float32) + eps
    numerator = nir.astype(np.float32) - red.astype(np.float32)
    ndvi = numerator / denominator
    return np.clip(ndvi, -1.0, 1.0)

def compute_ndwi(green: np.ndarray, nir: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """
    McFeeters NDWI = (Green - NIR) / (Green + NIR)
    Values > 0 typically correspond to open water bodies.
    """
    denominator = green.astype(np.float32) + nir.astype(np.float32) + eps
    numerator = green.astype(np.float32) - nir.astype(np.float32)
    ndwi = numerator / denominator
    return np.clip(ndwi, -1.0, 1.0)

def compute_ndbi(swir: np.ndarray, nir: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """
    NDBI = (SWIR - NIR) / (SWIR + NIR)
    Useful for bare soil, rock, or built-up embankments.
    """
    denominator = swir.astype(np.float32) + nir.astype(np.float32) + eps
    numerator = swir.astype(np.float32) - nir.astype(np.float32)
    ndbi = numerator / denominator
    return np.clip(ndbi, -1.0, 1.0)

def estimate_spectral_indices_from_rgb(rgb_img: np.ndarray) -> Dict[str, np.ndarray]:
    """
    When only standard 3-channel optical aerial/field images are available (FPCD dataset / standard camera),
    estimate pseudo-indices using Visible Atmospherically Resistant Index (VARI) and Green-Red Normalized
    Difference (GLI / NDWI-pseudo) for bi-temporal vegetation & water proxy tracking.
    
    VARI = (Green - Red) / (Green + Red - Blue + eps)
    NDWI_optical_proxy = (Green - Red) / (Green + Red + eps)
    """
    r = rgb_img[:, :, 0].astype(np.float32) / 255.0
    g = rgb_img[:, :, 1].astype(np.float32) / 255.0
    b = rgb_img[:, :, 2].astype(np.float32) / 255.0
    eps = 1e-6
    
    # VARI proxy for NDVI
    denom_vari = g + r - b + eps
    denom_vari[denom_vari == 0] = eps
    vari = np.clip((g - r) / denom_vari, -1.0, 1.0)
    
    # Visible Green-Red Water proxy
    denom_water = g + r + eps
    water_proxy = np.clip((g - r) / denom_water, -1.0, 1.0)
    
    # Excessive green index (2G - R - B)
    exg = np.clip(2 * g - r - b, -1.0, 1.0)
    
    return {
        "ndvi_proxy": vari,
        "ndwi_proxy": water_proxy,
        "exg": exg
    }

def analyze_bitemporal_spectral_change(
    t0_bands: Dict[str, np.ndarray],
    t1_bands: Dict[str, np.ndarray],
    water_threshold: float = 0.05,
    veg_threshold: float = 0.15
) -> Dict[str, Any]:
    """
    Compares before/after spectral representations to extract water and vegetation metrics.
    Supports either full Sentinel-2 bands (NIR, Red, Green, SWIR) or optical RGB proxies.
    """
    is_multispectral = "nir" in t0_bands and "nir" in t1_bands
    
    if is_multispectral:
        t0_ndvi = compute_ndvi(t0_bands["nir"], t0_bands["red"])
        t1_ndvi = compute_ndvi(t1_bands["nir"], t1_bands["red"])
        
        t0_ndwi = compute_ndwi(t0_bands["green"], t0_bands["nir"])
        t1_ndwi = compute_ndwi(t1_bands["green"], t1_bands["nir"])
    else:
        t0_idx = estimate_spectral_indices_from_rgb(t0_bands["rgb"])
        t1_idx = estimate_spectral_indices_from_rgb(t1_bands["rgb"])
        t0_ndvi = t0_idx["ndvi_proxy"]
        t1_ndvi = t1_idx["ndvi_proxy"]
        t0_ndwi = t0_idx["ndwi_proxy"]
        t1_ndwi = t1_idx["ndwi_proxy"]
        
    delta_ndvi = t1_ndvi - t0_ndvi
    delta_ndwi = t1_ndwi - t0_ndwi
    
    # Water extent binary thresholding
    t0_water_mask = t0_ndwi > water_threshold
    t1_water_mask = t1_ndwi > water_threshold
    
    t0_water_pixels = int(np.sum(t0_water_mask))
    t1_water_pixels = int(np.sum(t1_water_mask))
    water_pixel_delta = t1_water_pixels - t0_water_pixels
    
    # Vegetation binary thresholding
    t0_veg_mask = t0_ndvi > veg_threshold
    t1_veg_mask = t1_ndvi > veg_threshold
    
    t0_veg_pixels = int(np.sum(t0_veg_mask))
    t1_veg_pixels = int(np.sum(t1_veg_mask))
    veg_pixel_delta = t1_veg_pixels - t0_veg_pixels
    
    return {
        "mode": "Sentinel-2 MultiSpectral" if is_multispectral else "Optical RGB Proxy",
        "mean_t0_ndvi": float(np.mean(t0_ndvi)),
        "mean_t1_ndvi": float(np.mean(t1_ndvi)),
        "delta_mean_ndvi": float(np.mean(delta_ndvi)),
        "mean_t0_ndwi": float(np.mean(t0_ndwi)),
        "mean_t1_ndwi": float(np.mean(t1_ndwi)),
        "delta_mean_ndwi": float(np.mean(delta_ndwi)),
        "t0_water_pixels": t0_water_pixels,
        "t1_water_pixels": t1_water_pixels,
        "water_pixel_delta": water_pixel_delta,
        "water_extent_change_pct": round(float(water_pixel_delta / (t0_water_pixels + 1e-4) * 100), 2) if t0_water_pixels > 0 else 100.0 if t1_water_pixels > 0 else 0.0,
        "t0_veg_pixels": t0_veg_pixels,
        "t1_veg_pixels": t1_veg_pixels,
        "veg_pixel_delta": veg_pixel_delta,
        "veg_extent_change_pct": round(float(veg_pixel_delta / (t0_veg_pixels + 1e-4) * 100), 2) if t0_veg_pixels > 0 else 100.0 if t1_veg_pixels > 0 else 0.0
    }
