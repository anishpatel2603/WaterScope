"""
WATERSCOPE ML Engine - Production Inference Pipeline
Executes end-to-end bi-temporal change detection on image pairs,
generating pixel change masks, area calculations, calibrated confidence,
colorized overlays, and structured JSON responses.
"""

import io
import os
import uuid
import base64
from pathlib import Path
from typing import Union, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

from src.models.siamese import SiameseChangeNet, AttentionSiameseChangeNet
from src.models.baseline import BaselineChangeNet
from src.inference.field_mode import FieldPhotoAnalyzer
from src.inference.satellite_mode import SatellitePairAnalyzer
from src.inference.hybrid_analysis import HybridAnalyzer

CLASS_NAMES = [
    "background",
    "farm_pond_constructed",
    "farm_pond_demolished",
    "farm_pond_dried",
    "farm_pond_wetted"
]

CLASS_DISPLAY = {
    0: "Background (No Change)",
    1: "Farm Pond Constructed",
    2: "Farm Pond Demolished",
    3: "Farm Pond Dried",
    4: "Farm Pond Wetted"
}

# Distinct hex and RGB colors for mask visualization
CLASS_COLORS = {
    0: (0, 0, 0, 0),         # Transparent background
    1: (34, 197, 94, 210),   # Green (Constructed)
    2: (239, 68, 68, 210),   # Red (Demolished)
    3: (249, 115, 22, 210),  # Orange (Dried)
    4: (6, 182, 212, 210)    # Cyan (Wetted)
}

