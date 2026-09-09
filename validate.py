"""
WATERSCOPE ML Engine - Model Validation CLI
Usage:
  python validate.py --checkpoint models/fpcd_siamese_v1.pt --config configs/fpcd_siamese.yaml
"""

import os
import argparse
import yaml
import torch
from torch.utils.data import DataLoader

from src.dataset.dataset import FPCDDataset
from src.dataset.transforms import get_validation_transforms
from src.models.siamese import SiameseChangeNet
from src.models.baseline import BaselineChangeNet
from src.models.metrics import ChangeDetectionMetrics

def main():
    parser = argparse.ArgumentParser(description="Validate WATERSCOPE Model")
    parser.add_argument("--checkpoint", default="models/fpcd_siamese_v1.pt", help="Path to checkpoint .pt")
    parser.add_argument("--config", default="configs/fpcd_siamese.yaml", help="Path to config YAML")
    parser.add_argument("--device", default="cpu", help="Compute device")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    data_dir = config["dataset"]["data_dir"]
    img_size = tuple(config["dataset"]["image_size"])
    batch_size = config["dataset"]["batch_size"]

    val_transform = get_validation_transforms(img_size)
    val_ds = FPCDDataset(data_dir=data_dir, split="val", transform=val_transform)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model_type = config.get("model", {}).get("type", "siamese_unet")
    if model_type == "siamese_unet":
        model = SiameseChangeNet(num_classes=5, pretrained=False)
    else:
        model = BaselineChangeNet(num_classes=5, pretrained=False)

    if os.path.exists(args.checkpoint):
        ckpt = torch.load(args.checkpoint, map_location=args.device)
        model.load_state_dict(ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt)
        print(f"[VALIDATE] Loaded checkpoint from {args.checkpoint}")
    else:
        print(f"[VALIDATE WARNING] Checkpoint {args.checkpoint} not found. Using initialized weights.")

    model.to(args.device)
    model.eval()

    metrics = ChangeDetectionMetrics(num_classes=5)
    with torch.no_grad():
        for batch in val_loader:
            img0 = batch["image0"].to(args.device)
            img1 = batch["image1"].to(args.device)
            masks = batch["mask"].to(args.device)
            outputs = model(img0, img1)
            metrics.update(outputs["seg_logits"], masks)

    res = metrics.compute()
    print("==================================================")
    print(f"VALIDATION RESULTS: {os.path.basename(args.checkpoint)}")
    print(f"Pixel Accuracy: {res['pixel_accuracy'] * 100:.2f}%")
    print(f"Mean IoU (mIoU): {res['mIoU'] * 100:.2f}%")
    print(f"Change mIoU:    {res['change_mIoU'] * 100:.2f}%")
    print(f"Mean F1 Score:  {res['mean_f1'] * 100:.2f}%")
    print(f"Class-wise IoU: {res['class_iou']}")
    print(f"Change Area MAE: {res['change_area_error_mae_m2']} m²")
    print("==================================================")

if __name__ == "__main__":
    main()
