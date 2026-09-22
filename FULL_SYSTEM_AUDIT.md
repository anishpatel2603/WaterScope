# FULL SYSTEM AUDIT: WATERSCOPE GEO-SPATIAL INTELLIGENCE PLATFORM
**Audit Date:** 2026-09-12  
**System:** WATERSCOPE – Watershed Monitoring & Geo-Spatial Analysis Platform  
**Auditor:** Senior Full-Stack, GIS, ML, Data, QA & Security Engineering Review  
**Target Environment:** Python 3.13 / FastAPI / PyTorch / React 18 / Vite / TypeScript / SQLite (PostGIS compatible)

---

## Executive Summary
A comprehensive end-to-end technical audit of the WATERSCOPE repository was performed across all 37 prompt dimensions. The core architecture possesses strong foundations, including an actual trained Siamese change detection PyTorch model (`models/fpcd_siamese_v1.pt`, 74MB), a 4-component weighted scoring engine, 339 real registered interventions in `data/waterscope.db`, and interactive GIS/slider UI components. 

However, critical and high-severity flaws were discovered that compromise data integrity, cross-site consistency, and production reliability:
1. Hardcoded fallback values (`84.5`, `1240`, `1480`, `1850`, `2400`, `4400`, `0.13`, `0.60`, `0.34`, `0.12`, `62`) embedded in UI components and mock fallbacks.
2. Missing `metrics` prop in `InterventionDetailPage` causing every site to render the exact same fallback buffer table.
3. UI pages (`BeforeAfterPage`, `ChangeDetectionPage`) utilizing fake client-side mock objects instead of invoking the running PyTorch backend.
4. Security vulnerability in `api/app.py` `/ml/retrain` using unvalidated formatted strings in `subprocess.run(..., shell=True)`.
5. Missing backend API endpoint to list field images (`GET /api/images`), resulting in `EvidencePage` displaying hardcoded images.
6. Execution of plain `pytest` failing due to missing `pytest.ini` with `pythonpath = .`.
7. Repeated loading of 74MB model weights on every request in `ml_client.py`.
8. Geodesic distortion in GIS buffer generation and physical area scaling.
9. EXIF photo processing fabricating `datetime.utcnow()` when image timestamps are missing.

---

## System Audit Matrix