class ChangeDetectionPipeline:
    def __init__(
        self,
        model_path: Optional[str] = None,
        model_type: str = "siamese",
        device: str = "cpu",
        resolution_m: float = 1.0,
        img_size: Tuple[int, int] = (256, 256)
    ):
        self.device = torch.device(device)
        self.resolution_m = resolution_m
        self.img_size = img_size
        self.model_type = model_type
        
        # Initialize architecture
        if model_type == "attention_siamese":
            self.model = AttentionSiameseChangeNet(num_classes=5, pretrained=False)
            self.model_name = "waterscope_change_model_v3"
        elif model_type == "siamese":
            self.model = SiameseChangeNet(num_classes=5, pretrained=False)
            self.model_name = "waterscope_change_model_v2"
        else:
            self.model = BaselineChangeNet(num_classes=5, pretrained=False)
            self.model_name = "waterscope_change_model_v1"
            
        self.model_version = "1.0.0"
        self.dataset_id = "FPCD (ctundia/FPCD)"
        self.training_date = "2026-09-06"
        
        # Load weights if available
        if model_path and os.path.exists(model_path):
            self.load_checkpoint(model_path)
            
        self.model.to(self.device)
        self.model.eval()
        
        # Helper analyzers
        self.field_analyzer = FieldPhotoAnalyzer()
        self.satellite_analyzer = SatellitePairAnalyzer()
        self.hybrid_analyzer = HybridAnalyzer()

    def load_checkpoint(self, path: str):
        print(f"[PIPELINE] Loading model checkpoint from {path}...")
        ckpt = torch.load(path, map_location=self.device)
        if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
            self.model.load_state_dict(ckpt["model_state_dict"])
            if "config" in ckpt and "model" in ckpt["config"]:
                self.model_name = ckpt["config"]["model"].get("name", self.model_name)
        else:
            self.model.load_state_dict(ckpt)
        print("[PIPELINE] Model weights successfully loaded.")

    def _load_image(self, img_input: Union[str, Path, Image.Image, np.ndarray, bytes]) -> Image.Image:
        """Converts diverse image inputs into a standard RGB PIL Image."""
        if isinstance(img_input, (str, Path)):
            return Image.open(str(img_input)).convert("RGB")
        elif isinstance(img_input, Image.Image):
            return img_input.convert("RGB")
        elif isinstance(img_input, np.ndarray):
            return Image.fromarray(img_input).convert("RGB")
        elif isinstance(img_input, bytes):
            return Image.open(io.BytesIO(img_input)).convert("RGB")
        else:
            raise ValueError(f"Unsupported image input type: {type(img_input)}")

    def _preprocess(self, img: Image.Image) -> Tuple[torch.Tensor, np.ndarray]:
        """Resizes, converts to numpy, and returns normalized PyTorch tensor."""
        resized = img.resize(self.img_size, Image.Resampling.BILINEAR)
        arr = np.array(resized, dtype=np.float32) / 255.0
        
        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm_arr = (arr - mean) / std
        
        tensor = torch.from_numpy(norm_arr.transpose(2, 0, 1)).unsqueeze(0).float()
        return tensor.to(self.device), np.array(resized)

    def _colorize_mask(self, mask_2d: np.ndarray) -> Image.Image:
        """Generates an RGBA image from integer mask labels."""
        h, w = mask_2d.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        for cls_id, color in CLASS_COLORS.items():
            rgba[mask_2d == cls_id] = color
        return Image.fromarray(rgba, mode="RGBA")

    def _create_overlay(self, base_img: Image.Image, color_mask: Image.Image) -> Image.Image:
        """Blends the colorized mask over the target image."""
        base_rgba = base_img.convert("RGBA")
        return Image.alpha_composite(base_rgba, color_mask)

    def _img_to_data_uri(self, img: Image.Image, fmt: str = "PNG") -> str:
        buffered = io.BytesIO()
        img.save(buffered, format=fmt)
        b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/{fmt.lower()};base64,{b64}"

    def predict(
        self,
        t0_input: Any,
        t1_input: Any,
        mode: str = "satellite",
        analysis_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs complete bi-temporal prediction pipeline.
        Modes: 'satellite' or 'field'
        """
        aid = analysis_id or f"waterscope-{uuid.uuid4().hex[:12]}"
        
        # 1. Load and validate
        t0_raw = self._load_image(t0_input)
        t1_raw = self._load_image(t1_input)
        
        # Ensure dimensions match
        if t0_raw.size != t1_raw.size:
            t1_raw = t1_raw.resize(t0_raw.size, Image.Resampling.BILINEAR)

        # 2. Preprocess
        t0_tensor, t0_np_resized = self._preprocess(t0_raw)
        t1_tensor, t1_np_resized = self._preprocess(t1_raw)
        
        # 3. Model Forward Pass
        with torch.no_grad():
            outputs = self.model(t0_tensor, t1_tensor)
            seg_logits = outputs["seg_logits"] # [1, 5, H, W]
            cls_logits = outputs.get("cls_logits") # [1, 5]
            
            probs = F.softmax(seg_logits, dim=1).squeeze(0).cpu().numpy() # [5, H, W]
            mask_pred = np.argmax(probs, axis=0) # [H, W]
            
        # 4. Quantitative Change & Area Calculations
        total_pixels = mask_pred.size
        non_bg_mask = mask_pred > 0
        changed_pixels = int(np.sum(non_bg_mask))
        pixel_change_pct = round(float(changed_pixels / total_pixels * 100), 2)
        
        # Scale to real-world dimensions
        # Real resolution for 1 px at zoom 18 in Maharashtra is approx 1.0 meter
        scale_x = t0_raw.width / self.img_size[0]
        scale_y = t0_raw.height / self.img_size[1]
        area_m2_per_pixel = (self.resolution_m * scale_x) * (self.resolution_m * scale_y)
        changed_area_m2 = round(float(changed_pixels * area_m2_per_pixel), 1)

        # Determine dominant change class
        class_pixel_counts = {}
        for c in range(5):
            class_pixel_counts[c] = int(np.sum(mask_pred == c))
            
        # Class probabilities map (macro mean over image)
        class_probs = {
            CLASS_NAMES[c]: round(float(np.mean(probs[c])), 4)
            for c in range(5)
        }
        
        if changed_pixels > 0:
            change_counts = {c: class_pixel_counts[c] for c in range(1, 5)}
            dominant_id = max(change_counts, key=change_counts.get)
            change_class_str = CLASS_NAMES[dominant_id]
            # Calibrated Confidence: Mean softmax probability over the detected change region
            dominant_prob_map = probs[dominant_id]
            change_region_probs = dominant_prob_map[mask_pred == dominant_id]
            calibrated_confidence = float(np.mean(change_region_probs)) if len(change_region_probs) > 0 else 0.5
            confidence_method = "mean_probability_over_detected_change_region"
        else:
            dominant_id = 0
            change_class_str = "background"
            bg_probs = probs[0]
            calibrated_confidence = float(np.mean(bg_probs))
            confidence_method = "mean_probability_over_background"

        calibrated_confidence = round(calibrated_confidence, 4)

        # 5. Visualizations
        color_mask = self._colorize_mask(mask_pred)
        # Resize mask to match original input size
        color_mask_full = color_mask.resize(t0_raw.size, Image.Resampling.NEAREST)
        overlay_img = self._create_overlay(t1_raw, color_mask_full)
        
        mask_data_uri = self._img_to_data_uri(color_mask_full)
        overlay_data_uri = self._img_to_data_uri(overlay_img)
        t0_data_uri = self._img_to_data_uri(t0_raw, fmt="JPEG")
        t1_data_uri = self._img_to_data_uri(t1_raw, fmt="JPEG")

        # 6. Mode specific evaluations
        field_eval = None
        if mode == "field":
            field_eval = self.field_analyzer.evaluate_field_pair(
                np.array(t0_raw), np.array(t1_raw), calibrated_confidence
            )
            if not field_eval["can_classify"]:
                change_class_str = "insufficient_model_confidence"

        # 7. Satellite & Hybrid Analysis
        spectral_metrics = self.satellite_analyzer.process_pair(
            np.array(t0_raw), np.array(t1_raw)
        )
        
        prediction_stub = {
            "change_class": CLASS_DISPLAY.get(dominant_id, change_class_str),
            "confidence": calibrated_confidence,
            "pixel_change_percentage": pixel_change_pct
        }
        hybrid_results = self.hybrid_analyzer.evaluate(prediction_stub, spectral_metrics)

        # 8. Standardized JSON Output
        response = {
            "analysis_id": aid,
            "change_class": change_class_str,
            "change_class_display": CLASS_DISPLAY.get(dominant_id, change_class_str),
            "confidence": calibrated_confidence,
            "confidence_derivation_method": confidence_method,
            "pixel_change_percentage": pixel_change_pct,
            "changed_area_m2": changed_area_m2,
            "class_probabilities": class_probs,
            "class_pixel_counts": class_pixel_counts,
            "change_mask_url": mask_data_uri,
            "overlay_url": overlay_data_uri,
            "t0_url": t0_data_uri,
            "t1_url": t1_data_uri,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "dataset": self.dataset_id,
            "status": "completed",
            "mode": mode,
            "field_mode_diagnostics": field_eval,
            "spectral_indices": spectral_metrics,
            "hybrid_analysis": hybrid_results,
            "inference_timestamp": datetime.now().isoformat(),
            "scientific_disclaimer": (
                "Observed change detected from bi-temporal imagery. "
                "Demonstrates physical surface alteration; requires field validation."
            )
        }
        
        return response
