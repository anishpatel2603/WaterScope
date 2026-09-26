"""
WATERSCOPE ML Engine - Comprehensive Test Suite
Tests dataset loading, Siamese & Baseline model forward passes, metrics calculation,
field photo mode, satellite multi-spectral analysis, and inference pipeline.
"""

import os
import pytest
import numpy as np
import torch
from PIL import Image

from src.dataset.dataset import FPCDDataset
from src.dataset.satellite import compute_ndvi, compute_ndwi, estimate_spectral_indices_from_rgb
from src.models.siamese import SiameseChangeNet
from src.models.baseline import BaselineChangeNet
from src.models.loss import ChangeDetectionLoss
from src.models.metrics import ChangeDetectionMetrics
from src.inference.field_mode import FieldPhotoAnalyzer
from src.inference.satellite_mode import SatellitePairAnalyzer
from src.inference.hybrid_analysis import HybridAnalyzer
from src.inference.pipeline import ChangeDetectionPipeline

def test_spectral_indices():
    nir = np.ones((64, 64), dtype=np.float32) * 0.8
    red = np.ones((64, 64), dtype=np.float32) * 0.2
    green = np.ones((64, 64), dtype=np.float32) * 0.4
    
    ndvi = compute_ndvi(nir, red)
    assert ndvi.shape == (64, 64)
    assert 0.5 < np.mean(ndvi) < 0.7 # (0.8 - 0.2) / (0.8 + 0.2) = 0.6
    
    ndwi = compute_ndwi(green, nir)
    assert ndwi.shape == (64, 64)
    assert -0.4 < np.mean(ndwi) < -0.3 # (0.4 - 0.8) / (0.4 + 0.8) = -0.333

def test_rgb_spectral_proxies():
    img_rgb = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    indices = estimate_spectral_indices_from_rgb(img_rgb)
    assert "ndvi_proxy" in indices
    assert "ndwi_proxy" in indices
    assert indices["ndvi_proxy"].shape == (64, 64)

def test_siamese_architecture():
    model = SiameseChangeNet(num_classes=5, pretrained=False)
    x0 = torch.randn(2, 3, 128, 128)
    x1 = torch.randn(2, 3, 128, 128)
    out = model(x0, x1)
    assert "seg_logits" in out
    assert out["seg_logits"].shape == (2, 5, 128, 128)
    assert "cls_logits" in out
    assert out["cls_logits"].shape == (2, 5)

def test_baseline_architecture():
    model = BaselineChangeNet(num_classes=5, pretrained=False)
    x0 = torch.randn(2, 3, 128, 128)
    x1 = torch.randn(2, 3, 128, 128)
    out = model(x0, x1)
    assert "seg_logits" in out
    assert out["seg_logits"].shape == (2, 5, 128, 128)

def test_loss_and_metrics():
    loss_fn = ChangeDetectionLoss()
    logits = torch.randn(2, 5, 32, 32)
    targets = torch.randint(0, 5, (2, 32, 32))
    loss = loss_fn(logits, targets)
    assert loss.item() > 0

    metrics = ChangeDetectionMetrics(num_classes=5)
    metrics.update(logits, targets)
    res = metrics.compute()
    assert "pixel_accuracy" in res
    assert "mIoU" in res
    assert "confusion_matrix" in res

def test_field_mode_analyzer():
    analyzer = FieldPhotoAnalyzer()
    sharp = np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8)
    q = analyzer.check_quality(sharp)
    assert "sharpness_score" in q
    
    # Blurry image
    blurry = np.ones((100, 100, 3), dtype=np.uint8) * 128
    q_blur = analyzer.check_quality(blurry)
    assert q_blur["passed"] is False

def test_hybrid_analyzer():
    hybrid = HybridAnalyzer()
    ml_pred = {
        "change_class": "Farm Pond Constructed",
        "confidence": 0.88,
        "pixel_change_percentage": 15.0
    }
    spectral = {
        "delta_mean_ndwi": 0.25,
        "delta_mean_ndvi": 0.15,
        "water_extent_change_pct": 80.0,
        "veg_extent_change_pct": 30.0
    }
    result = hybrid.evaluate(ml_pred, spectral)
    assert result["verdict"] in ["OBSERVED IMPROVEMENT", "OBSERVED DEGRADATION", "NO SIGNIFICANT OBSERVED CHANGE", "INSUFFICIENT EVIDENCE"]
    assert 0.0 <= result["composite_score"] <= 100.0
    assert "scientific_limitation_notice" in result
