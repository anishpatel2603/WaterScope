"""
WATERSCOPE ML Engine - Post-Hoc Confidence Calibration
Implements:
- Temperature Scaling for multi-class probability calibration
- Expected Calibration Error (ECE) metric calculation
- Reliability diagram data generation
Evaluated strictly on validation set to prevent test data leakage.
"""

from typing import Dict, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

class TemperatureScaler(nn.Module):
    """
    Learns a scalar temperature T to soften or sharpen logits:
    p_calibrated = softmax(logits / T)
    T is optimized strictly on the validation set via cross-entropy loss.
    """
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        # logits: [B, C, H, W] or [B, C]
        temp = self.temperature.clamp(min=0.01)
        if logits.ndim == 4:
            return logits / temp.view(1, 1, 1, 1)
        return logits / temp

    def calibrate(self, val_logits: torch.Tensor, val_targets: torch.Tensor, max_iters: int = 50, lr: float = 0.01) -> float:
        """
        Optimizes temperature T using validation logits and targets.
        """
        self.train()
        nll_criterion = nn.CrossEntropyLoss()
        optimizer = optim.LBFGS([self.temperature], lr=lr, max_iter=max_iters)

        def eval_step():
            optimizer.zero_grad()
            scaled = self.forward(val_logits)
            loss = nll_criterion(scaled, val_targets)
            loss.backward()
            return loss

        optimizer.step(eval_step)
        optimal_t = float(self.temperature.item())
        print(f"[CALIBRATION] Optimal Validation Temperature: {optimal_t:.4f}")
        self.eval()
        return optimal_t

def compute_ece(
    probs: np.ndarray,
    targets: np.ndarray,
    num_bins: int = 10
) -> Dict[str, Any]:
    """
    Calculates Expected Calibration Error (ECE) and reliability diagram bins.
    probs: [N, C] or [N] max confidence
    targets: [N] true integer class labels
    """
    if probs.ndim == 2:
        confidences = np.max(probs, axis=1)
        predictions = np.argmax(probs, axis=1)
    else:
        confidences = probs
        predictions = (confidences > 0.5).astype(int)

    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0
    bins_data = []

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = float(np.mean(in_bin))

        if prop_in_bin > 0:
            acc_in_bin = float(np.mean(predictions[in_bin] == targets[in_bin]))
            avg_conf_in_bin = float(np.mean(confidences[in_bin]))
            ece += np.abs(avg_conf_in_bin - acc_in_bin) * prop_in_bin

            bins_data.append({
                "bin_lower": round(bin_lower, 2),
                "bin_upper": round(bin_upper, 2),
                "confidence": round(avg_conf_in_bin, 4),
                "accuracy": round(acc_in_bin, 4),
                "sample_count": int(np.sum(in_bin))
            })

    return {
        "ece": round(float(ece), 4),
        "ece_percentage": round(float(ece) * 100.0, 2),
        "reliability_bins": bins_data
    }
