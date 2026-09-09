"""
WATERSCOPE ML Engine - Production Model Trainer
Orchestrates training, validation, multi-metric evaluation, AdamW optimization,
Cosine Annealing schedule, Focal-Tversky loss, and checkpoint management.
Saves training_history.csv and best_model.pt based on Validation Macro F1 / Mean IoU.
"""

import os
import csv
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.models.loss import ChangeDetectionLoss
from src.models.metrics import ChangeDetectionMetrics

class ModelTrainer:
    def __init__(
        self,
        model: torch.nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        config: Dict[str, Any],
        device: str = "cpu"
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.device = torch.device(device)
        self.model.to(self.device)

        t_cfg = config.get("training", {})
        self.epochs = t_cfg.get("epochs", 5)
        self.lr = t_cfg.get("learning_rate", 0.001)
        self.weight_decay = t_cfg.get("weight_decay", 1e-4)
        self.save_dir = Path(t_cfg.get("save_dir", "./models"))
        self.log_dir = Path(t_cfg.get("log_dir", "./experiments"))
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Loss setup with Focal + Tversky support
        class_weights = t_cfg.get("class_weights", [0.2, 2.5, 6.0, 5.0, 4.0])
        weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(self.device)
        loss_type = t_cfg.get("loss_type", "focal_tversky")

        self.criterion = ChangeDetectionLoss(
            class_weights=weights_tensor,
            loss_type=loss_type,
            ce_weight=t_cfg.get("loss_ce_weight", 0.4),
            seg_weight=t_cfg.get("loss_dice_weight", 0.6),
            aux_cls_weight=t_cfg.get("aux_cls_weight", 0.2),
            gamma=t_cfg.get("focal_gamma", 2.0),
            tversky_alpha=t_cfg.get("tversky_alpha", 0.3),
            tversky_beta=t_cfg.get("tversky_beta", 0.7)
        )

        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.lr,
            weight_decay=self.weight_decay
        )
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=max(1, self.epochs))

        self.history = {
            "train_loss": [],
            "val_loss": [],
            "val_mIoU": [],
            "val_macro_f1": [],
            "val_accuracy": [],
            "learning_rates": []
        }
        self.best_val_score = -1.0
        self.csv_path = self.log_dir / "training_history.csv"

        # Initialize CSV log header
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Epoch", "Train_Loss", "Val_Loss", "Accuracy", "Macro_F1", "Mean_IoU", "Dice", "Learning_Rate"])

    def train_epoch(self, epoch: int) -> float:
        self.model.train()
        total_loss = 0.0
        pbar = tqdm(self.train_loader, desc=f"Epoch {epoch+1:02d}/{self.epochs:02d} [Train]")

        for batch in pbar:
            img0 = batch["image0"].to(self.device)
            img1 = batch["image1"].to(self.device)
            masks = batch["mask"].to(self.device)
            dom_cls = batch["dominant_class"].to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(img0, img1)

            loss = self.criterion(
                seg_logits=outputs["seg_logits"],
                seg_targets=masks,
                cls_logits=outputs.get("cls_logits"),
                cls_targets=dom_cls
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        return total_loss / max(1, len(self.train_loader))

    def evaluate(self, loader: DataLoader) -> Dict[str, Any]:
        self.model.eval()
        total_loss = 0.0
        metrics = ChangeDetectionMetrics(num_classes=5)

        with torch.no_grad():
            for batch in loader:
                img0 = batch["image0"].to(self.device)
                img1 = batch["image1"].to(self.device)
                masks = batch["mask"].to(self.device)
                dom_cls = batch["dominant_class"].to(self.device)

                outputs = self.model(img0, img1)
                loss = self.criterion(
                    seg_logits=outputs["seg_logits"],
                    seg_targets=masks,
                    cls_logits=outputs.get("cls_logits"),
                    cls_targets=dom_cls
                )
                total_loss += loss.item()
                metrics.update(outputs["seg_logits"], masks)

        results = metrics.compute()
        results["loss"] = total_loss / max(1, len(loader))
        return results

    def run(self) -> Dict[str, Any]:
        model_name = self.config.get("model", {}).get("name", "waterscope_model")
        print("=" * 60)
        print(f"STARTING REPRODUCIBLE TRAINING: {model_name}")
        print(f"Device: {self.device} | Epochs: {self.epochs} | LR: {self.lr}")
        print("=" * 60)

        start_time = time.time()
        best_metrics = {}

        for epoch in range(self.epochs):
            train_loss = self.train_epoch(epoch)
            val_results = self.evaluate(self.val_loader)

            curr_lr = self.optimizer.param_groups[0]["lr"]
            self.scheduler.step()

            val_acc = val_results.get("pixel_accuracy", 0.0)
            val_miou = val_results.get("mIoU", 0.0)
            val_f1 = val_results.get("mean_f1", 0.0)
            val_loss = val_results["loss"]

            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["val_mIoU"].append(val_miou)
            self.history["val_macro_f1"].append(val_f1)
            self.history["val_accuracy"].append(val_acc)
            self.history["learning_rates"].append(curr_lr)

            # Append to training_history.csv
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    epoch + 1,
                    f"{train_loss:.4f}",
                    f"{val_loss:.4f}",
                    f"{val_acc:.4f}",
                    f"{val_f1:.4f}",
                    f"{val_miou:.4f}",
                    f"{val_f1:.4f}",
                    f"{curr_lr:.6f}"
                ])

            print(f"Epoch {epoch+1:02d} Summary: Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Macro F1: {val_f1*100:.2f}% | mIoU: {val_miou*100:.2f}% | Acc: {val_acc*100:.2f}%")

            # Selection criterion: Composite validation Macro F1 and mIoU (NOT raw accuracy)
            val_score = 0.5 * val_f1 + 0.5 * val_miou
            if val_score > self.best_val_score:
                self.best_val_score = val_score
                best_metrics = val_results

                # Save best checkpoint
                best_ckpt_path = self.save_dir / f"{model_name}.pt"
                torch.save({
                    "model_state_dict": self.model.state_dict(),
                    "epoch": epoch + 1,
                    "val_metrics": val_results,
                    "config": self.config
                }, best_ckpt_path)

                # Save best_model.pt
                torch.save({
                    "model_state_dict": self.model.state_dict(),
                    "epoch": epoch + 1,
                    "val_metrics": val_results,
                    "config": self.config
                }, self.save_dir / "best_model.pt")

                print(f"[CHECKPOINT] Saved best model to {best_ckpt_path} (Score: {self.best_val_score:.4f}, mIoU: {val_miou:.4f}, F1: {val_f1:.4f})")

        # Save final_model.pt after all epochs
        torch.save(self.model.state_dict(), self.save_dir / "final_model.pt")

        total_time = time.time() - start_time
        print(f"[TRAIN] Finished {self.epochs} epochs in {total_time:.2f}s.")

        # Save comprehensive training history JSON
        history_path = self.log_dir / "training_history.json"
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump({
                "model_name": model_name,
                "history": self.history,
                "best_metrics": best_metrics,
                "duration_seconds": round(total_time, 2)
            }, f, indent=2)

        return best_metrics
