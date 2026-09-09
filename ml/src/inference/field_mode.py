"""
WATERSCOPE ML Engine - Real Field Photo Mode (FIELD_IMAGE_MODE)
Evaluates ground-level smartphone photos, perspective distortion, blur, exposure anomalies,
and domain shift, enforcing strict confidence thresholds and OOD flags.
"""

from typing import Dict, Any, Tuple
import cv2
import numpy as np

class FieldPhotoAnalyzer:
    """
    Validates field-captured photographs against aerial/satellite training distribution.
    Prevents false classifications on uncalibrated handheld smartphone photos.
    """
    def __init__(self, blur_threshold: float = 80.0, min_confidence: float = 0.65):
        self.blur_threshold = blur_threshold
        self.min_confidence = min_confidence

    def check_quality(self, img_rgb: np.ndarray) -> Dict[str, Any]:
        """Examines sharpness, dynamic range, and exposure of photo."""
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        
        # Laplacian variance for blur
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = lap_var < self.blur_threshold
        
        # Exposure check
        mean_lum = float(np.mean(gray))
        overexposed = mean_lum > 220.0
        underexposed = mean_lum < 35.0
        
        # Color distribution (standard deviation across channels)
        std_rgb = [float(np.std(img_rgb[:, :, c])) for c in range(3)]
        low_contrast = any(s < 20.0 for s in std_rgb)
        
        issues = []
        if is_blurry: issues.append(f"Image blur detected (sharpness: {lap_var:.1f})")
        if overexposed: issues.append(f"Severe overexposure (mean luminance: {mean_lum:.1f})")
        if underexposed: issues.append(f"Severe underexposure (mean luminance: {mean_lum:.1f})")
        if low_contrast: issues.append("Low dynamic contrast across color bands")
        
        return {
            "passed": len(issues) == 0,
            "sharpness_score": round(lap_var, 2),
            "mean_luminance": round(mean_lum, 2),
            "issues": issues
        }

    def assess_distribution_shift(self, t0: np.ndarray, t1: np.ndarray) -> Dict[str, Any]:
        """
        Detects if imagery deviates substantially from top-down nadir orthophotos
        (e.g., ground angle, horizon present, extreme camera tilt).
        """
        # Top-down nadir aerial images typically have relatively uniform spatial gradient distribution
        # Ground photos often feature large perspective gradients (sky/horizon at top, ground at bottom)
        gray0 = cv2.cvtColor(t0, cv2.COLOR_RGB2GRAY)
        gray1 = cv2.cvtColor(t1, cv2.COLOR_RGB2GRAY)
        
        top_half0 = np.mean(gray0[:gray0.shape[0]//3, :])
        bot_half0 = np.mean(gray0[2*gray0.shape[0]//3:, :])
        vert_grad0 = abs(top_half0 - bot_half0)
        
        top_half1 = np.mean(gray1[:gray1.shape[0]//3, :])
        bot_half1 = np.mean(gray1[2*gray1.shape[0]//3:, :])
        vert_grad1 = abs(top_half1 - bot_half1)
        
        is_perspective_tilted = (vert_grad0 > 75.0) or (vert_grad1 > 75.0)
        
        return {
            "out_of_distribution": is_perspective_tilted,
            "vertical_gradient_t0": round(float(vert_grad0), 2),
            "vertical_gradient_t1": round(float(vert_grad1), 2),
            "perspective_warning": "Probable ground-angle photo with horizon rather than nadir orthophoto." if is_perspective_tilted else None
        }

    def evaluate_field_pair(
        self,
        t0_rgb: np.ndarray,
        t1_rgb: np.ndarray,
        raw_confidence: float
    ) -> Dict[str, Any]:
        """Full evaluation pipeline for field photo mode."""
        q0 = self.check_quality(t0_rgb)
        q1 = self.check_quality(t1_rgb)
        ood = self.assess_distribution_shift(t0_rgb, t1_rgb)
        
        all_issues = q0["issues"] + q1["issues"]
        if ood["perspective_warning"]:
            all_issues.append(ood["perspective_warning"])
            
        is_ood = ood["out_of_distribution"] or len(all_issues) > 0
        insufficient_confidence = (raw_confidence < self.min_confidence) or is_ood
        
        status = "INSUFFICIENT_MODEL_CONFIDENCE" if insufficient_confidence else "CONFIDENT"
        
        return {
            "mode": "FIELD_IMAGE_MODE",
            "field_photo_status": status,
            "can_classify": not insufficient_confidence,
            "confidence": round(raw_confidence if not is_ood else raw_confidence * 0.65, 3),
            "quality_check_t0": q0,
            "quality_check_t1": q1,
            "out_of_distribution": is_ood,
            "warnings": all_issues,
            "recommendation": (
                "Capture high-angle or drone nadir photograph under daylight conditions, "
                "or request manual field personnel ground inspection." if insufficient_confidence else "Accept model prediction with routine field verification."
            )
        }
