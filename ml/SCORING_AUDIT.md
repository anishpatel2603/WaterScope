# SCORING_AUDIT.md: Audit of Watershed Observed Impact & Scoring System

**Audit Date:** 2026-09-09  
**Auditor:** Senior Computer Vision / Remote Sensing ML Engineer  
**Status:** COMPLETED — Root Cause Identified  

---

## 1. Executive Summary

Every watershed and intervention site inspected across the platform currently displays an identical **Composite Index score of 84.5 / 100** (accompanied by **ML Change: 92.0%**, **Water Retention: 88.0%**, **Vegetation: 72.5%**, and **Data Quality / Model Confidence: 90.0%**). 

The audit confirms that this identical score across all sites is caused by a chain of hardcoded mock fallbacks in the frontend components, unpassed props in the site detail view, lack of a dedicated site-specific scoring API endpoint, and hardcoded fallback values in backend report generation.

---

## 2. Hardcoded Values & Mock Data Found

### A. Frontend Fallback in `ObservedImpactCard.tsx`
- **File:** `frontend/src/components/ObservedImpactCard.tsx` (Lines 15–30)
- **Code:**
  ```typescript
  const data: ObservedImpact = impact || {
    verdict: 'OBSERVED IMPROVEMENT',
    verdict_type: 'OBSERVED_CHANGE',
    composite_score: 84.5,
    narrative:
      'Bi-temporal analysis confirms physical construction of farm pond structure with substantial increase in localized surface water retention (+1,240 m²) and surrounding vegetative vigour within 250m buffer.',
    components: {
      ml_change: { score: 92.0, weight: 0.35 },
      water_extent: { score: 88.0, weight: 0.3 },
      vegetation_response: { score: 72.5, weight: 0.2 },
      model_confidence: { score: 90.0, weight: 0.15 },
    },
    ...
  };
  ```
- **Headline (Line 72):**
  `<h3 className="text-base font-bold ...">Synthetic Impact Verdict</h3>`

### B. Missing Prop in `InterventionDetailPage.tsx`
- **File:** `frontend/src/pages/InterventionDetailPage.tsx` (Line 247)
- **Code:**
  ```tsx
  <ObservedImpactCard />
  ```
- **Problem:** When a user navigates to `/interventions/:id` for **any** site (e.g. `int-akola-akhatwada-0`, `int-amravati-takarkheda-1`, `int-washim-babhali-5`), `InterventionDetailPage` renders `<ObservedImpactCard />` without passing the `impact` prop. Consequently, the component always renders the hardcoded fallback object containing 84.5, 92%, 88%, 72.5%, and 90%.

### C. Static Mock Data in `ReportsPage.tsx`
- **File:** `frontend/src/pages/ReportsPage.tsx` (Lines 7–44)
- **Code:**
  ```typescript
  const reports = [
    {
      id: 'rep-001',
      title: 'Bi-Temporal Verification Audit - Farm Pond Akhatwada 10',
      composite_score: 84.5,
      components: { ml_change: 92.0, water_extent: 88.0, vegetation_response: 72.5, model_confidence: 90.0 }
    },
    ...
  ];
  ```

### D. Hardcoded Score in Backend Report Generator
- **File:** `backend/main.py` (Lines 837–846)
- **Code:**
  ```python
  rep = Report(
      id=f"rep-{uuid.uuid4().hex[:10]}",
      analysis_job_id=payload.analysis_job_id,
      title=payload.title or f"Intervention Verification Audit - {payload.analysis_job_id}",
      verdict="OBSERVED IMPROVEMENT",
      composite_score=85.0,
      scientific_limitation_notice="..."
  )
  ```

### E. AI Assistant Static Knowledge
- **File:** `frontend/src/pages/AIAssistantPage.tsx` (Line 57)
- **Code:**
  `For Akhatwada 10, this synthesized into a composite score of **84.5 / 100** ("OBSERVED IMPROVEMENT").`

---

## 3. Current Scoring Formula in `backend/services/scoring_engine.py`

In `backend/services/scoring_engine.py`:
- **Weights:**
  - `ml_change_weight`: 0.35 (35%)
  - `water_extent_weight`: 0.30 (30%)
  - `vegetation_response_weight`: 0.20 (20%)
  - `model_confidence_weight`: 0.15 (15%)
- **Formula:**
  $$\text{Composite} = 0.35 \times \text{ML} + 0.30 \times \text{Water} + 0.20 \times \text{Veg} + 0.15 \times \text{Conf}$$
- **Limitations of Current Engine:**
  1. Component scores rely on linear heuristic approximations (e.g. `50.0 + delta_water_m2 / 50.0 + delta_ndwi * 80.0`) without handling edge cases, severe negative changes, or missing sensor observations.
  2. The 4th component was labeled `model_confidence` rather than true multi-factor **Data Quality** (GPS validity, EXIF date check, sensor resolution, cloud coverage, temporal proximity).
  3. No dedicated API endpoint exists for fetching a site's real-time or cached score by `site_id` / `intervention_id`.
  4. Narratives were static template strings rather than dynamically generated from actual measurements (+1,240 m² was hardcoded regardless of actual delta).

