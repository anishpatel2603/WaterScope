"""
WATERSCOPE ML Engine - Evaluation Metrics
Calculates IoU, mIoU, Dice/F1, Precision, Recall, Pixel Accuracy, Class-wise IoU,
Confusion Matrix, and Change Area Error for bi-temporal change detection.
"""

from typing import Dict, Any, List
import numpy as np
import torch

CLASS_NAMES = [
    "Background",
    "Farm Pond Constructed",
    "Farm Pond Demolished",
    "Farm Pond Dried",
    "Farm Pond Wetted"
]

class ChangeDetectionMetrics:
    """
    Tracks and accumulates confusion matrix and calculates all change detection metrics.
    """
    def __init__(self, num_classes: int = 5, resolution_m: float = 1.0):
        self.num_classes = num_classes
        self.resolution_m = resolution_m
        self.reset()

    def reset(self):
        self.confusion_matrix = np.zeros((self.num_classes, self.num_classes), dtype=np.int64)
        self.pred_areas = []
        self.target_areas = []

    def update(self, preds: torch.Tensor, targets: torch.Tensor):
        # preds: [B, H, W] or [B, C, H, W]
        # targets: [B, H, W]
        if preds.ndim == 4:
            preds = torch.argmax(preds, dim=1)
            
        preds_np = preds.detach().cpu().numpy().flatten()
        targets_np = targets.detach().cpu().numpy().flatten()
        
        # Valid mask indices
        mask = (targets_np >= 0) & (targets_np < self.num_classes) & (preds_np >= 0) & (preds_np < self.num_classes)
        t_valid = targets_np[mask]
        p_valid = preds_np[mask]
        
        # Accumulate confusion matrix (rows = true, cols = pred)
        indices = self.num_classes * t_valid + p_valid
        counts = np.bincount(indices, minlength=self.num_classes ** 2)
        self.confusion_matrix += counts.reshape(self.num_classes, self.num_classes)
        
        # Track area changes (non-background pixels * resolution^2)
        batch_size = preds.shape[0] if preds.ndim == 3 else 1
        for b in range(batch_size):
            p_batch = (preds[b] > 0).sum().item() * (self.resolution_m ** 2)
            t_batch = (targets[b] > 0).sum().item() * (self.resolution_m ** 2)
            self.pred_areas.append(p_batch)
            self.target_areas.append(t_batch)

    def compute(self) -> Dict[str, Any]:
        cm = self.confusion_matrix.astype(np.float64)
        total = np.sum(cm)
        if total == 0:
            return {}

        pixel_accuracy = float(np.trace(cm) / total)
        
        # Class-wise calculations
        class_iou = {}
        class_precision = {}
        class_recall = {}
        class_f1 = {}
        
        for c in range(self.num_classes):
            tp = cm[c, c]
            fp = np.sum(cm[:, c]) - tp
            fn = np.sum(cm[c, :]) - tp
            
            denom_iou = tp + fp + fn
            iou = float(tp / denom_iou) if denom_iou > 0 else 0.0
            
            denom_prec = tp + fp
            prec = float(tp / denom_prec) if denom_prec > 0 else 0.0
            
            denom_rec = tp + fn
            rec = float(tp / denom_rec) if denom_rec > 0 else 0.0
            
            denom_f1 = prec + rec
            f1 = float(2 * prec * rec / denom_f1) if denom_f1 > 0 else 0.0
            
            cname = CLASS_NAMES[c] if c < len(CLASS_NAMES) else f"Class_{c}"
            class_iou[cname] = round(iou, 4)
            class_precision[cname] = round(prec, 4)
            class_recall[cname] = round(rec, 4)
            class_f1[cname] = round(f1, 4)

        # Mean IoU (macro across all classes)
        miou = float(np.mean(list(class_iou.values())))
        # Change-class specific mIoU (excluding background class 0)
        change_miou = float(np.mean([v for k, v in class_iou.items() if k != "Background"]))
        
        # Change area error (MAE and RMSE in square meters)
        if self.pred_areas and self.target_areas:
            diffs = np.abs(np.array(self.pred_areas) - np.array(self.target_areas))
            area_mae_m2 = float(np.mean(diffs))
            area_rmse_m2 = float(np.sqrt(np.mean(diffs ** 2)))
        else:
            area_mae_m2 = 0.0
            area_rmse_m2 = 0.0

        return {
            "pixel_accuracy": round(pixel_accuracy, 4),
            "mIoU": round(miou, 4),
            "change_mIoU": round(change_miou, 4),
            "mean_f1": round(float(np.mean(list(class_f1.values()))), 4),
            "class_iou": class_iou,
            "class_f1_dice": class_f1,
            "class_precision": class_precision,
            "class_recall": class_recall,
            "confusion_matrix": self.confusion_matrix.tolist(),
            "change_area_error_mae_m2": round(area_mae_m2, 2),
            "change_area_error_rmse_m2": round(area_rmse_m2, 2)
        }
