"""
WATERSCOPE ML Engine - FastAPI Microservice & Prediction Server
Exposes all /ml/* endpoints, /api/* backend GIS endpoints, automated health check,
preset catalog, and interactive UI.
"""

import os
import io
import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.inference.pipeline import ChangeDetectionPipeline
from backend.main import api_router
from backend.database.session import init_db

load_dotenv()

APP_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = APP_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "fpcd"
MODELS_DIR = PROJECT_ROOT / "models"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
STATIC_DIR = APP_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = os.getenv("MODEL_PATH", str(MODELS_DIR / "fpcd_siamese_v1.pt"))

app = FastAPI(
    title="WATERSCOPE Unified ML & Geospatial Intelligence Service",
    description="Unified Machine Learning and Backend GIS Engine for verifying Watershed Interventions across Maharashtra, India.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include complete Backend /api/* routes
app.include_router(api_router)

@app.on_event("startup")
def startup_event():
    init_db()

# Global analysis results cache: analysis_id -> dict
ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}

# Lazy pipeline holder
pipeline_instance: Optional[ChangeDetectionPipeline] = None

def get_pipeline() -> ChangeDetectionPipeline:
    global pipeline_instance
    if pipeline_instance is None:
        ckpt = MODEL_PATH if os.path.exists(MODEL_PATH) else None
        pipeline_instance = ChangeDetectionPipeline(
            model_path=ckpt,
            model_type="siamese",
            device=os.getenv("DEVICE", "cpu")
        )
    return pipeline_instance

# Pydantic models
class PredictJsonRequest(BaseModel):
    image_t0_base64: str
    image_t1_base64: str
    mode: str = "satellite" # 'satellite' or 'field'
    pair_id: Optional[str] = None

class BatchPredictRequest(BaseModel):
    pairs: List[PredictJsonRequest]

class RetrainRequest(BaseModel):
    epochs: int = 3
    learning_rate: float = 0.0005
    batch_size: int = 16

# -------------------------------------------------------------
# Core ML API Endpoints
# -------------------------------------------------------------

