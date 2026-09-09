"""
WATERSCOPE ML Engine - Automated Error Analysis & Diagnostic Reporting
Analyzes:
- True Positives, False Positives, False Negatives
- Confusion Matrix & Most Confused Classes
- Worst-Performing Locations (Villages/Districts)
- Low-Confidence / Borderline Predictions
- Generates reports/error_analysis.html and saves representative visual error samples
"""

import os
import json
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from src.dataset.dataset import FPCDDataset, CLASS_NAMES
from src.dataset.transforms import get_validation_transforms
from src.models.siamese import SiameseChangeNet, AttentionSiameseChangeNet
from src.models.baseline import BaselineChangeNet
from src.models.metrics import ChangeDetectionMetrics

COLOR_MAP = {
    0: (20, 20, 20),        # Background
    1: (34, 197, 94),       # Constructed (Green)
    2: (239, 68, 68),       # Demolished (Red)
    3: (249, 115, 22),      # Dried (Orange)
    4: (6, 182, 212)        # Wetted (Cyan)
}

def colorize_mask(mask_arr: np.ndarray) -> Image.Image:
    h, w = mask_arr.shape[:2]
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for c, col in COLOR_MAP.items():
        rgb[mask_arr == c] = col
    return Image.fromarray(rgb)

def run_error_analysis(
    model_path: str = "models/fpcd_siamese_v1.pt",
    model_type: str = "siamese",
    data_dir: str = "./data/fpcd",
    split: str = "val",
    output_dir: str = "./reports",
    device: str = "cpu",
    max_samples: int = 50
):
    out_dir = Path(output_dir)
    samples_dir = out_dir / "error_samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    dev = torch.device(device)
    if model_type == "attention_siamese":
        model = AttentionSiameseChangeNet(num_classes=5, pretrained=False)
    elif model_type == "siamese":
        model = SiameseChangeNet(num_classes=5, pretrained=False, use_attention=False)
    else:
        model = BaselineChangeNet(num_classes=5, pretrained=False)

    if os.path.exists(model_path):
        ckpt = torch.load(model_path, map_location=dev)
        model.load_state_dict(ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt)
        print(f"[ERROR_ANALYSIS] Loaded model weights from {model_path}")
    else:
        print(f"[ERROR_ANALYSIS WARNING] Model weights not found at {model_path}. Using initialized weights.")

    model.to(dev)
    model.eval()

    val_transform = get_validation_transforms((256, 256))
    dataset = FPCDDataset(data_dir=data_dir, split=split, transform=val_transform, max_samples=max_samples)
    loader = DataLoader(dataset, batch_size=1, shuffle=False)

    metrics = ChangeDetectionMetrics(num_classes=5)
    location_errors = {}
    error_cases = []
    low_confidence_cases = []

    print(f"[ERROR_ANALYSIS] Evaluating {len(dataset)} samples for error breakdown...")

    with torch.no_grad():
        for i, batch in enumerate(loader):
            img0 = batch["image0"].to(dev)
            img1 = batch["image1"].to(dev)
            mask = batch["mask"].to(dev)
            key = batch["key"][0]
            district = batch["district"][0]
            village = batch["village"][0]
            loc_key = f"{district}_{village}"

            outputs = model(img0, img1)
            seg_logits = outputs["seg_logits"]
            probs = F.softmax(seg_logits, dim=1)
            conf, preds = torch.max(probs, dim=1)

            metrics.update(seg_logits, mask)

            pred_np = preds[0].cpu().numpy()
            gt_np = mask[0].cpu().numpy()
            conf_np = conf[0].cpu().numpy()

            # Error breakdown
            fp_pixels = int(np.sum((gt_np == 0) & (pred_np > 0)))
            fn_pixels = int(np.sum((gt_np > 0) & (pred_np == 0)))
            tp_pixels = int(np.sum((gt_np > 0) & (pred_np == gt_np)))
            mismatch_pixels = int(np.sum((gt_np > 0) & (pred_np > 0) & (pred_np != gt_np)))
            mean_conf = float(np.mean(conf_np))

            if loc_key not in location_errors:
                location_errors[loc_key] = {"total": 0, "fp": 0, "fn": 0, "tp": 0}
            location_errors[loc_key]["total"] += 1
            location_errors[loc_key]["fp"] += fp_pixels
            location_errors[loc_key]["fn"] += fn_pixels
            location_errors[loc_key]["tp"] += tp_pixels

            # Collect severe error sample
            if (fp_pixels > 200 or fn_pixels > 200 or mismatch_pixels > 100) and len(error_cases) < 8:
                # Save visual error comparison
                t0_unnorm = ((img0[0].cpu().permute(1, 2, 0).numpy() * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])).clip(0, 1) * 255).astype(np.uint8)
                t1_unnorm = ((img1[0].cpu().permute(1, 2, 0).numpy() * np.array([0.229, 0.224, 0.225]) + np.array([0.485, 0.456, 0.406])).clip(0, 1) * 255).astype(np.uint8)

                img_t0 = Image.fromarray(t0_unnorm)
                img_t1 = Image.fromarray(t1_unnorm)
                img_gt = colorize_mask(gt_np)
                img_pred = colorize_mask(pred_np)

                # Composite montage: T0 | T1 | Ground Truth | Prediction
                composite = Image.new("RGB", (256 * 4, 256))
                composite.paste(img_t0, (0, 0))
                composite.paste(img_t1, (256, 0))
                composite.paste(img_gt, (512, 0))
                composite.paste(img_pred, (768, 0))

                sample_fname = f"error_{key}.jpg"
                sample_path = samples_dir / sample_fname
                composite.save(sample_path, quality=90)

                error_cases.append({
                    "key": key,
                    "location": loc_key,
                    "image_file": sample_fname,
                    "false_positives": fp_pixels,
                    "false_negatives": fn_pixels,
                    "mismatches": mismatch_pixels,
                    "mean_confidence": round(mean_conf, 4)
                })

            if mean_conf < 0.70:
                low_confidence_cases.append({
                    "key": key,
                    "location": loc_key,
                    "mean_confidence": round(mean_conf, 4)
                })

    computed = metrics.compute()
    cm = computed.get("confusion_matrix", [])

    # HTML Report Generation
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WATERSCOPE ML Engine - Error Analysis Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }}
  h1, h2, h3 {{ color: #38bdf8; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
  th, td {{ padding: 8px 12px; border: 1px solid #334155; text-align: left; }}
  th {{ background: #0f172a; color: #38bdf8; }}
  .metric-box {{ display: inline-block; background: #0f172a; border: 1px solid #38bdf8; border-radius: 6px; padding: 12px 18px; margin-right: 12px; }}
  .metric-val {{ font-size: 20px; font-weight: bold; color: #4ade80; font-family: monospace; }}
  .img-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 16px; }}
  .img-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 10px; }}
  .img-card img {{ width: 100%; border-radius: 4px; display: block; }}
  .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase; }}
  .badge-danger {{ background: #ef4444; color: white; }}
  .badge-warn {{ background: #f59e0b; color: white; }}
  .badge-ok {{ background: #10b981; color: white; }}
</style>
</head>
<body>
<h1>WATERSCOPE ML Diagnostic & Error Analysis Report</h1>
<p>Generated for evaluation split: <strong>{split.upper()}</strong> | Total Pairs: <strong>{len(dataset)}</strong></p>

<div class="card">
  <h2>Overall Validation Metrics</h2>
  <div class="metric-box">
    <div>Pixel Accuracy</div>
    <div class="metric-val">{computed.get('pixel_accuracy', 0)*100:.2f}%</div>
  </div>
  <div class="metric-box">
    <div>Mean IoU (Macro)</div>
    <div class="metric-val">{computed.get('mIoU', 0)*100:.2f}%</div>
  </div>
  <div class="metric-box">
    <div>Change mIoU (Classes 1..4)</div>
    <div class="metric-val">{computed.get('change_mIoU', 0)*100:.2f}%</div>
  </div>
  <div class="metric-box">
    <div>Mean F1 / Dice</div>
    <div class="metric-val">{computed.get('mean_f1', 0)*100:.2f}%</div>
  </div>
</div>

<div class="card">
  <h2>Class-wise IoU & Detection Metrics</h2>
  <table>
    <tr>
      <th>Class Name</th>
      <th>IoU</th>
      <th>F1 Score</th>
      <th>Precision</th>
      <th>Recall</th>
    </tr>
"""
    for cname in CLASS_NAMES:
        iou = computed.get("class_iou", {}).get(cname, 0.0)
        f1 = computed.get("class_f1_dice", {}).get(cname, 0.0)
        prec = computed.get("class_precision", {}).get(cname, 0.0)
        rec = computed.get("class_recall", {}).get(cname, 0.0)
        html_content += f"""
    <tr>
      <td><strong>{cname}</strong></td>
      <td>{iou*100:.2f}%</td>
      <td>{f1*100:.2f}%</td>
      <td>{prec*100:.2f}%</td>
      <td>{rec*100:.2f}%</td>
    </tr>
"""
    html_content += """
  </table>
</div>

<div class="card">
  <h2>Geographic Location Performance Breakdown</h2>
  <table>
    <tr>
      <th>Location (District_Village)</th>
      <th>Evaluated Pairs</th>
      <th>True Positive Pixels</th>
      <th>False Positive Pixels</th>
      <th>False Negative Pixels</th>
    </tr>
"""
    for loc, data in location_errors.items():
        html_content += f"""
    <tr>
      <td><strong>{loc}</strong></td>
      <td>{data['total']}</td>
      <td>{data['tp']:,}</td>
      <td style="color:#ef4444">{data['fp']:,}</td>
      <td style="color:#f59e0b">{data['fn']:,}</td>
    </tr>
"""

    html_content += """
  </table>
</div>

<div class="card">
  <h2>Representative Misclassified Cases</h2>
  <p>Columns in each image: <strong>T0 Before (RGB) | T1 After (RGB) | Ground Truth Mask | Predicted Change Mask</strong></p>
  <div class="img-grid">
"""
    for case in error_cases:
        html_content += f"""
    <div class="img-card">
      <img src="error_samples/{case['image_file']}" alt="{case['key']}" />
      <div style="margin-top: 8px; font-size: 11px;">
        <strong>{case['key']}</strong> ({case['location']})<br/>
        <span class="badge badge-danger">FP: {case['false_positives']} px</span>
        <span class="badge badge-warn">FN: {case['false_negatives']} px</span>
        <span class="badge badge-ok">Conf: {case['mean_confidence']*100:.1f}%</span>
      </div>
    </div>
"""

    html_content += """
  </div>
</div>

</body>
</html>
"""

    report_path = out_dir / "error_analysis.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[ERROR_ANALYSIS] Saved HTML diagnostic report to {report_path}")

    # Also save JSON summary
    json_path = out_dir / "error_analysis_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": computed,
            "location_errors": location_errors,
            "error_cases_count": len(error_cases),
            "low_confidence_count": len(low_confidence_cases)
        }, f, indent=2)

    return computed

def main():
    parser = argparse.ArgumentParser(description="Run WATERSCOPE ML Error Analysis")
    parser.add_argument("--model-path", default="models/fpcd_siamese_v1.pt")
    parser.add_argument("--model-type", default="siamese", choices=["siamese", "baseline", "attention_siamese"])
    parser.add_argument("--data-dir", default="./data/fpcd")
    parser.add_argument("--split", default="val", choices=["val", "test", "train"])
    parser.add_argument("--output-dir", default="./reports")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-samples", type=int, default=30)
    args = parser.parse_args()

    run_error_analysis(
        model_path=args.model_path,
        model_type=args.model_type,
        data_dir=args.data_dir,
        split=args.split,
        output_dir=args.output_dir,
        device=args.device,
        max_samples=args.max_samples
    )

if __name__ == "__main__":
    main()
