"""
WATERSCOPE Backend - Background Dataset Sync Job
"""
from scripts.sync_datasets import sync_and_seed_dataset

def run_sync_job():
    return sync_and_seed_dataset()

if __name__ == "__main__":
    run_sync_job()
