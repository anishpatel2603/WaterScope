"""
WATERSCOPE ML Engine - PyTorch Bi-Temporal Dataset
Loads paired T0, T1 images and multi-class change masks for farm pond change detection.
"""

import os
import json
import cv2
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset

CLASS_NAMES = [
    "Background",
    "Farm Pond Constructed",
    "Farm Pond Demolished",
    "Farm Pond Dried",
    "Farm Pond Wetted"
]

class FPCDDataset(Dataset):
    """
    Bi-temporal dataset for Farm Pond Change Detection (FPCD).
    Returns (T0, T1, Mask, Dominant_Class) tuples.
    """
    def __init__(
        self,
        data_dir: str = "./data/fpcd",
        split: str = "train",
        transform: Optional[Callable] = None,
        max_samples: Optional[int] = None
    ):
        self.data_dir = Path(data_dir).resolve()
        self.split = split
        self.transform = transform
        
        self.t0_dir = self.data_dir / "T0"
        self.t1_dir = self.data_dir / "T1"
        self.masks_dir = self.data_dir / "masks"
        manifest_path = self.data_dir / "manifest.json"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest.json not found in {self.data_dir}. Run scripts/prepare_dataset.py first.")
            
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        self.catalog = manifest.get("pairs", {})
        
        split_file = self.data_dir / f"{split}.txt"
        if not split_file.exists():
            raise FileNotFoundError(f"Split file not found: {split_file}")
            
        with open(split_file, "r", encoding="utf-8") as f:
            raw_lines = [line.strip() for line in f if line.strip()]
            
        self.keys: List[str] = [k for k in raw_lines if k in self.catalog]
        if max_samples and max_samples > 0:
            self.keys = self.keys[:max_samples]
            
        print(f"[DATASET] Loaded {len(self.keys)} bi-temporal pairs for split '{split}'")

    def get_sample_weights(self) -> torch.Tensor:
        """
        Computes sample weights for WeightedRandomSampler to oversample pairs containing
        rare minority change classes (Demolished, Dried, Wetted) during training.
        """
        presence_file = self.data_dir / "train_class_presence.json"
        class_presence = {}
        if presence_file.exists():
            try:
                with open(presence_file, "r") as f:
                    class_presence = json.load(f)
            except Exception:
                pass

        weights = []
        for k in self.keys:
            classes = class_presence.get(k, [])
            if not classes:
                dom = self.catalog.get(k, {}).get("dominant_change_class", 0)
                classes = [dom]

            w = 1.0
            if 2 in classes:
                w = max(w, 14.0)
            if 3 in classes:
                w = max(w, 10.0)
            if 4 in classes:
                w = max(w, 8.0)
            if 1 in classes:
                w = max(w, 3.0)
            weights.append(w)

        return torch.tensor(weights, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.keys)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        key = self.keys[idx]
        info = self.catalog[key]
        
        t0_path = self.t0_dir / info["t0_file"]
        t1_path = self.t1_dir / info["t1_file"]
        mask_path = self.masks_dir / info["mask_file"]
        
        # Load images as RGB numpy arrays
        t0_img = np.array(Image.open(t0_path).convert("RGB"))
        t1_img = np.array(Image.open(t1_path).convert("RGB"))
        
        # Load mask as integer 2D array
        mask_raw = np.array(Image.open(mask_path))
        if mask_raw.ndim == 3:
            mask_raw = mask_raw[:, :, 0]
        mask_arr = np.clip(mask_raw, 0, 4).astype(np.uint8)
        
        # Ensure identical spatial dimensions before augmentation
        h0, w0 = t0_img.shape[:2]
        if t1_img.shape[:2] != (h0, w0):
            t1_img = cv2.resize(t1_img, (w0, h0), interpolation=cv2.INTER_LINEAR)
        if mask_arr.shape[:2] != (h0, w0):
            mask_arr = cv2.resize(mask_arr, (w0, h0), interpolation=cv2.INTER_NEAREST)
        
        dominant_class = info.get("dominant_change_class", 0)
        
        # Apply synchronized transforms if given
        if self.transform is not None:
            augmented = self.transform(image=t0_img, image1=t1_img, mask=mask_arr)
            t0_tensor = augmented['image']
            t1_tensor = augmented['image1']
            mask_tensor = augmented['mask'].long()
        else:
            t0_tensor = torch.from_numpy(t0_img.transpose(2, 0, 1)).float() / 255.0
            t1_tensor = torch.from_numpy(t1_img.transpose(2, 0, 1)).float() / 255.0
            mask_tensor = torch.from_numpy(mask_arr).long()

        return {
            "image0": t0_tensor,
            "image1": t1_tensor,
            "mask": mask_tensor,
            "dominant_class": torch.tensor(dominant_class, dtype=torch.long),
            "key": key,
            "district": info.get("district", "Unknown"),
            "village": info.get("village", "Unknown"),
            "t0_date": info.get("t0_date", ""),
            "t1_date": info.get("t1_date", "")
        }