---

## 4. API & Database Fields Involved

### Database Models (`backend/database/models.py`)
- `Intervention`: `id`, `name`, `type`, `latitude`, `longitude`, `location_source`, `village`, `district`, `implementation_date`, `status`
- `FieldImage`: `gps_status`, `capture_date`, `exif_metadata`, `image_type`
- `SatelliteScene`: `cloud_cover`, `resolution_meters`, `acquisition_date`, `bands`
- `SpatialMetric`: `delta_ndvi`, `delta_ndwi`, `water_extent_m2_before`, `water_extent_m2_after`, `delta_water_extent_m2`, `delta_vegetation_extent_m2`
- `MLPrediction`: `change_class`, `confidence`, `pixel_change_percentage`, `changed_area_m2`
- `Report`: `composite_score`, `verdict`, `components_breakdown`

### API Endpoints
- **Existing:**
  - `POST /api/analysis/create`: Executes full pipeline on uploaded/matched images and stores `observed_impact`.
  - `GET /api/interventions/{id}`: Returns intervention details, but currently lacks `observed_impact` or score fields.
- **Missing (Required):**
  - `GET /api/interventions/{id}/score` or `GET /api/sites/{id}/score`: Endpoint that dynamically resolves the site's available data, executes the scoring engine, and returns a standardized site-specific scoring object.

---

## 5. Frontend Components Involved

1. `frontend/src/components/ObservedImpactCard.tsx`: Displays the Composite Index, 4 sub-scores, dynamic narrative, and verdict.
2. `frontend/src/pages/InterventionDetailPage.tsx`: Main site inspection page; must query and pass the site-specific score to `ObservedImpactCard`.
3. `frontend/src/pages/ReportsPage.tsx`: Dossier view; must display site-specific audit records rather than static mock items.
4. `frontend/src/services/apiClient.ts`: Must expose `getSiteScore(siteId)` and integrate with backend endpoints.
5. `frontend/src/types/api.ts`: Schema definitions for `ObservedImpact`, `SiteScoreResponse`, and `ScoreComponents`.

---

## 6. Proposed Solution Architecture

### 1. Dedicated Backend Scoring Module (`backend/scoring/`)
Structure:
```
backend/
└── scoring/
    ├── __init__.py
    ├── normalization.py       # Robust min-max clamp, non-linear saturation, delta scaling
    ├── evidence.py            # Site evidence extraction from ML, GIS, Satellite, Field EXIF
    ├── verdict.py             # Configurable multi-condition non-causal decision logic
    └── scoring_engine.py      # SiteSpecificScoringEngine conforming to v2.0 spec
```

### 2. Standardized Scoring Object Schema (v2.0)
Conforming strictly to Section 11 of the specification:
```json
{
  "site_id": "int-akola-akhatwada-10",
  "scoring_version": "v2.0",
  "ml_change_score": 91.2,
  "water_retention_score": 84.6,
  "vegetation_score": 73.1,
  "data_quality_score": 88.0,
  "composite_index": 85.1,
  "verdict": "OBSERVED IMPROVEMENT",
  "confidence": 0.88,
  "evidence": {
    "before_water_area_m2": 0.0,
    "after_water_area_m2": 1240.0,
    "water_area_change_m2": 1240.0,
    "water_area_change_percent": 100.0,
    "ndvi_before": 0.28,
    "ndvi_after": 0.42,
    "ndvi_change": 0.14,
    "ndwi_before": -0.15,
    "ndwi_after": 0.35,
    "ndwi_change": 0.50,
    "ml_confidence": 0.89,
    "quality_score": 0.94
  },
  "explanation": {
    "ml_change": "High-confidence structural change detected (+1,240 m² constructed basin)",
    "water_retention": "Surface water area increased by 1,240 m² with positive NDWI shift",
    "vegetation": "Canopy vigour increased by +0.14 NDVI in 250m perimeter",
    "data_quality": "High-resolution orthophotos (1.0m/px) with valid GPS and 0% cloud cover"
  },
  "narrative": "Observed farm pond construction with surface water extent expanding by 1,240 m² and perimeter NDVI increasing by +0.14.",
  "data_sources": ["Sentinel-2 MSI", "Google Earth / FPCD High-Res", "State Cadastral GIS"],
  "model_version": "waterscope_change_model_v3"
}
```

### 3. Backend API Endpoints
- `GET /api/interventions/{id}/score`: Computes or retrieves deterministic site-specific score.
- `GET /api/sites/{id}/score`: Alias for compatibility.
- Ensure `enrich_intervention` or `InterventionResponse` links the score.

### 4. Frontend Integration
- Update `apiClient.ts` with `getSiteScore(siteId: string)`.
- In `InterventionDetailPage.tsx`, fetch `useQuery(['siteScore', interventionId], () => apiClient.getSiteScore(interventionId))`, and pass the returned `data` directly into `<ObservedImpactCard impact={siteScore} />`.
- Update `ObservedImpactCard.tsx` header from `"Synthetic Impact Verdict"` to `"Observed Impact Evidence"`.
- Make explanations and narratives dynamic based on actual measurements.
