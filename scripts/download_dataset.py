"""
WATERSCOPE ML Engine - Automatic Dataset Synchronizer
Downloads the Farm Pond Change Detection (FPCD) dataset from Hugging Face.
Dataset ID: ctundia/FPCD
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download, HfApi

load_dotenv()

DATASET_ID = os.getenv("FPCD_DATASET_ID", "ctundia/FPCD")
DEFAULT_DATA_DIR = os.getenv("FPCD_DATA_DIR", "./data/fpcd")

REQUIRED_FILES = [
    "T0.zip",
    "T1.zip",
    "multi_class_masks.zip",
    "cd_dataset_train.txt",
    "cd_dataset_test.txt",
    "object_annotations_test_coco.json",
    "README.txt"
]

OPTIONAL_FILES = [
    "task_1_masks.zip",
    "task_2_masks.zip",
    "task_3_masks.zip",
    "README.md"
]

def check_local_dataset(target_dir: Path) -> dict:
    """Check if the dataset files or extracted directories already exist."""
    status = {
        "is_complete": False,
        "missing_files": [],
        "existing_files": [],
        "is_extracted": False
    }
    
    # Check extracted state
    t0_dir = target_dir / "T0"
    t1_dir = target_dir / "T1"
    masks_dir = target_dir / "masks"
    
    if t0_dir.exists() and t1_dir.exists() and masks_dir.exists():
        t0_count = len(list(t0_dir.glob("*.png")) + list(t0_dir.glob("*.jpg")))
        t1_count = len(list(t1_dir.glob("*.png")) + list(t1_dir.glob("*.jpg")))
        mask_count = len(list(masks_dir.glob("*.png")) + list(masks_dir.glob("*.jpg")))
        if t0_count > 0 and t1_count > 0 and mask_count > 0:
            status["is_extracted"] = True
            print(f"[SYNC] Found extracted dataset: {t0_count} T0 images, {t1_count} T1 images, {mask_count} masks.")
            status["is_complete"] = True
            return status

    # Check zip files
    for fname in REQUIRED_FILES:
        fpath = target_dir / "raw" / fname
        if fpath.exists() and fpath.stat().st_size > 0:
            status["existing_files"].append(fname)
        else:
            status["missing_files"].append(fname)
            
    if len(status["missing_files"]) == 0:
        status["is_complete"] = True
        
    return status

def download_dataset(repo_id: str = DATASET_ID, target_dir: str = DEFAULT_DATA_DIR, force: bool = False) -> bool:
    """Download dataset from Hugging Face Hub."""
    data_path = Path(target_dir).resolve()
    raw_dir = data_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"==================================================")
    print(f"WATERSCOPE DATASET SYNCHRONIZATION")
    print(f"Repository: {repo_id}")
    print(f"Target Directory: {data_path}")
    print(f"==================================================")
    
    status = check_local_dataset(data_path)
    if status["is_extracted"] and not force:
        print("[SYNC] Dataset is already downloaded and extracted locally. Skipping download.")
        return True
        
    if status["is_complete"] and not force:
        print("[SYNC] All required archive files exist in raw directory. Skipping download.")
        return True

    print(f"[SYNC] Files to download: {status['missing_files'] or REQUIRED_FILES}")
    
    try:
        api = HfApi()
        repo_files = api.list_repo_files(repo_id, repo_type="dataset")
        print(f"[SYNC] Connected to Hugging Face Hub successfully. Available files: {len(repo_files)}")
    except Exception as e:
        print(f"[SYNC ERROR] Failed to connect to Hugging Face Hub: {e}")
        return False

    downloaded = 0
    files_to_get = REQUIRED_FILES if force else status["missing_files"]
    
    for filename in files_to_get:
        if filename not in repo_files:
            print(f"[SYNC WARNING] '{filename}' not found in repo files list, checking if optional...")
            continue
            
        dest_file = raw_dir / filename
        if dest_file.exists() and not force:
            print(f"[SYNC] Already present: {filename}")
            continue
            
        print(f"[SYNC] Downloading '{filename}' from {repo_id}...")
        try:
            cached_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                repo_type="dataset",
                local_dir=str(raw_dir),
                local_dir_use_symlinks=False
            )
            print(f"[SYNC] Successfully downloaded '{filename}' ({os.path.getsize(cached_path) / (1024*1024):.2f} MB)")
            downloaded += 1
        except Exception as e:
            print(f"[SYNC ERROR] Error downloading {filename}: {e}")
            return False

    print(f"[SYNC] Dataset download completed: {downloaded} files downloaded.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download FPCD dataset from Hugging Face")
    parser.add_argument("--repo-id", default=DATASET_ID, help="Hugging Face Dataset ID")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Local dataset storage directory")
    parser.add_argument("--force", action="store_true", help="Force re-download even if files exist")
    args = parser.parse_args()
    
    success = download_dataset(args.repo_id, args.data_dir, args.force)
    sys.exit(0 if success else 1)
