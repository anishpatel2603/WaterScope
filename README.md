# WATERSCOPE: Bi-Temporal Change Detection ML Engine for Watershed Interventions

An enterprise-grade, scientifically rigorous machine learning engine for the **WATERSCOPE** project. It automatically determines whether a watershed intervention (starting with the Farm Pond Change Detection prototype across Maharashtra, India) has undergone observable bi-temporal change between BEFORE ($T_0$) and AFTER ($T_1$) imagery.

---

## 🌊 Project Objectives

When field personnel capture a geo-tagged photograph BEFORE an intervention, and subsequently capture another AFTER implementation, WATERSCOPE answers:
1. **Did the intervention appear?** (Farm Pond Constructed)
2. **Did it disappear?** (Farm Pond Demolished)
3. **Did its physical state change?** (Farm Pond Dried / Wetted)
4. **Did surface water presence change?** (NDWI & water pixel extent quantification)
5. **What physical area changed?** (Computed in square meters $m^2$ via ground sampling distance)
6. **How confident is the model?** (Calibrated probability derived strictly over the change region)

---

## 📦 Primary Training Dataset (FPCD)

- **Dataset Identifier**: [`ctundia/FPCD`](https://huggingface.co/datasets/ctundia/FPCD)
- **Geographic Coverage**: Maharashtra, India (Akola, Amravati, Washim, Buldhana, etc.)
- **Resolution**: High-resolution orthophotos at Zoom Level 18 (~1.0 meter/pixel ground sampling distance)
- **Temporal Range**: 2007–2021 (Minimum 2 years, Maximum 9 years interval)
- **Classes**:
  - `0`: Background (No Change)
  - `1`: Farm Pond Constructed
  - `2`: Farm Pond Demolished
  - `3`: Farm Pond Dried
  - `4`: Farm Pond Wetted

---

## 🔄 Automatic Dataset Synchronization & Verification

The engine automatically synchronizes, extracts, verifies, and splits the dataset without manual intervention:

```bash
# 1. Download archives idempotently from Hugging Face
python scripts/download_dataset.py

# 2. Extract, match bi-temporal triplets, and create geographic-aware splits
python scripts/prepare_dataset.py

# 3. Perform deep integrity and validation checks
python scripts/verify_dataset.py
```

### Dataset Structure
```
data/
└── fpcd/
    ├── T0/             # 694 Before imagery files (e.g. Akola_Akhatwada_200703_0.jpg)
    ├── T1/             # 693 After imagery files (e.g. Akola_Akhatwada_201803_0.jpg)
    ├── masks/          # Multi-class indexed masks [0..4] (e.g. Akola_Akhatwada_0.png)
    ├── annotations/    # COCO format annotations and README
    ├── train.txt       # 434 train pairs (grouped by village to prevent spatial leakage)
    ├── val.txt         # 111 validation pairs
    ├── test.txt        # 148 test pairs
    └── manifest.json   # Full dataset metadata, class frequencies, and weights
```

---

## 🧠 Model Architectures

### 1. Siamese Bi-Temporal Network (`SiameseChangeNet`)
- **Twin Encoder**: Shared-weight ResNet-18 extracting multi-scale feature pyramids from $T_0$ and $T_1$.
- **Multi-Scale Fusion**: At each stage, computes differential features:
  $$F_{\text{diff}} = |f_{T_1} - f_{T_0}|$$
  $$F_{\text{cat}} = [f_{T_0}, f_{T_1}, F_{\text{diff}}]$$
  $$F_{\text{fused}} = \text{Conv}_{1\times1}(F_{\text{cat}}) + F_{\text{diff}}$$
- **Decoder**: Feature-pyramid UNet decoder with skip connections from fused features.
- **Dual Heads**:
  1. Pixel-level Segmentation Head ($5$ classes).
  2. Bottleneck Classification Head for dominant change class.

### 2. Baseline Model (`BaselineChangeNet`)
- Concatenates $T_0$, $T_1$, and pixel difference $|T_1 - T_0|$ directly into 9 channels, passed through a standard CNN encoder-decoder.

---

## 📊 Training, Validation, Evaluation & Inference CLI

```bash
# 1. Train Best Attention Siamese Model (with Focal-Tversky & Balanced Sampler)
python train.py --config configs/best.yaml

# 2. Train Standard Siamese Model
python train.py --config configs/fpcd_siamese.yaml --epochs 5 --batch-size 16

# 3. Train Baseline Model for Comparison
python train.py --config configs/fpcd_baseline.yaml --epochs 5 --batch-size 16

# 4. Comprehensive Test Set Evaluation across all model tiers
python evaluate.py --attention-ckpt checkpoints/best_model.pt --siamese-ckpt models/fpcd_siamese_v1.pt --baseline-ckpt models/fpcd_baseline_cnn.pt

# 5. Automated Error Analysis & Visual Diagnostics
python error_analysis.py --data-dir data/fpcd --output-dir reports

# 6. Bi-Temporal Prediction CLI
python infer.py --t0 data/fpcd/T0/sample.jpg --t1 data/fpcd/T1/sample.jpg --model-type attention_siamese --mode satellite
```

---

## 🛰️ Multi-Mode Inference & Hybrid Environmental Analysis

### Modes Supported
1. **`SATELLITE_PAIR_MODE`**:
   - Calculates NDVI (Biomass/Vegetation) and NDWI (Water Index) across Sentinel-2 / optical bands.
   - Measures surface water extent delta ($\Delta m^2$) and vegetative canopy response.
2. **`FIELD_IMAGE_MODE`**:
   - Analyzes handheld smartphone field photos.
   - Evaluates blur (Laplacian variance), exposure abnormalities, and perspective horizon tilt.
   - Returns `INSUFFICIENT_MODEL_CONFIDENCE` with diagnostic guidance rather than forcing a false classification.

### 📊 Site-Specific Observed Impact Scoring Engine (v2.0)
Calculates deterministic, scientifically calibrated composite indices for watershed interventions from actual site telemetry:
$$\text{Composite Index} = 0.35 \times \text{ML Change} + 0.30 \times \text{Water Retention} + 0.20 \times \text{Vegetation} + 0.15 \times \text{Data Quality}$$

Key Properties:
- **Zero Global Constants**: Every site computes its own distinct score based on physical water extent delta ($m^2$), NDVI canopy shift, ResNet-18 Siamese attention change detection, and sensor ground sampling distance.
- **REST Endpoints**:
  - `GET /api/interventions/{id}/score`: Returns site-specific score object conforming to v2.0 schema.
  - `GET /api/sites/{id}/score`: Site score alias.
- **Scientific Non-Causal Verdicts**:
  - `OBSERVED IMPROVEMENT` (Composite $\ge 75$ with positive hydrological telemetry)
  - `MODERATE OBSERVED CHANGE` (Composite $50 - 74$)
  - `NO SIGNIFICANT OBSERVED CHANGE` (Composite $< 50$ with stable baseline)
  - `OBSERVED DEGRADATION` (Negative water/canopy delta or structural desiccation)
  - `INSUFFICIENT EVIDENCE` (Low sensor quality $<45\%$, missing GPS, or obscured optical scenes)

> [!NOTE]
> **Scientific Limitation**: The metric certifies observed bi-temporal surface variation between baseline and verification imagery. Remote sensing analysis verifies physical presence and localized moisture dynamics; it does not establish sole legal contractor causation.

---

## 🚀 FastAPI ML Microservice

Start the service:
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/ml/health` | Backend auto-sync health check (online status, model version, dataset state) |
| `GET` | `/ml/model` | Model parameters, architecture, class mapping, and training metadata |
| `POST` | `/ml/predict` | Bi-temporal prediction (multipart file upload or base64 JSON) |
| `POST` | `/ml/batch-predict` | Batch prediction for multiple pairs |
| `GET` | `/ml/analysis/{id}` | Retrieve cached prediction results by analysis ID |
| `GET` | `/ml/metrics` | Model performance, confusion matrix, and class IoU benchmarks |
| `POST` | `/ml/retrain` | Background model fine-tuning and retraining |
| `POST` | `/ml/validate` | On-demand validation run on current model |
| `GET` | `/` or `/demo` | Interactive Watershed Intervention Demonstration Dashboard |

---

## 💻 Interactive Demonstration Dashboard

Access `http://localhost:8000/demo` in your browser:
1. Select a verified Maharashtra case study (e.g. **Farm Pond #FP-001** Akola, **#FP-042** Amravati, or **#FP-108** Washim).
2. Inspect Before ($T_0$) and After ($T_1$) orthophotos.
3. Click **Run AI Bi-Temporal Analysis**.
4. Explore the pixel change mask with the **interactive opacity slider**.
5. Review changed area ($m^2$), calibrated confidence, NDVI/NDWI spectral indicators, and hybrid verdict.
6. Click **Audit Report** to view or print an official intervention verification certificate.
