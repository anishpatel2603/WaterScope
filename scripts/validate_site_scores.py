"""
WATERSCOPE Site Score Validation Generator
Iterates through all sites/interventions in the database,
computes their site-specific scores via SiteSpecificScoringEngine,
and records the results in reports/site_score_validation.csv.
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.session import SessionLocal
from backend.database.models import Intervention
from backend.scoring.site_provider import get_or_compute_site_score

def main():
    db = SessionLocal()
    interventions = db.query(Intervention).all()
    print(f"[VALIDATION] Computing scores for {len(interventions)} sites...")

    out_path = Path("reports/site_score_validation.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    scores_seen = set()

    for it in interventions:
        score = get_or_compute_site_score(it.id, db)
        rows.append({
            "site_id": it.id,
            "intervention_name": it.name,
            "village": it.village,
            "district": it.district,
            "ml_change_score": score["ml_change_score"],
            "water_retention_score": score["water_retention_score"],
            "vegetation_score": score["vegetation_score"],
            "data_quality_score": score["data_quality_score"],
            "composite_index": score["composite_index"],
            "verdict": score["verdict"]
        })
        scores_seen.add(score["composite_index"])

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "site_id", "intervention_name", "village", "district",
            "ml_change_score", "water_retention_score", "vegetation_score",
            "data_quality_score", "composite_index", "verdict"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[VALIDATION] Successfully saved {out_path} with {len(rows)} site records.")
    print(f"[VALIDATION] Unique score distributions observed across sites: {len(scores_seen)} distinct values.")
    print("[VALIDATION] First 8 sites:")
    for r in rows[:8]:
        print(f"  {r['site_id']} ({r['village']}): Composite={r['composite_index']} ({r['verdict']}) [ML:{r['ml_change_score']} W:{r['water_retention_score']} V:{r['vegetation_score']} Q:{r['data_quality_score']}]")
    db.close()

if __name__ == "__main__":
    main()
