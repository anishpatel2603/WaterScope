"""
WATERSCOPE Full System Verification Test Suite
Tests every backend endpoint, ML pipeline, GIS raster engine, and frontend asset delivery.
"""

import urllib.request
import json
import base64
import sys

BASE_URL = "http://127.0.0.1:8000"

def get(endpoint: str) -> dict:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Failed GET {endpoint}: status {resp.status}"
        return json.loads(resp.read().decode("utf-8"))

def post_json(endpoint: str, data: dict) -> dict:
    url = f"{BASE_URL}{endpoint}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Failed POST {endpoint}: status {resp.status}"
        return json.loads(resp.read().decode("utf-8"))

def test_full_system():
    print("=" * 60)
    print("WATERSCOPE FULL PLATFORM VERIFICATION")
    print("=" * 60)

    # 1. System status
    status = get("/api/system/status")
    print(f"1. [OK] System Status: {status['status']}, Active Interventions: {status['active_interventions_count']}")
    assert status["backend_online"] is True
    assert status["active_interventions_count"] >= 60

    # 2. Watersheds
    ws = get("/api/watersheds")
    print(f"2. [OK] Watersheds: {ws['total']} basin management units found")
    assert ws["total"] >= 1

    # 3. Interventions
    interventions = get("/api/interventions?limit=5")
    print(f"3. [OK] Interventions: {interventions['total']} total registered")
    assert interventions["total"] >= 60
    sample_id = interventions["items"][0]["id"]

    # 4. Presets
    presets = get("/api/presets")
    print(f"4. [OK] Presets: {len(presets['presets'])} benchmark pairs ready")
    assert len(presets["presets"]) >= 4
    preset = presets["presets"][0]

    # 5. Raw Preset Image retrieval
    t0_url = f"{BASE_URL}{preset['t0_url']}"
    with urllib.request.urlopen(t0_url) as r:
        t0_bytes = r.read()
        print(f"5. [OK] Preset T0 Image retrieved: {len(t0_bytes)} bytes")
        assert len(t0_bytes) > 5000

    # 6. Priority Zones
    zones = get("/api/priority-zones")
    print(f"6. [OK] Priority Zones: {zones['count']} degradation/maintenance alerts flagged")

    # 7. Data Sources
    sources = get("/api/data-sources")
    print(f"7. [OK] Data Sources: {sources['total']} providers & datasets cataloged")

    # 8. ML Health & Model
    ml_health = get("/ml/health")
    print(f"8. [OK] ML Engine Health: {ml_health['status']}, Model: {ml_health['model_name']}")
    assert ml_health["ml_online"] is True

    # 9. ML Predict
    t0_b64 = base64.b64encode(t0_bytes).decode("utf-8")
    with urllib.request.urlopen(f"{BASE_URL}{preset['t1_url']}") as r:
        t1_bytes = r.read()
    t1_b64 = base64.b64encode(t1_bytes).decode("utf-8")

    pred = post_json("/ml/predict", {
        "image_t0_base64": t0_b64,
        "image_t1_base64": t1_b64,
        "mode": "satellite"
    })
    print(f"9. [OK] ML Siamese Prediction: class={pred['change_class']}, confidence={pred['confidence']:.3f}, footprint={pred.get('changed_area_m2')} m2")
    assert "change_class" in pred

    # 10. GIS Full Bi-Temporal Analysis
    job = post_json("/api/analysis/create", {
        "intervention_id": sample_id,
        "mode": "satellite",
        "buffer_distances": [100, 250, 500, 1000]
    })
    print(f"10. [OK] GIS Analysis Job Created: id={job['id']}, status={job['status']}")
    assert job["status"] == "COMPLETED"
    assert len(job["spatial_metrics"]) == 4
    assert "observed_impact" in job

    # 11. Report Generation
    rep = post_json("/api/reports/generate", {
        "analysis_job_id": job["id"],
        "title": "Institutional Verification Audit Certificate"
    })
    print(f"11. [OK] Audit Report Generated: id={rep['report_id']}, verdict={rep['verdict']}, score={rep['composite_score']}")

    # 12. Frontend SPA & Asset serving
    with urllib.request.urlopen(f"{BASE_URL}/") as r:
        assert r.status == 200
        html = r.read().decode("utf-8")
        assert "WATERSCOPE" in html
    print("12. [OK] Frontend SPA HTML successfully delivered at /")

    with urllib.request.urlopen(f"{BASE_URL}/interventions/{sample_id}") as r:
        assert r.status == 200
        assert "WATERSCOPE" in r.read().decode("utf-8")
    print(f"13. [OK] Deep SPA client route successfully delivered at /interventions/{sample_id}")

    print("=" * 60)
    print("ALL 13 SYSTEM INTEGRATION TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_system()