| ID | Component | File | Severity | Issue | Root Cause | Recommended Fix | Status |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **AUD-01** | Test Suite | `pytest.ini` / `tests/*` | **CRITICAL** | `pytest` fails with `ModuleNotFoundError` for `src` and `backend` | Root directory not in `sys.path` when running plain `pytest` | Add `pytest.ini` at workspace root defining `pythonpath = .` and test flags | Pending Fix |
| **AUD-02** | Security / API | `api/app.py:314` | **CRITICAL** | Shell command injection vulnerability in `/ml/retrain` | Unsanitized string formatting executed with `shell=True` in background task | Validate input boundaries and execute tokenized process arguments without `shell=True` | Pending Fix |
| **AUD-03** | Frontend API | `frontend/src/services/apiClient.ts:48-60` | **CRITICAL** | Fake operational status fallback on system error | Catch block returns hardcoded `{ backend_online: true, active_interventions_count: 62 }` | Return genuine offline state so UI correctly notifies user of backend unavailability | Pending Fix |
| **AUD-04** | UI / Data Integrity | `frontend/src/components/BufferMetricsTable.tsx:19-84` | **HIGH** | Hardcoded metric fallbacks (`1240`, `1480`, `1850`, `2400`, `4400`, `0.13`, etc.) | When `metrics` prop is empty, static array is rendered | Show clean empty/loading state ("Spatial metrics pending analysis") instead of hardcoded numbers | Pending Fix |
| **AUD-05** | UI / Cross-Site | `frontend/src/pages/InterventionDetailPage.tsx:199,234,262` | **HIGH** | `BufferMetricsTable` rendered without `metrics` prop; hardcoded 94.8% & 1240m² | Props not passed from loaded site data; hardcoded prediction object passed to `ChangeMaskOverlay` | Pass site-specific metrics, dynamic confidence, and dynamic changed area | Pending Fix |
| **AUD-06** | ML Integration | `frontend/src/pages/BeforeAfterPage.tsx:86-96` | **HIGH** | Client-side mock prediction object in `handleRunInference` | `setPredictionResult(mockResult)` hardcodes 95.4% confidence and static values | Call backend `/api/analysis/create` or `/ml/predict` to run the real PyTorch model on preset scenes | Pending Fix |
| **AUD-07** | ML Integration | `frontend/src/pages/ChangeDetectionPage.tsx:59-80` | **HIGH** | Client-side mock result returned when files are not uploaded | Fallback returns static JSON without running ML engine | Call backend analysis with active preset or mandate uploaded image pair | Pending Fix |
| **AUD-08** | API / Database | `backend/main.py` / `frontend/src/pages/EvidencePage.tsx` | **HIGH** | Missing `GET /api/images` endpoint; `EvidencePage` hardcodes 4 static photos | No listing endpoint for `FieldImage` records; frontend uses local array | Implement `GET /api/images` (with `intervention_id` filter) and wire `EvidencePage` to fetch real DB photos | Pending Fix |
| **AUD-09** | Field Image EXIF | `backend/services/photo_service.py:163-164` | **HIGH** | Fabricates `datetime.utcnow()` when photo timestamp is missing | Fallback assigns current time if EXIF capture date is null | Set `capture_date = None` and display "Capture date unavailable" in UI (Phase 9 mandate) | Pending Fix |
| **AUD-10** | Performance | `backend/services/ml_client.py:30-34` | **HIGH** | PyTorch model re-initialized and 74MB weights reloaded on every inference request | `ChangeDetectionPipeline` constructed inside function scope without caching | Cache pipeline instance as a singleton across requests | Pending Fix |
| **AUD-11** | Backend API | `backend/main.py:578-605` | **HIGH** | `GET /api/analysis/{id}` response omits `observed_impact` | Endpoint constructs dictionary without `observed_impact` key; `AnalysisDetailPage` fails to render | Include `observed_impact` and full spectral metrics in endpoint payload | Pending Fix |
| **AUD-12** | GIS Engine | `backend/services/gis_service.py:88-93,165` | **MEDIUM** | Buffer circle distortion and artificial area scaling | Degrees of lon and lat averaged into single scalar radius; `area_factor` applies `((1000/d)**0.5)` | Use accurate geodesic/UTM projection and standard pixel ground sampling distance area (`res^2`) | Pending Fix |
| **AUD-13** | Scoring Engine | `backend/scoring/site_provider.py:151-186` | **MEDIUM** | Fixed constant NDVI/NDWI estimates in fallback pair telemetry | Hardcodes `0.14`, `0.45` rather than measuring real raster differences when T0/T1 exist | Calculate actual spectral differences from T0/T1 images using `estimate_spectral_indices_from_rgb` | Pending Fix |
| **AUD-14** | Frontend Dashboard | `frontend/src/pages/DashboardPage.tsx:171` | **MEDIUM** | Hardcoded average impact score `83.6 / 100` | KPI card uses static text string | Compute average score dynamically across all loaded site interventions | Pending Fix |
| **AUD-15** | AI Assistant | `frontend/src/pages/AIAssistantPage.tsx:19,69` | **MEDIUM** | Hardcoded site count (62) and static evidence text (1480 m², +0.12 NDVI) | Welcome text and fallback answers contain static mock values | Dynamically inject actual active site counts and site-specific telemetry | Pending Fix |
| **AUD-16** | Scoring Deprecation | `backend/scoring/scoring_engine.py:160,170,180` | **MEDIUM** | Python 3.13 deprecation warnings on `datetime.utcnow()` | `datetime.utcnow()` scheduled for removal in future Python | Update to `datetime.now(timezone.utc)` | Pending Fix |
| **AUD-17** | Reports Page | `frontend/src/pages/ReportsPage.tsx:9,32` | **MEDIUM** | Static generated date (`2026-09-06`), limit 8, missing CSV/GeoJSON download | Static object initialization; missing file export callbacks | Bind current date, allow selecting any site, implement CSV and GeoJSON downloads | Pending Fix |
| **AUD-18** | Configuration | `.gitignore:3` | **LOW** | `.env.example` included in `.gitignore` | Template environment file is ignored from git | Remove `.env.example` from `.gitignore` | Pending Fix |
| **AUD-19** | Terminology | `Navbar.tsx:65`, `SettingsPage.tsx:191` | **LOW** | Provider labeled "Synthetic" | Confuses simulated/benchmark demo data with fabricated claims | Rename to "Sentinel-2 Demo Benchmark" | Pending Fix |

