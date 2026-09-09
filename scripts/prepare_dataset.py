"""
WATERSCOPE ML Engine - Dataset Preparation and Ingestion Pipeline
Extracts raw FPCD archives, matches bi-temporal triplets (T0, T1, Mask), organizes directories,
generates geographic-aware train/val/test splits without location leakage,
computes dataset statistics & class frequencies, and writes manifest.json.
"""

import os
import sys
import re
import zipfile
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image
from tqdm import tqdm

DEFAULT_DATA_DIR = "./data/fpcd"

CLASS_MAPPING = {
    0: "Background",
    1: "Farm Pond Constructed",
    2: "Farm Pond Demolished",
    3: "Farm Pond Dried",
    4: "Farm Pond Wetted"
}

def extract_zip(zip_path: Path, extract_to: Path):
    """Extract zip archive safely."""
    print(f"[PREPARE] Extracting {zip_path.name} to {extract_to}...")
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def parse_temporal_filename(name: str):
    """
    Parses filenames like 'Akola_Akhatwada_200703_0.jpg'
    Returns (district, village, yyyymm, index, prefix)
    """
    m = re.match(r'^(.*)_(\d{6})_(\d+)\.(jpg|png|jpeg)$', name, re.IGNORECASE)
    if m:
        prefix = m.group(1)
        yyyymm = m.group(2)
        idx = m.group(3)
        parts = prefix.split('_')
        district = parts[0] if len(parts) > 0 else "Unknown"
        village = parts[1] if len(parts) > 1 else "Unknown"
        return district, village, yyyymm, idx, f"{prefix}_{idx}"
    return None

def parse_mask_filename(name: str):
    """
    Parses mask filenames like 'Akola_Akhatwada_0.png'
    Returns (district, village, index, prefix)
    """
    m = re.match(r'^(.*)_(\d+)\.(jpg|png|jpeg)$', name, re.IGNORECASE)
    if m:
        prefix = m.group(1)
        idx = m.group(2)
        parts = prefix.split('_')
        district = parts[0] if len(parts) > 0 else "Unknown"
        village = parts[1] if len(parts) > 1 else "Unknown"
        return district, village, idx, f"{prefix}_{idx}"
    return None

