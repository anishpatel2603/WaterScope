"""
WATERSCOPE ML Engine - Dataset Verification & Health Check
Validates bi-temporal image pair completeness, dimensions, mask class labels,
detects corrupted files, and produces an authoritative audit report.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm

DEFAULT_DATA_DIR = "./data/fpcd"
ALLOWED_CLASSES = {0, 1, 2, 3, 4}

def verify_dataset(data_dir: str = DEFAULT_DATA_DIR, sample_limit: int = 50) -> dict:
    data_path = Path(data_dir).resolve()
    print("==================================================")
    print("WATERSCOPE DATASET INTEGRITY & VALIDATION REPORT")
    print(f"Directory: {data_path}")
    print("==================================================")
    
    report = {
        "status": "HEALTHY",
        "dataset_path": str(data_path),
        "manifest_exists": False,
        "splits_found": {},
        "t0_count": 0,
        "t1_count": 0,
        "mask_count": 0,
        "matched_pairs": 0,
        "dimension_mismatches": [],
        "invalid_label_files": [],
        "corrupted_images": [],
        "warnings": []
    }
    
    t0_dir = data_path / "T0"
    t1_dir = data_path / "T1"
    masks_dir = data_path / "masks"
    manifest_path = data_path / "manifest.json"
    
    for req, p in [("T0", t0_dir), ("T1", t1_dir), ("masks", masks_dir)]:
        if not p.exists():
            report["status"] = "INCOMPLETE"
            report["warnings"].append(f"Directory missing: {req}")
            print(f"[VERIFY ERROR] Required directory missing: {p}")
            return report

    report["manifest_exists"] = manifest_path.exists()
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
    # Splits check
    for split in ["train.txt", "val.txt", "test.txt"]:
        sp_file = data_path / split
        if sp_file.exists():
            with open(sp_file, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip()]
            report["splits_found"][split] = len(lines)
        else:
            report["warnings"].append(f"Split file missing: {split}")

    t0_files = list(t0_dir.glob("*.jpg")) + list(t0_dir.glob("*.png"))
    t1_files = list(t1_dir.glob("*.jpg")) + list(t1_dir.glob("*.png"))
    mask_files = list(masks_dir.glob("*.png")) + list(masks_dir.glob("*.jpg"))
    
    report["t0_count"] = len(t0_files)
    report["t1_count"] = len(t1_files)
    report["mask_count"] = len(mask_files)
    
    pairs = manifest.get("pairs", {})
    report["matched_pairs"] = len(pairs)
    
    # Inspect a sample of triplets
    sample_keys = list(pairs.keys())
    if sample_limit and sample_limit > 0:
        sample_keys = sample_keys[:sample_limit]
        
    print(f"[VERIFY] Checking integrity of {len(sample_keys)} bi-temporal image/mask pairs...")
    for key in tqdm(sample_keys, desc="Verifying Pairs"):
        info = pairs[key]
        p0 = t0_dir / info["t0_file"]
        p1 = t1_dir / info["t1_file"]
        pm = masks_dir / info["mask_file"]
        
        if not (p0.exists() and p1.exists() and pm.exists()):
            report["corrupted_images"].append({"key": key, "error": "Missing file on disk"})
            continue
            
        try:
            with Image.open(p0) as img0:
                w0, h0 = img0.size
            with Image.open(p1) as img1:
                w1, h1 = img1.size
            with Image.open(pm) as imgm:
                wm, hm = imgm.size
                arr_m = np.array(imgm)
                
            if (w0, h0) != (w1, h1) or (w0, h0) != (wm, hm):
                report["dimension_mismatches"].append({
                    "key": key,
                    "t0": (w0, h0),
                    "t1": (w1, h1),
                    "mask": (wm, hm)
                })
                
            unique_labels = set(np.unique(arr_m))
            invalid = unique_labels - ALLOWED_CLASSES
            if invalid:
                report["invalid_label_files"].append({
                    "key": key,
                    "unexpected_labels": [int(x) for x in invalid]
                })
        except Exception as err:
            report["corrupted_images"].append({"key": key, "error": str(err)})

    if report["corrupted_images"] or report["dimension_mismatches"] or report["invalid_label_files"]:
        report["status"] = "ISSUES_FOUND"
    elif report["warnings"]:
        report["status"] = "WARNINGS"
    else:
        report["status"] = "HEALTHY"

    print("\n--------------------------------------------------")
    print(f"VERIFICATION STATUS: {report['status']}")
    print(f"Total T0 Images:     {report['t0_count']}")
    print(f"Total T1 Images:     {report['t1_count']}")
    print(f"Total Masks:         {report['mask_count']}")
    print(f"Matched Triplets:    {report['matched_pairs']}")
    print(f"Splits:              {report['splits_found']}")
    print(f"Corrupted Images:    {len(report['corrupted_images'])}")
    print(f"Dimension Mismatches:{len(report['dimension_mismatches'])}")
    print(f"Invalid Label Files: {len(report['invalid_label_files'])}")
    print("--------------------------------------------------")
    
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify FPCD dataset integrity")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Path to data directory")
    parser.add_argument("--sample", type=int, default=50, help="Number of pairs to sample verify")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    rep = verify_dataset(args.data_dir, args.sample)
    if args.json:
        print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["status"] in ["HEALTHY", "WARNINGS"] else 1)
