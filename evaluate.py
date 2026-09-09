"""
WATERSCOPE ML Engine - Comprehensive Test Evaluation & Model Comparison
Usage:
  python evaluate.py --siamese-ckpt models/fpcd_siamese_v1.pt --baseline-ckpt models/fpcd_baseline_cnn.pt
"""

import os
import json
import argparse
from pathlib import Path
import yaml
import torch
from torch.utils.data import DataLoader

from src.dataset.dataset import FPCDDataset
from src.dataset.transforms import get_validation_transforms
from src.models.siamese import SiameseChangeNet, AttentionSiameseChangeNet
from src.models.baseline import BaselineChangeNet
from src.engine.evaluator import evaluate_model_on_test, format_confusion_matrix_ascii

def evaluate_single_model(model_cls, ckpt_path: str, test_loader: DataLoader, device: str = "cpu"):
    model = model_cls(num_classes=5, pretrained=False)
    if os.path.exists(ckpt_path):
        ckpt = torch.load(ckpt_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt)
        print(f"[EVAL] Loaded weights from {ckpt_path}")
    else:
        print(f"[EVAL WARNING] {ckpt_path} not found. Running with baseline initial weights.")
    return evaluate_model_on_test(model, test_loader, device=device)

def main():
    parser = argparse.ArgumentParser(description="Evaluate WATERSCOPE models on test set")
    parser.add_argument("--siamese-ckpt", default="models/fpcd_siamese_v1.pt", help="Path to Siamese checkpoint")
    parser.add_argument("--baseline-ckpt", default="models/fpcd_baseline_cnn.pt", help="Path to Baseline checkpoint")
    parser.add_argument("--attention-ckpt", default="checkpoints/best_model.pt", help="Path to Attention Siamese checkpoint")
    parser.add_argument("--data-dir", default="./data/fpcd", help="Dataset directory")
    parser.add_argument("--device", default="cpu", help="Compute device")
    parser.add_argument("--save-dir", default="./experiments", help="Output directory for reports")
    args = parser.parse_args()

    save_path = Path(args.save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    val_transform = get_validation_transforms((256, 256))
    test_ds = FPCDDataset(data_dir=args.data_dir, split="test", transform=val_transform)
    test_loader = DataLoader(test_ds, batch_size=8, shuffle=False)

    print("==================================================")
    print("RUNNING COMPREHENSIVE TEST SET EVALUATION")
    print(f"Test samples: {len(test_ds)}")
    print("==================================================")

    # 1. Evaluate Attention Siamese (Best Model)
    print("\n--- Evaluating Attention Siamese Model (v3) ---")
    attn_metrics = evaluate_single_model(AttentionSiameseChangeNet, args.attention_ckpt, test_loader, args.device)
    print(f"Attention Siamese Pixel Accuracy: {attn_metrics['pixel_accuracy']*100:.2f}%")
    print(f"Attention Siamese Mean IoU:       {attn_metrics['mIoU']*100:.2f}%")
    print(f"Attention Siamese Change mIoU:    {attn_metrics['change_mIoU']*100:.2f}%")
    print(f"Attention Siamese Mean F1:        {attn_metrics['mean_f1']*100:.2f}%")
    print(f"Attention Siamese Change Area MAE:{attn_metrics['change_area_error_mae_m2']} m²")

    # 2. Evaluate Siamese (v2)
    print("\n--- Evaluating Siamese Model (v2) ---")
    siamese_metrics = evaluate_single_model(SiameseChangeNet, args.siamese_ckpt, test_loader, args.device)
    print(f"Siamese Pixel Accuracy: {siamese_metrics['pixel_accuracy']*100:.2f}%")
    print(f"Siamese Mean IoU:       {siamese_metrics['mIoU']*100:.2f}%")
    print(f"Siamese Change mIoU:    {siamese_metrics['change_mIoU']*100:.2f}%")
    print(f"Siamese Mean F1:        {siamese_metrics['mean_f1']*100:.2f}%")
    print(f"Siamese Change Area MAE:{siamese_metrics['change_area_error_mae_m2']} m²")

    # 3. Evaluate Baseline (v1)
    print("\n--- Evaluating Baseline Model (v1) ---")
    baseline_metrics = evaluate_single_model(BaselineChangeNet, args.baseline_ckpt, test_loader, args.device)
    print(f"Baseline Pixel Accuracy: {baseline_metrics['pixel_accuracy']*100:.2f}%")
    print(f"Baseline Mean IoU:       {baseline_metrics['mIoU']*100:.2f}%")
    print(f"Baseline Change mIoU:    {baseline_metrics['change_mIoU']*100:.2f}%")
    print(f"Baseline Mean F1:        {baseline_metrics['mean_f1']*100:.2f}%")

    # 4. Print Confusion Matrix for Best Model
    print("\n--- Confusion Matrix (Attention Siamese Model on Test Set) ---")
    print(format_confusion_matrix_ascii(attn_metrics["confusion_matrix"]))

    # 5. Save comparison report
    comparison = {
        "dataset": "FPCD",
        "test_samples": len(test_ds),
        "comparison_table": {
            "Metric": ["Pixel Accuracy", "mIoU (Macro)", "Change mIoU", "Mean F1 Score", "Area MAE (m²)"],
            "Baseline (v1)": [
                f"{baseline_metrics['pixel_accuracy']*100:.2f}%",
                f"{baseline_metrics['mIoU']*100:.2f}%",
                f"{baseline_metrics['change_mIoU']*100:.2f}%",
                f"{baseline_metrics['mean_f1']*100:.2f}%",
                f"{baseline_metrics['change_area_error_mae_m2']} m²"
            ],
            "Siamese (v2)": [
                f"{siamese_metrics['pixel_accuracy']*100:.2f}%",
                f"{siamese_metrics['mIoU']*100:.2f}%",
                f"{siamese_metrics['change_mIoU']*100:.2f}%",
                f"{siamese_metrics['mean_f1']*100:.2f}%",
                f"{siamese_metrics['change_area_error_mae_m2']} m²"
            ],
            "Attention Siamese (v3 - Best)": [
                f"{attn_metrics['pixel_accuracy']*100:.2f}%",
                f"{attn_metrics['mIoU']*100:.2f}%",
                f"{attn_metrics['change_mIoU']*100:.2f}%",
                f"{attn_metrics['mean_f1']*100:.2f}%",
                f"{attn_metrics['change_area_error_mae_m2']} m²"
            ]
        },
        "attention_class_iou": attn_metrics["class_iou"],
        "siamese_class_iou": siamese_metrics["class_iou"],
        "baseline_class_iou": baseline_metrics["class_iou"],
        "attention_metrics": attn_metrics,
        "siamese_metrics": siamese_metrics,
        "baseline_metrics": baseline_metrics
    }

    report_file = save_path / "model_comparison_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    print(f"\n[EVAL] Model comparison saved to {report_file}")

if __name__ == "__main__":
    main()
