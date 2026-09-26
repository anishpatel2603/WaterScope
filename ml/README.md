# 🛰️ WATERSCOPE: Bi-Temporal Watershed Change Detection ML Engine

An enterprise-grade, scientifically calibrated machine learning engine for automated watershed intervention verification, bi-temporal change detection, and environmental assessment across Maharashtra, India.

Designed to eliminate false positive intervention claims, prevent spatial data leakage, handle severe pixel class imbalance, and produce honest, calibrated evidence for watershed governance.

---

## 📑 Table of Contents
1. [Overview & Target Classes](#overview--target-classes)
2. [Installation & Environment Setup](#installation--environment-setup)
3. [Dataset Acquisition & Leakage Prevention](#dataset-acquisition--leakage-prevention)
4. [Training the Models](#training-the-models)
5. [Evaluation & Metric Verification](#evaluation--metric-verification)
6. [Running Inference (CLI & Programmatic)](#running-inference-cli--programmatic)
7. [Starting the ML API Service](#starting-the-ml-api-service)
8. [Connecting ML API to the Backend](#connecting-ml-api-to-the-backend)
9. [Error Analysis & Visual Diagnostics](#error-analysis--visual-diagnostics)
10. [Scientific Integrity & Non-Causal Framework](#scientific-integrity--non-causal-framework)

---

## 🎯 Overview & Target Classes

WATERSCOPE evaluates bi-temporal image pairs:
- **$T_0$ (Before Image)**: Geo-referenced orthophoto or field photo prior to intervention.
- **$T_1$ (After Image)**: Geo-referenced orthophoto or field photo subsequent to intervention.

### Supported Classes
| ID | Class Name | Description |
|:--:|:-----------|:------------|
| `0` | **Background / No Change** | Unchanged agricultural, fallow, or barren terrain |
| `1` | **Farm Pond Constructed** | Excavation and establishment of a new farm pond structure |
| `2` | **Farm Pond Demolished** | Backfilled or degraded farm pond basin |
| `3` | **Farm Pond Dried** | Seasonal evaporation or desiccation of water body |
| `4` | **Farm Pond Wetted** | Re-filling, rainwater capture, or water-table recharge |

---

## 💻 Installation & Environment Setup

### 1. Prerequisites
- Python 3.10+ (tested on Windows 11 and Ubuntu 22.04 LTS)
- CUDA-enabled GPU (optional; engine automatically falls back to multi-threaded CPU)

### 2. Setup Virtual Environment
```bash
# Clone or navigate to the repository
cd "c:\Users\anish\Desktop\2 no"

# Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install all required ML dependencies
pip install -r requirements.txt
```

---

## 📦 Dataset Acquisition & Leakage Prevention

### Primary Dataset: FPCD (`ctundia/FPCD`)
The engine integrates directly with Hugging Face's Farm Pond Change Detection (FPCD) dataset covering 694 bi-temporal pairs across Maharashtra (Akola, Amravati, Buldhana, Washim, etc.).

### Automatic Download & Verification
Run the reproducible data ingestion pipeline:
```bash
# 1. Programmatically download archives from Hugging Face
python scripts/download_dataset.py

# 2. Extract, match bi-temporal triplets, and construct spatial splits
python scripts/prepare_dataset.py

# 3. Verify integrity, image dimensions, and mask boundaries
python scripts/verify_dataset.py
```

### Zero Data Leakage Split Strategy
To ensure true geographic generalization, dataset partitioning is strictly location-grouped:
- **Train Split (434 pairs)**: 10 distinct villages (e.g., Amravati Takarkheda, Babhali, Dabhadi, etc.).
- **Validation Split (111 pairs)**: 5 distinct villages with 0% overlap with Train.
- **Test Split (148 pairs)**: 2 completely unseen talukas (Akola Ghusar and Akhatwada) strictly reserved for final benchmarks.

Inspect the complete split audit at [`data_split_report.json`](file:///c:/Users/anish/Desktop/2%20no/data_split_report.json).

---

## 🚀 Training the Models

All training pipelines automatically detect CUDA vs. CPU, enable mixed precision when GPU is present, apply paired augmentations, and save both best and final checkpoints.

### 1. Train the Best Attention Siamese Model (`waterscope_change_model_v3`)
Combines ResNet18 twin encoders, Spatial & Channel Difference Attention, Focal-Tversky loss ($\beta=0.7$), and minority oversampling:
```bash
python train.py --config configs/best.yaml
```

### 2. Train the Standard Siamese U-Net (`waterscope_change_model_v2`)
```bash
python train.py --config configs/fpcd_siamese.yaml --epochs 5 --batch-size 16
```

### 3. Train the Baseline CNN (`waterscope_change_model_v1`)
```bash
python train.py --config configs/fpcd_baseline.yaml --epochs 5 --batch-size 16
```

### Key Training Options:
- `--epochs <int>`: Override default epochs.
- `--batch-size <int>`: Override batch size (default: 16 on GPU, 8 on CPU).
- `--class-balanced`: Force `WeightedRandomSampler` to oversample rare change events.
- `--device <cpu|cuda>`: Explicitly select compute device.

Logs are saved to `experiments/<run_name>/training_history.csv`.

---

## 📊 Evaluation & Metric Verification

Test set evaluation is strictly isolated and never used for hyperparameter tuning.

Run comprehensive model comparison across all architectures:
```bash
python evaluate.py \
  --attention-ckpt checkpoints/best_model.pt \
  --siamese-ckpt models/fpcd_siamese_v1.pt \
  --baseline-ckpt models/fpcd_baseline_cnn.pt
```

### Evaluated Metrics:
- **Pixel Accuracy**: Overall percentage of correctly classified pixels.
- **Macro F1 Score**: Unweighted harmonic mean of precision and recall across all 5 classes.
- **Mean IoU (mIoU)**: Macro Intersection-over-Union across all classes.
- **Change mIoU**: Intersection-over-Union strictly computed over foreground change classes [1..4].
- **Confusion Matrix**: Full multi-class confusion grid.
- **Area MAE ($m^2$)**: Mean Absolute Error in physical intervention area estimation.

Results are automatically saved to [`experiments/model_comparison_report.json`](file:///c:/Users/anish/Desktop/2%20no/experiments/model_comparison_report.json).

---

## 🔮 Running Inference (CLI & Programmatic)

### 1. CLI Inference
Run bi-temporal prediction on arbitrary $T_0$ and $T_1$ pairs:
```bash
# Satellite mode with Attention Siamese model
python infer.py \
  --t0 data/fpcd/T0/Akola_Akhatwada_200703_0.jpg \
  --t1 data/fpcd/T1/Akola_Akhatwada_201803_0.jpg \
  --model-type attention_siamese \
  --mode satellite \
  --output result.json

# Field photo mode with handheld smartphone photo validation
python infer.py \
  --t0 uploads/before_field.jpg \
  --t1 uploads/after_field.jpg \
  --model-type attention_siamese \
  --mode field
```

### 2. Programmatic Python Usage
```python
from src.inference.pipeline import ChangeDetectionPipeline

# Initialize pipeline with calibrated weights
pipeline = ChangeDetectionPipeline(
    model_path="checkpoints/best_model.pt",
    model_type="attention_siamese",
    device="cpu"
)

# Run bi-temporal inference
result = pipeline.predict("path/to/t0.jpg", "path/to/t1.jpg", mode="satellite")

print(f"Predicted Class: {result['change_class_display']}")
print(f"Calibrated Confidence: {result['confidence']:.2%}")
print(f"Physical Area Changed: {result['changed_area_m2']} m²")
print(f"Requires Manual Review: {result['requires_review']}")
```

---

## 🌐 Starting the ML API Service

The ML Engine is served as a high-performance FastAPI microservice.

### Launch API:
```bash
# Start ML microservice on port 8000
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
`http://localhost:8000/docs`

---

## 🔗 Connecting ML API to the Backend

The ML microservice provides REST endpoints compliant with the watershed backend specification:

### Primary Endpoint: `POST /api/ml/change-detection`
Accepts multipart form-data or JSON payloads:

#### Request Parameters:
- `before_image` (file, required): $T_0$ before image.
- `after_image` (file, required): $T_1$ after image.
- `latitude` (float, optional): Geographic latitude for location tracking.
- `longitude` (float, optional): Geographic longitude for location tracking.
- `mode` (string, optional): `"satellite"` or `"field"` (default: `"satellite"`).

#### Response Schema:
```json
{
  "change_detected": true,
  "predicted_class": "farm_pond_constructed",
  "confidence": 0.892,
  "calibrated_confidence": 0.841,
  "change_percentage": 14.35,
  "quality_score": 0.965,
  "requires_review": false,
  "model_version": "waterscope_change_model_v3",
  "changed_area_m2": 420.5,
  "change_mask_url": "data:image/png;base64,...",
  "scientific_disclaimer": "Observed bi-temporal surface change detected by visual and spectral analysis. This indicates observable physical variance and does not establish sole legal or hydrological causation."
}
```

If image quality is degraded or confidence is below threshold ($<0.70$):
```json
{
  "change_detected": false,
  "predicted_class": "insufficient_visual_evidence",
  "confidence": 0.35,
  "calibrated_confidence": 0.28,
  "quality_score": 0.42,
  "requires_review": true,
  "model_version": "waterscope_change_model_v3"
}
```

---

## 🔍 Error Analysis & Visual Diagnostics

To systematically audit failure modes, generate the standalone interactive diagnostic report:
```bash
python error_analysis.py --data-dir data/fpcd --output-dir reports
```

This generates:
- **`reports/error_analysis.html`**: Interactive HTML dashboard with confusion matrices, per-village performance, and low-confidence prediction distributions.
- **`reports/error_samples/`**: Multi-panel visual diagnostic montages showing $T_0$, $T_1$, Ground Truth Mask, Predicted Mask, and Discrepancy Error Maps.
- **`reports/ablation_study.csv`**: Controlled empirical comparison validating the impact of augmentations, Focal-Tversky loss, and attention mechanisms.

---

## ⚖️ Scientific Integrity & Non-Causal Framework

Per remote sensing best practices and administrative GIS guidelines:
1. **No Artificial Accuracy Claims**: While background pixel accuracy reaches $>98\%$, the platform explicitly measures and optimizes for **Macro F1 (43.15%)** and **Change mIoU**.
2. **Non-Causal Classification**: Predictions represent **"Observed physical change evidence"**, not proof of government contractor completion or natural intervention causality.
3. **Low-Confidence Triaging**: Any prediction with calibrated confidence $<70\%$ or quality score $<0.65$ triggers `requires_review = True` for mandatory ground-truth field inspection.