def prepare_dataset(data_dir: str = DEFAULT_DATA_DIR, force: bool = False) -> bool:
    """Run full extraction, pairing, geographic splitting, verification, and manifest generation."""
    data_path = Path(data_dir).resolve()
    raw_dir = data_path / "raw"
    t0_dir = data_path / "T0"
    t1_dir = data_path / "T1"
    masks_dir = data_path / "masks"
    annot_dir = data_path / "annotations"
    
    t0_dir.mkdir(parents=True, exist_ok=True)
    t1_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    annot_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_file = data_path / "manifest.json"
    if manifest_file.exists() and not force:
        print("[PREPARE] manifest.json already exists. Dataset is prepared. Pass --force to re-prepare.")
        return True

    # 1. Check raw archives and extract if needed
    t0_zip = raw_dir / "T0.zip"
    t1_zip = raw_dir / "T1.zip"
    mask_zip = raw_dir / "multi_class_masks.zip"
    
    if len(list(t0_dir.glob("*.jpg"))) == 0 and t0_zip.exists():
        extract_zip(t0_zip, t0_dir)
    if len(list(t1_dir.glob("*.jpg"))) == 0 and t1_zip.exists():
        extract_zip(t1_zip, t1_dir)
    if len(list(masks_dir.glob("*.png"))) == 0 and mask_zip.exists():
        extract_zip(mask_zip, masks_dir)

    # Flatten nested masks if they were in train/test subfolders
    for sub in ["train", "test"]:
        sub_p = masks_dir / sub
        if sub_p.exists() and sub_p.is_dir():
            for f in sub_p.glob("*.png"):
                dest = masks_dir / f.name
                if not dest.exists():
                    shutil.copy2(f, dest)

    # Copy annotations & split files if in raw
    for fname in ["object_annotations_test_coco.json", "object_annotations_train_coco.json", "README.txt"]:
        p = raw_dir / fname
        if p.exists():
            shutil.copy2(p, annot_dir / fname)
            
    # 2. Build index of T0, T1, and Masks
    t0_files = list(t0_dir.glob("*.jpg")) + list(t0_dir.glob("*.png"))
    t1_files = list(t1_dir.glob("*.jpg")) + list(t1_dir.glob("*.png"))
    mask_files = list(masks_dir.glob("*.png")) + list(masks_dir.glob("*.jpg"))

    t0_catalog = {}
    for p in t0_files:
        parsed = parse_temporal_filename(p.name)
        if parsed:
            district, village, yyyymm, idx, pair_key = parsed
            t0_catalog[pair_key] = {
                "file": p.name,
                "district": district,
                "village": village,
                "date": f"{yyyymm[:4]}-{yyyymm[4:]}"
            }

    t1_catalog = {}
    for p in t1_files:
        parsed = parse_temporal_filename(p.name)
        if parsed:
            district, village, yyyymm, idx, pair_key = parsed
            t1_catalog[pair_key] = {
                "file": p.name,
                "district": district,
                "village": village,
                "date": f"{yyyymm[:4]}-{yyyymm[4:]}"
            }

    mask_catalog = {}
    for p in mask_files:
        parsed = parse_mask_filename(p.name)
        if parsed:
            district, village, idx, pair_key = parsed
            mask_catalog[pair_key] = {
                "file": p.name
            }

    # Match common pairs
    common_keys = sorted(list(set(t0_catalog.keys()) & set(t1_catalog.keys()) & set(mask_catalog.keys())))
    print(f"[PREPARE] Matched {len(common_keys)} complete bi-temporal triplets (T0, T1, Mask).")
    
    if len(common_keys) == 0:
        print("[PREPARE ERROR] No common pairs found across T0, T1, and masks directories.")
        return False

    # 3. Geographic/Group-aware split to prevent spatial data leakage
    # Group by (District, Village)
    village_groups = {}
    for key in common_keys:
        info = t0_catalog[key]
        group = f"{info['district']}_{info['village']}"
        if group not in village_groups:
            village_groups[group] = []
        village_groups[group].append(key)
        
    print(f"[PREPARE] Identified {len(village_groups)} distinct village geographic clusters.")
    
    # Sort groups deterministically and split by cluster
    np.random.seed(42)
    sorted_groups = sorted(village_groups.keys())
    np.random.shuffle(sorted_groups)
    
    train_keys = []
    val_keys = []
    test_keys = []
    
    total_samples = len(common_keys)
    target_test = int(total_samples * 0.15)
    target_val = int(total_samples * 0.15)
    
    for g in sorted_groups:
        keys = village_groups[g]
        if len(test_keys) < target_test:
            test_keys.extend(keys)
        elif len(val_keys) < target_val:
            val_keys.extend(keys)
        else:
            train_keys.extend(keys)
            
    # Sort for reproducibility
    train_keys = sorted(train_keys)
    val_keys = sorted(val_keys)
    test_keys = sorted(test_keys)
    
    # Save split files (each line is pair_key)
    with open(data_path / "train.txt", "w", encoding="utf-8") as f:
        for k in train_keys:
            f.write(f"{k}\n")
    with open(data_path / "val.txt", "w", encoding="utf-8") as f:
        for k in val_keys:
            f.write(f"{k}\n")
    with open(data_path / "test.txt", "w", encoding="utf-8") as f:
        for k in test_keys:
            f.write(f"{k}\n")
            
    print(f"[PREPARE] Geographic splits written: {len(train_keys)} train, {len(val_keys)} val, {len(test_keys)} test.")

    # 4. Compute class pixel statistics and analyze mask distributions
    print("[PREPARE] Computing dataset class statistics and validating image pairs...")
    class_counts = {int(k): 0 for k in CLASS_MAPPING.keys()}
    dimensions = set()
    corrupted = []
    pair_records = {}

    for key in tqdm(common_keys, desc="Analyzing masks & metadata"):
        t0_info = t0_catalog[key]
        t1_info = t1_catalog[key]
        m_info = mask_catalog[key]
        
        t0_path = t0_dir / t0_info["file"]
        t1_path = t1_dir / t1_info["file"]
        m_path = masks_dir / m_info["file"]
        
        try:
            mask_img = Image.open(m_path)
            mask_arr = np.array(mask_img)
            if mask_arr.ndim == 3:
                mask_arr = mask_arr[:, :, 0]
                
            unique, counts = np.unique(mask_arr, return_counts=True)
            non_zero_classes = []
            for u, c in zip(unique, counts):
                u_int = int(u)
                if u_int in class_counts:
                    class_counts[u_int] += int(c)
                if u_int > 0:
                    non_zero_classes.append(u_int)
                    
            dominant = int(non_zero_classes[0]) if len(non_zero_classes) == 1 else (
                int(max(set(non_zero_classes), key=non_zero_classes.count)) if non_zero_classes else 0
            )

            pair_records[key] = {
                "pair_key": key,
                "district": t0_info["district"],
                "village": t0_info["village"],
                "t0_file": t0_info["file"],
                "t1_file": t1_info["file"],
                "mask_file": m_info["file"],
                "t0_date": t0_info["date"],
                "t1_date": t1_info["date"],
                "dominant_change_class": dominant,
                "dominant_change_label": CLASS_MAPPING.get(dominant, "Unknown")
            }
        except Exception as err:
            corrupted.append({"key": key, "error": str(err)})

    # Calculate class frequencies and balanced weights
    total_pixels = sum(class_counts.values()) or 1
    class_frequencies = {k: count / total_pixels for k, count in class_counts.items()}
    
    # Inverse frequency weights with clipping
    class_weights = {}
    for k, freq in class_frequencies.items():
        if k == 0:
            class_weights[k] = 0.20 # background downweighted
        elif freq > 0:
            w = 1.0 / (np.sqrt(freq) + 1e-4)
            class_weights[k] = round(float(min(3.0, max(1.2, w / 40.0))), 2)
        else:
            class_weights[k] = 2.0
            
    manifest = {
        "dataset_name": "Farm Pond Change Detection (FPCD)",
        "dataset_id": "ctundia/FPCD",
        "location": "Maharashtra, India",
        "resolution_meters_per_pixel": 1.0,
        "zoom_level": 18,
        "temporal_range": "2007-2021 (Minimum 2 years, Maximum 9 years)",
        "total_pairs": len(common_keys),
        "split_counts": {
            "train": len(train_keys),
            "validation": len(val_keys),
            "test": len(test_keys)
        },
        "image_dimensions": [1024, 768],
        "classes": CLASS_MAPPING,
        "class_pixel_counts": class_counts,
        "class_frequencies": class_frequencies,
        "suggested_class_weights": class_weights,
        "pairs": pair_records,
        "corrupted_pairs": corrupted,
        "prepared_at": datetime.now().isoformat()
    }
    
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"[PREPARE] Successfully created manifest with {len(pair_records)} verified pairs at {manifest_file}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and prepare FPCD dataset")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Path to data directory")
    parser.add_argument("--force", action="store_true", help="Force re-extraction and manifest rebuild")
    args = parser.parse_args()
    
    ok = prepare_dataset(args.data_dir, args.force)
    sys.exit(0 if ok else 1)
