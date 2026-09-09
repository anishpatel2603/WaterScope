# WATERSCOPE ML Engine - Comprehensive Model & Data Audit
**Document Version:** 1.0.0  
**Audit Date:** 2026-09-09  
**Role:** Senior Computer Vision & Remote Sensing ML Engineer  
**System:** Institutional Watershed Intervention Verification Platform (Maharashtra, India)

---

## 1. Executive Summary

The WATERSCOPE ML Engine is designed to detect and classify bi-temporal watershed interventions (farm pond construction, demolition, drying, wetting, check dams, contour bunds, and vegetation/erosion dynamics) from high-resolution satellite orthophotos and field photography.

This audit evaluates the existing codebase, model architectures, dataset loaders, loss functions, metrics, and splitting methodology. While the existing project has an established Siamese CNN architecture with paired Albumentations and zero-leakage geographic splitting, **the current models suffer from severe minority class collapse (0.0% IoU on Demolished, Dried, and Wetted ponds)** due to extreme pixel imbalance (up to 8,690:1) and inadequate loss weighting. Pixel accuracy (98.99%) is dangerously misleading because background pixels account for 99.31% of the dataset.

---

## 2. Current Architecture Inventory

| Component | Baseline (`BaselineChangeNet`) | Siamese Twin (`SiameseChangeNet`) |
| :--- | :--- | :--- |
| **Input Channels** | 9 channels: Concatenation $[T_0, T_1, \|T_1 - T_0\|]$ | Dual 3-channel Siamese streams: $T_0$ and $T_1$ |
| **Encoder Backbone** | Single ResNet-18 (modified conv1 for 9 channels) | Shared-weight Siamese ResNet-18 twin |
| **Temporal Fusion** | Early pixel concatenation at input | Multi-scale feature difference: $[F_0, F_1, \|F_1 - F_0\|]$ with residual difference boost at all 5 pyramid stages |
| **Decoder** | 4-stage UNet ConvTranspose2d decoder | 4-stage FPN/UNet decoder with fused multi-scale skip connections |
| **Dual Heads** | Pixel segmentation logits + Global pooling classification | Pixel segmentation logits (5 classes) + Global average pooled classifier head (128-d bottleneck, dropout 0.3) |
| **Parameters** | 14.33 Million parameters | 18.57 Million parameters |
| **Compute Device** | CPU (Intel/AMD x86_64, CUDA unavailable on current host) | CPU |

---

## 3. Dataset Audit: Farm Pond Change Detection (FPCD)

* **Source:** HuggingFace `ctundia/FPCD` (Curated for Maharashtra, India)
* **Image Specifications:** 1024 × 768 native resolution, rescaled to 256 × 256 for training, 1.0 meter/pixel Ground Sample Distance (GSD), Google Earth Zoom 18.
* **Total Image Triplets:** 693 matched triplets ($T_0$ Before, $T_1$ After, Multi-class Change Mask).
* **Temporal Range:** 2007 to 2021 (Intervals from 2 to 9 years across post-monsoon and pre-monsoon seasons).

### Class Pixel Distribution

| Class ID | Class Label | Total Pixel Count | Global Frequency | Imbalance Ratio vs Background |
| :---: | :--- | :---: | :---: | :---: |
| **0** | Background (No Change) | 541,244,010 | **99.311%** | 1.0 : 1 |
| **1** | Farm Pond Constructed | 2,635,793 | **0.484%** | 205 : 1 |
| **2** | Farm Pond Demolished | 222,639 | **0.041%** | **2,431 : 1** |
| **3** | Farm Pond Dried | 290,320 | **0.053%** | **1,864 : 1** |
| **4** | Farm Pond Wetted | 604,614 | **0.111%** | **895 : 1** |

> [!CAUTION]
> Background pixels comprise **99.31%** of the entire dataset. Any naive model that predicts Class 0 everywhere immediately achieves **99.31% pixel accuracy** while having **zero utility** for watershed monitoring.

---

## 4. Train / Validation / Test Splitting Strategy & Data Leakage Audit

### Audit Finding: Zero Geographic Leakage Verified
The existing split in `scripts/prepare_dataset.py` groups image triplets by geographic village cluster `(District, Village)`:

* **Training Set:** 434 triplets across **10 completely distinct villages**:
  `Osmanabad_Ambejawalga`, `Amravati_Nardoda`, `Beed_Kumbhephal`, `Jalgaon_PimpalgaonBk`, `Aurangabad_Kumbhephal`, `Hingoli_Gondala`, `Latur_Sumthana`, `Parbhani_KinholaBk`, `Yavatmal_WadhonaPilki`, `Nanded_Chainpur`.
* **Validation Set:** 111 triplets across **5 completely distinct villages**:
  `Washim_BHOYATA`, `Wardha_KAKKADARA`, `Buldhana_Bhimgaon Kh`, `Jalna_Bhatkheda`, `Nasik_HadapSawargaon`.
* **Test Set:** 148 triplets across **2 completely distinct villages** (strictly held out):
  `Akola_Ghusar`, `Akola_Akhatwada`.

```
Pair Overlap Audit:
- Leakage between Train & Validation: 0 pairs (DISJOINT)
- Leakage between Train & Test:       0 pairs (DISJOINT)
- Leakage between Validation & Test:  0 pairs (DISJOINT)
```