---

## Data Flow Verification (T0 → Processing → UI)

### 1. Site Selection & Isolation Flow
- **Current state:** Selecting an intervention on the Dashboard updates `selectedInterventionId` in Zustand `useAppStore`. Navigating to `/interventions/:id` fetches `/api/interventions/:id` and `/api/interventions/:id/score`.
- **Finding:** The backend `get_or_compute_site_score` correctly keys calculations by `site_id` in `SITE_SCORE_CACHE[intervention_id]`. However, in the frontend, `InterventionDetailPage` failed to pass `metrics` to `BufferMetricsTable` and hardcoded changed area to `1240` and confidence to `94.8%`.
- **Required Fix:** Bind `BufferMetricsTable` and `ChangeMaskOverlay` strictly to the loaded site data.

### 2. Machine Learning Inference Flow
- **Current state:** `api/app.py` has a full `ChangeDetectionPipeline` using `SiameseChangeNet` loaded from `models/fpcd_siamese_v1.pt`.
- **Finding:** The UI on `BeforeAfterPage` was mocking the prediction on the client side (`mockResult`) instead of calling `/api/analysis/create`.
- **Required Fix:** Route all inspection runs through the real API so actual model tensor inference is performed.

### 3. Field Evidence Flow
- **Current state:** Photos can be uploaded to `/api/images/upload`, which saves the file and generates a thumbnail.
- **Finding:** There was no listing endpoint `/api/images`, so the UI rendered 4 hardcoded photos.
- **Required Fix:** Add `/api/images` with site filtering and render real database photos.

---

## Implementation Plan

1. **Test & Infrastructure:** Add `pytest.ini` with `pythonpath = .` to make `pytest` pass cleanly without module errors.
2. **Security & Performance:** Fix command injection in `api/app.py` `/ml/retrain`; cache `ChangeDetectionPipeline` in `ml_client.py`.
3. **Backend API Fixes:**
   - Add `GET /api/images` endpoint in `backend/main.py`.
   - Fix `GET /api/analysis/{id}` to return `observed_impact` and complete `spatial_metrics`.
   - Fix `photo_service.py` to leave `capture_date` as `None` when missing.
   - Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` in `scoring_engine.py`.
   - Fix GIS buffer calculation and area factor in `gis_service.py`.
   - Update `site_provider.py` to compute real NDVI/NDWI deltas when T0/T1 exist.
4. **Frontend Fixes:**
   - Remove fake fallback from `apiClient.ts` `/api/system/status`.
   - Remove hardcoded fallbacks from `BufferMetricsTable.tsx`.
   - Fix `InterventionDetailPage.tsx` to pass real site metrics, area, and confidence.
   - Wire `BeforeAfterPage.tsx` and `ChangeDetectionPage.tsx` to call real backend inference.
   - Connect `EvidencePage.tsx` to fetch real photos from `/api/images` for the selected site.
   - Calculate dynamic KPI average in `DashboardPage.tsx`.
   - Add CSV and GeoJSON report download handlers to `ReportsPage.tsx`.
   - Update `AIAssistantPage.tsx`, `Navbar.tsx`, `SettingsPage.tsx` to eliminate hardcoded counts/labels.
5. **Testing & Verification:**
   - Run `pytest` and verify all tests pass.
   - Run `npm run build` and verify frontend bundle builds cleanly without TypeScript errors.
   - Run cross-site verification across multiple sites to ensure distinct, site-specific scores.
   - Verify report exports and demo/real mode behavior.
