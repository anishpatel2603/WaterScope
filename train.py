"""
WATERSCOPE ML Engine - Production Training CLI
Usage:
  python train.py --config configs/best.yaml
  python train.py --config configs/fpcd_siamese.yaml
  python train.py --config configs/fpcd_baseline.yaml --epochs 3
"""

import os
import argparse
import yaml
import random
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader, WeightedRandomSampler

from src.dataset.dataset import FPCDDataset
from src.dataset.transforms import get_training_transforms, get_validation_transforms
from src.models.siamese import SiameseChangeNet, AttentionSiameseChangeNet
from src.models.baseline import BaselineChangeNet
from src.engine.trainer import ModelTrainer

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def main():
    parser = argparse.ArgumentParser(description="Train WATERSCOPE Change Detection Models")
    parser.add_argument("--config", default="configs/best.yaml", help="Path to config YAML")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of training epochs")
    parser.add_argument("--batch-size", type=int, default=None, help="Override batch size")
    parser.add_argument("--device", default=None, help="Compute device (auto, cpu, or cuda)")
    parser.add_argument("--max-samples", type=int, default=None, help="Limit samples for quick verification")
    parser.add_argument("--class-balanced", action="store_true", help="Force class-balanced oversampling")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if args.epochs is not None:
        config["training"]["epochs"] = args.epochs
    if args.batch_size is not None:
        config["dataset"]["batch_size"] = args.batch_size
    if args.class_balanced:
        config["dataset"]["use_class_balanced_sampler"] = True

    # Automatic device determination
    if args.device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    seed = config.get("training", {}).get("seed", 42)
    set_seed(seed)

    data_dir = config["dataset"]["data_dir"]
    img_size = tuple(config["dataset"]["image_size"])
    batch_size = config["dataset"]["batch_size"]

    print(f"[TRAIN] Preparing DataLoaders from {data_dir} on {device.upper()}...")
    train_transform = get_training_transforms(img_size)
    val_transform = get_validation_transforms(img_size)

    train_ds = FPCDDataset(data_dir=data_dir, split="train", transform=train_transform, max_samples=args.max_samples)
    val_ds = FPCDDataset(data_dir=data_dir, split="val", transform=val_transform, max_samples=args.max_samples)

    # Class-balanced sampler for addressing extreme pixel / scene imbalance
    sampler = None
    shuffle = True
    if config["dataset"].get("use_class_balanced_sampler", False):
        sample_weights = train_ds.get_sample_weights()
        sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(train_ds), replacement=True)
        shuffle = False
        print("[TRAIN] Class-Balanced WeightedRandomSampler enabled for minority change oversampling.")

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=shuffle,
        sampler=sampler,
        num_workers=config["dataset"].get("num_workers", 0),
        pin_memory=config["dataset"].get("pin_memory", False)
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=config["dataset"].get("num_workers", 0)
    )

    # Initialize model
    model_type = config.get("model", {}).get("type", "attention_siamese")
    num_classes = config.get("model", {}).get("num_classes", 5)
    pretrained = config.get("model", {}).get("pretrained", True)

    if model_type == "attention_siamese":
        model = AttentionSiameseChangeNet(num_classes=num_classes, pretrained=pretrained)
    elif model_type in ["siamese_unet", "siamese"]:
        model = SiameseChangeNet(num_classes=num_classes, pretrained=pretrained, use_attention=False)
    else:
        model = BaselineChangeNet(num_classes=num_classes, pretrained=pretrained)

    trainer = ModelTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        device=device
    )

    results = trainer.run()
    print("[TRAIN] Training workflow completed successfully.")
    return results

if __name__ == "__main__":
    main()
