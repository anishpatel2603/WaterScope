"""
WATERSCOPE Backend - Complete API Test Suite
Validates all 19 required backend REST endpoints against active server.
"""

import io
import requests
import pytest
from PIL import Image
import numpy as np

BASE_URL = "http://127.0.0.1:8000"

def test_system_status():
    r = requests.get(f"{BASE_URL}/api/system/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "OPERATIONAL"
    assert data["backend_online"] is True
    assert data["active_interventions_count"] > 0

def test_watersheds():
    r = requests.get(f"{BASE_URL}/api/watersheds")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 0
    ws_id = data["items"][0]["id"]
    
    r_detail = requests.get(f"{BASE_URL}/api/watersheds/{ws_id}")
    assert r_detail.status_code == 200
    assert r_detail.json()["id"] == ws_id

def test_interventions_crud():
    # 1. List
    r = requests.get(f"{BASE_URL}/api/interventions?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 0
    first_id = data["items"][0]["id"]

    # 2. Detail
    r_get = requests.get(f"{BASE_URL}/api/interventions/{first_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == first_id

    # 3. Create
    payload = {
        "type": "farm_pond",
        "name": "Test Intervention #FP-TEST",
        "latitude": 20.705,
        "longitude": 77.012,
        "village": "Akhatwada",
        "district": "Akola",
        "state": "Maharashtra",
        "status": "active"
    }
    r_post = requests.post(f"{BASE_URL}/api/interventions", json=payload)
    assert r_post.status_code == 200
    created = r_post.json()
    assert created["name"] == "Test Intervention #FP-TEST"
    assert created["location_source"] == "GPS"

def test_image_upload_and_exif():
    # Create test JPEG in-memory
    arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("field_test.jpg", buf, "image/jpeg")}
    data = {"image_type": "BEFORE"}
    r = requests.post(f"{BASE_URL}/api/images/upload", files=files, data=data)
    assert r.status_code == 200
    res = r.json()
    assert "id" in res
    assert res["gps_status"] in ["GPS_AVAILABLE", "GPS_MISSING"]
    img_id = res["id"]

    # Retrieve
    r_get = requests.get(f"{BASE_URL}/api/images/{img_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == img_id

def test_satellite_scenes_and_search():
    # 1. List
    r = requests.get(f"{BASE_URL}/api/satellite/scenes")
    assert r.status_code == 200

    # 2. Search
    payload = {
        "latitude": 20.7002,
        "longitude": 77.0082,
        "window_days": 15,
        "max_cloud_cover": 20.0,
        "provider": "demo"
    }
    r_search = requests.post(f"{BASE_URL}/api/satellite/search", json=payload)
    assert r_search.status_code == 200
    data = r_search.json()
    assert data["count"] > 0
    assert "scene_id" in data["scenes"][0]

    # 3. Compare
    s0 = data["scenes"][0]["scene_id"]
    s1 = data["scenes"][1]["scene_id"] if len(data["scenes"]) > 1 else s0
    r_comp = requests.post(f"{BASE_URL}/api/satellite/compare", json={
        "before_scene_id": s0,
        "after_scene_id": s1,
        "latitude": 20.7002,
        "longitude": 77.0082,
        "buffer_distance_meters": 500
    })
    assert r_comp.status_code == 200
    assert r_comp.json()["status"] == "COMPLETED"

def test_bi_temporal_analysis_workflow():
    payload = {
        "mode": "satellite",
        "buffer_distances": [100, 250, 500, 1000]
    }
    r = requests.post(f"{BASE_URL}/api/analysis/create", json=payload)
    assert r.status_code == 200
    job = r.json()
    job_id = job["id"]
    assert job["status"] == "COMPLETED"
    assert "ml_prediction" in job
    assert "spatial_metrics" in job
    assert len(job["spatial_metrics"]) == 4 # 100, 250, 500, 1000m
    assert "observed_impact" in job
    assert job["observed_impact"]["verdict_type"] == "OBSERVED_CHANGE"

    # Get analysis
    r_get = requests.get(f"{BASE_URL}/api/analysis/{job_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == job_id

    # Get ML specific analysis
    r_ml = requests.get(f"{BASE_URL}/api/ml/analysis/{job_id}")
    assert r_ml.status_code == 200
    assert "change_class" in r_ml.json()

    # Get metrics
    r_met = requests.get(f"{BASE_URL}/api/metrics/{job_id}")
    assert r_met.status_code == 200
    assert r_met.json()["buffers_evaluated"] == 4

    # Get change mask
    r_mask = requests.get(f"{BASE_URL}/api/change-mask/{job_id}")
    assert r_mask.status_code == 200
    assert "mask_endpoint" in r_mask.json()

    # Generate Report
    r_rep = requests.post(f"{BASE_URL}/api/reports/generate", json={
        "analysis_job_id": job_id,
        "title": "Automated Test Verification Report"
    })
    assert r_rep.status_code == 200
    assert r_rep.json()["status"] == "ready"

def test_priority_zones_and_data_sources():
    # Priority zones
    r_pz = requests.get(f"{BASE_URL}/api/priority-zones")
    assert r_pz.status_code == 200
    assert "priority_zones" in r_pz.json()

    # Data sources
    r_ds = requests.get(f"{BASE_URL}/api/data-sources")
    assert r_ds.status_code == 200
    data = r_ds.json()
    assert data["total"] >= 4
    source_names = [s["name"] for s in data["sources"]]
    assert any("Sentinel-2" in s for s in source_names)
    assert any("FPCD" in s for s in source_names)
