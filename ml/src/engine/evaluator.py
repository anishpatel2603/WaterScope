"""
WATERSCOPE ML Engine - Model Evaluator
Computes test metrics, class-wise performance, confusion matrices, and model comparison.
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.models.metrics import ChangeDetectionMetrics, CLASS_NAMES

def evaluate_model_on_test(
    model: torch.nn.Module,
    test_loader: DataLoader,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Evaluates a model over the test DataLoader and computes all change metrics.
    """
    model.eval()
    dev = torch.device(device)
    model.to(dev)
    
    metrics = ChangeDetectionMetrics(num_classes=5)
    
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluating on Test Set"):
            img0 = batch["image0"].to(dev)
            img1 = batch["image1"].to(dev)
            masks = batch["mask"].to(dev)
            
            outputs = model(img0, img1)
            metrics.update(outputs["seg_logits"], masks)
            
    results = metrics.compute()
    return results

def format_confusion_matrix_ascii(cm: List[List[int]]) -> str:
    """Format confusion matrix as readable ASCII table."""
    lines = []
    header = f"{'Class (True \\ Pred)':<26} | " + " | ".join([f"{c[:10]:>10}" for c in CLASS_NAMES])
    lines.append(header)
    lines.append("-" * len(header))
    for i, row in enumerate(cm):
        row_str = " | ".join([f"{val:>10d}" for val in row])
        lines.append(f"{CLASS_NAMES[i]:<26} | {row_str}")
    return "\n".join(lines)