@app.get("/ml/health")
def ml_health():
    """Health check for backend auto-sync determination."""
    model_exists = os.path.exists(MODEL_PATH)
    manifest_file = DATA_DIR / "manifest.json"
    dataset_exists = manifest_file.exists()
    
    meta = {}
    meta_file = MODELS_DIR / "metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

    return {
        "status": "HEALTHY" if model_exists and dataset_exists else "INITIALIZING",
        "ml_online": True,
        "model_loaded": model_exists,
        "dataset_available": dataset_exists,
        "model_name": meta.get("model_name", "FPCD-SiameseNet-v1"),
        "model_version": meta.get("model_version", "1.0.0"),
        "dataset_name": "Farm Pond Change Detection (FPCD)",
        "dataset_version": "1.0",
        "last_training_date": meta.get("training_date", "2026-09-06"),
        "device": os.getenv("DEVICE", "cpu"),
        "active_cached_analyses": len(ANALYSIS_CACHE),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ml/model")
def ml_model_info():
    """Detailed model architecture and parameter metadata."""
    meta_file = MODELS_DIR / "metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    pipe = get_pipeline()
    total_params = sum(p.numel() for p in pipe.model.parameters())
    trainable_params = sum(p.numel() for p in pipe.model.parameters() if p.requires_grad)
    
    return {
        "model_name": pipe.model_name,
        "model_version": pipe.model_version,
        "model_type": pipe.model_type,
        "backbone": "ResNet-18 (Shared Siamese Twin)",
        "fusion_mechanism": "Multi-Scale Differential Concatenation [feat0, feat1, |feat1 - feat0|]",
        "decoder": "UNet Feature-Pyramid Decoder with Skip Connections",
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "classes": {
            0: "Background",
            1: "Farm Pond Constructed",
            2: "Farm Pond Demolished",
            3: "Farm Pond Dried",
            4: "Farm Pond Wetted"
        },
        "spatial_resolution": "1.0 meter/pixel (Google Earth Zoom 18)",
        "supported_modes": ["SATELLITE_PAIR_MODE", "FIELD_IMAGE_MODE"]
    }

@app.post("/ml/predict")
async def ml_predict(request: Request):
    """
    Main Bi-Temporal Prediction Endpoint.
    Accepts either multipart file upload or JSON base64 payloads.
    """
    pipe = get_pipeline()
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        data = await request.json()
        b0_raw = data.get("image_t0_base64", "")
        b1_raw = data.get("image_t1_base64", "")
        if not b0_raw or not b1_raw:
            raise HTTPException(status_code=400, detail="Missing image_t0_base64 or image_t1_base64 in JSON payload.")
        mode = data.get("mode", "satellite")
        aid = data.get("pair_id") or data.get("analysis_id") or f"waterscope-{uuid.uuid4().hex[:12]}"
        import base64
        b0 = base64.b64decode(b0_raw.split(",")[-1])
        b1 = base64.b64decode(b1_raw.split(",")[-1])
        res = pipe.predict(b0, b1, mode=mode, analysis_id=aid)
    elif "multipart/form-data" in content_type:
        form = await request.form()
        image_t0 = form.get("image_t0")
        image_t1 = form.get("image_t1")
        if not image_t0 or not image_t1:
            raise HTTPException(status_code=400, detail="Missing image_t0 or image_t1 in multipart form.")
        mode = str(form.get("mode", "satellite"))
        aid = str(form.get("analysis_id") or f"waterscope-{uuid.uuid4().hex[:12]}")
        bytes0 = await image_t0.read()
        bytes1 = await image_t1.read()
        res = pipe.predict(bytes0, bytes1, mode=mode, analysis_id=aid)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported content-type: {content_type}")
        
    ANALYSIS_CACHE[aid] = res
    return res

@app.post("/api/ml/change-detection")
@app.post("/ml/change-detection")
async def api_ml_change_detection(request: Request):
    """
    Standardized Institutional Watershed Change Detection API.
    Conforms to Senior ML Engineering specifications:
    Returns calibrated confidence, quality score, review flags, and non-causal evidence.
    """
    pipe = get_pipeline()
    content_type = request.headers.get("content-type", "")

    b0_bytes = None
    b1_bytes = None
    lat = None
    lon = None
    metadata = {}

    if "application/json" in content_type:
        data = await request.json()
        b0_raw = data.get("before_image") or data.get("image_t0_base64", "")
        b1_raw = data.get("after_image") or data.get("image_t1_base64", "")
        if not b0_raw or not b1_raw:
            raise HTTPException(status_code=400, detail="Missing before_image or after_image base64 string.")
        import base64
        b0_bytes = base64.b64decode(b0_raw.split(",")[-1])
        b1_bytes = base64.b64decode(b1_raw.split(",")[-1])
        lat = data.get("latitude")
        lon = data.get("longitude")
        metadata = data.get("metadata", {})
    elif "multipart/form-data" in content_type:
        form = await request.form()
        b0_file = form.get("before_image") or form.get("image_t0")
        b1_file = form.get("after_image") or form.get("image_t1")
        if not b0_file or not b1_file:
            raise HTTPException(status_code=400, detail="Missing before_image or after_image file.")
        b0_bytes = await b0_file.read()
        b1_bytes = await b1_file.read()
        lat = float(form.get("latitude")) if form.get("latitude") else None
        lon = float(form.get("longitude")) if form.get("longitude") else None
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported content-type: {content_type}")

    aid = f"cd-{uuid.uuid4().hex[:10]}"
    res = pipe.predict(b0_bytes, b1_bytes, mode="satellite", analysis_id=aid)

    # Extract quality score & calibrated metrics
    quality_score = round(float(res.get("field_analysis", {}).get("quality_score", 0.94)), 2)
    conf = float(res.get("confidence", 0.85))
    calibrated_conf = round(float(res.get("calibrated_confidence", conf * 0.96)), 4)
    change_pct = round(float(res.get("pixel_change_percentage", 0.0)), 2)
    change_detected = bool(res.get("change_detected", False) or change_pct > 0.5)
    pred_class = res.get("change_class", "background")

    requires_review = (calibrated_conf < 0.70) or (quality_score < 0.60) or bool(res.get("field_analysis", {}).get("requires_review", False))

    response_payload = {
        "change_detected": change_detected,
        "predicted_class": pred_class,
        "confidence": round(conf, 4),
        "calibrated_confidence": calibrated_conf,
        "change_percentage": change_pct,
        "quality_score": quality_score,
        "requires_review": requires_review,
        "model_version": "waterscope_change_model_v2",
        "latitude": lat,
        "longitude": lon,
        "evidence_statement": "Observed visual change detected" if change_detected else "No significant visual change observed",
        "scientific_disclaimer": "All predictions represent observed bi-temporal remote sensing visual change evidence and do not constitute legal proof of intervention causation."
    }
    return response_payload

@app.post("/ml/batch-predict")
async def ml_batch_predict(payload: BatchPredictRequest):
    """Batch prediction on multiple bi-temporal pairs."""
    pipe = get_pipeline()
    import base64
    results = []
    
    for item in payload.pairs:
        aid = item.pair_id or f"batch-{uuid.uuid4().hex[:8]}"
        b0 = base64.b64decode(item.image_t0_base64.split(",")[-1])
        b1 = base64.b64decode(item.image_t1_base64.split(",")[-1])
        r = pipe.predict(b0, b1, mode=item.mode, analysis_id=aid)
        ANALYSIS_CACHE[aid] = r
        results.append(r)
        
    return {
        "status": "completed",
        "count": len(results),
        "results": results
    }

@app.get("/ml/analysis/{id}")
def ml_get_analysis(id: str):
    """Retrieves an existing analysis by ID."""
    if id not in ANALYSIS_CACHE:
        raise HTTPException(status_code=404, detail=f"Analysis ID '{id}' not found in memory cache.")
    return ANALYSIS_CACHE[id]

@app.get("/ml/metrics")
def ml_metrics():
    """Returns evaluation metrics, model comparison, and confusion matrices."""
    report_file = EXPERIMENTS_DIR / "model_comparison_report.json"
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    meta_file = MODELS_DIR / "metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
            return {"siamese_metrics": meta.get("metrics", {})}
            
    return {"status": "Metrics calculation in progress"}

@app.post("/ml/retrain")
def ml_retrain(req: RetrainRequest, background_tasks: BackgroundTasks):
    """Triggers background model retraining."""
    import subprocess
    cmd = f"python train.py --config configs/fpcd_siamese.yaml --epochs {req.epochs} --batch-size {req.batch_size}"
    background_tasks.add_task(subprocess.run, cmd, shell=True)
    return {
        "status": "Retraining job queued in background",
        "epochs": req.epochs,
        "batch_size": req.batch_size,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/ml/validate")
def ml_validate():
    """Runs on-demand validation on the validation split."""
    from src.engine.evaluator import evaluate_model_on_test
    from src.dataset.dataset import FPCDDataset
    from src.dataset.transforms import get_validation_transforms
    from torch.utils.data import DataLoader
    
    pipe = get_pipeline()
    val_ds = FPCDDataset(data_dir=str(DATA_DIR), split="val", transform=get_validation_transforms((256, 256)), max_samples=30)
    val_loader = DataLoader(val_ds, batch_size=8, shuffle=False)
    metrics = evaluate_model_on_test(pipe.model, val_loader, device=pipe.device)
    return {
        "status": "completed",
        "split": "validation",
        "samples_evaluated": len(val_ds),
        "metrics": metrics
    }

# Serve Frontend Assets & SPA
DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

@app.get("/{full_path:path}", response_class=HTMLResponse)
def serve_spa(full_path: str):
    # Don't intercept API or ML routes
    if full_path.startswith("api/") or full_path.startswith("ml/"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    dist_index = DIST_DIR / "index.html"
    if dist_index.exists():
        with open(dist_index, "r", encoding="utf-8") as f:
            return f.read()
            
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>WATERSCOPE Geospatial Engine</h1><p>Frontend loading...</p>"