### Severe Challenge Identified: Geographic Class Imbalance
Because certain types of agricultural interventions (such as pond dry-outs and demolitions) cluster in specific drought-prone or canal-irrigated talukas, holding out whole villages concentrates rare classes unevenly:
* **Train split dominant classes:** Class 0: 279, Class 1: 143, Class 2: 7, Class 3: 4, Class 4: 1.
* **Test split dominant classes:** Class 1: 71, Class 0: 53, Class 3: 13, Class 2: 8, Class 4: 3.
* **Consequence:** In standard batch training without oversampling, the network encounters a "Demolished" pair once every ~62 batches, and a "Wetted" pair once every 434 batches!

---

## 5. Preprocessing & Augmentation Audit

1. **Paired Transformations:**
   - Albumentations `Compose` pipeline uses `additional_targets={'image1': 'image'}`.
   - Spatial geometric transforms (HorizontalFlip, VerticalFlip, RandomRotate90, Affine rotation/scale) are strictly synchronized across $T_0$, $T_1$, and the ground-truth mask.
   - **Integrity Assessment:** PASS. No artificial change artifacts are introduced by independent geometric warping.
2. **Photometric Variations:**
   - Mild brightness and contrast jitter ($\pm 15\%$) is applied.
3. **Weaknesses:**
   - No multi-scale crop or cutmix for rare classes.
   - No explicit seasonal normalization (handling summer dry soil reflectance vs winter crop reflectance).

---

## 6. Loss Function, Optimizer & Metrics Audit

### Current Loss Function (`src/models/loss.py`):
```python
total_loss = 0.5 * WeightedCrossEntropy + 0.5 * MultiClassDiceLoss + 0.2 * AuxClassification
```
* **Class weights currently used:** `[0.2, 1.5, 2.0, 2.0, 1.8]`.
* **Defect:** A weight ratio of $2.0 / 0.2 = 10\times$ is mathematically powerless against an empirical imbalance ratio of $2,431\times$.
* **Dice Defect:** `MultiClassDiceLoss` calculates mean Dice over all classes including classes absent in the patch. If a class is not present in target or prediction, $\frac{2(0) + 1}{0 + 1} = 1.0 \implies \text{Loss} = 0.0$. However, any small false-positive prediction incurs a massive penalty, heavily training the network toward predicting zero pixels for all rare classes.

### Current Optimizer:
* `AdamW(lr=0.001, weight_decay=1e-4)` with `CosineAnnealingLR`.
* Effective, but needs gradient clipping and progressive layer-wise learning rates (slower for pretrained backbone, faster for decoder/fusion).

---

## 7. Current Model Performance (Test Set Evaluation)

| Metric | Baseline Model (`fpcd_baseline_cnn.pt`) | Siamese Model (`fpcd_siamese_v1.pt`) | Target Engineering Status |
| :--- | :---: | :---: | :---: |
| **Pixel Accuracy** | 97.86% | 98.99% | Misleading high baseline |
| **mIoU (Macro All)** | 19.59% | **26.93%** | Unacceptable (Class Collapse) |
| **Change mIoU (Classes 1..4)** | 0.01% | **8.90%** | Unacceptable |
| **Macro F1 Score** | 19.81% | **30.40%** | Deficient |
| **Class 0 (Background) IoU** | 0.9787 | 0.9905 | Saturated |
| **Class 1 (Constructed) IoU** | 0.0006 | **0.3559** (Recall: 60.6%, Prec: 46.3%) | Operational |
| **Class 2 (Demolished) IoU** | **0.0000** | **0.0000** (0 / 10,568 pixels detected) | **COLLAPSED** |
| **Class 3 (Dried) IoU** | **0.0000** | **0.0000** (0 / 20,571 pixels detected) | **COLLAPSED** |
| **Class 4 (Wetted) IoU** | **0.0000** | **0.0000** (0 / 9,489 pixels detected) | **COLLAPSED** |
| **Area MAE ($m^2$)** | 1,358.18 $m^2$ | 396.55 $m^2$ | Moderately accurate on constructed |

---

## 8. Prioritized Engineering Action Plan

1. **Implement Class-Balanced Focal Tversky & Dynamic Weighted Loss:**
   - Combine Focal Loss ($\gamma = 2.0$, $\alpha$-weighted) with Mask-Aware Dice/Tversky loss focusing on false negatives for Classes 2, 3, and 4.
2. **Hard-Example & Rare-Class Guided Sampler:**
   - Implement `ClassBalancedSampler` that oversamples pairs containing Demolished, Dried, and Wetted pixels during training (strictly from the 434 training pairs; test set remains untouched).
3. **Advanced Siamese Architecture with Difference Attention:**
   - Add spatial and channel cross-attention between $T_0$ and $T_1$ feature maps prior to concatenation.
4. **Spectral & Field Mode Support:**
   - Integrate Sentinel-2 multi-spectral band processing (NDVI, NDWI, MNDWI) with quality scores for blur/exposure.
5. **Validation Confidence Calibration:**
   - Implement post-hoc Temperature Scaling on the validation set to report calibrated probabilistic confidence and ECE.
6. **Execution of Systematic Ablation Experiments & Comprehensive Reporting:**
   - Record baseline vs balanced loss vs attention vs hard-example mining in `reports/ablation_study.csv` and `FINAL_ML_REPORT.md`.
