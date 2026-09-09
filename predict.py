"""
WATERSCOPE ML Engine - Prediction CLI
Usage:
  python predict.py --t0 data/fpcd/T0/sample.jpg --t1 data/fpcd/T1/sample.jpg --mode satellite
"""

import os
import json
import argparse
from pathlib import Path
from src.inference.pipeline import ChangeDetectionPipeline

def main():
    parser = argparse.ArgumentParser(description="Run WATERSCOPE Bi-temporal Change Prediction")
    parser.add_argument("--t0", required=True, help="Path to BEFORE image (T0)")
    parser.add_argument("--t1", required=True, help="Path to AFTER image (T1)")
    parser.add_argument("--model-path", default="models/fpcd_siamese_v1.pt", help="Path to checkpoint")
    parser.add_argument("--model-type", default="siamese", choices=["attention_siamese", "siamese", "baseline"], help="Model architecture")
    parser.add_argument("--mode", default="satellite", choices=["satellite", "field"], help="Inference mode")
    parser.add_argument("--device", default="cpu", help="Compute device")
    parser.add_argument("--output", default=None, help="Optional output JSON filepath")
    args = parser.parse_args()

    pipeline = ChangeDetectionPipeline(
        model_path=args.model_path if os.path.exists(args.model_path) else None,
        model_type=args.model_type,
        device=args.device
    )

    result = pipeline.predict(args.t0, args.t1, mode=args.mode)
    
    # Print concise summary
    print("==================================================")
    print(f"WATERSCOPE CHANGE PREDICTION ({args.mode.upper()} MODE)")
    print("==================================================")
    print(f"Analysis ID:             {result['analysis_id']}")
    print(f"Change Class:            {result['change_class_display']} ({result['change_class']})")
    print(f"Calibrated Confidence:   {result['confidence'] * 100:.2f}% [{result['confidence_derivation_method']}]")
    print(f"Pixel Change:            {result['pixel_change_percentage']:.2f}%")
    print(f"Estimated Changed Area:  {result['changed_area_m2']} m²")
    print(f"Hybrid Verdict:          {result['hybrid_analysis']['verdict']}")
    print(f"Composite Score:         {result['hybrid_analysis']['composite_score']} / 100")
    print(f"Scientific Disclaimer:   {result['scientific_disclaimer']}")
    print("==================================================")

    if args.output:
        # Exclude giant data URIs for raw json file if needed
        clean_res = dict(result)
        clean_res["change_mask_url"] = "<base64_png_encoded>"
        clean_res["overlay_url"] = "<base64_png_encoded>"
        clean_res["t0_url"] = "<base64_jpeg_encoded>"
        clean_res["t1_url"] = "<base64_jpeg_encoded>"
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(clean_res, f, indent=2)
        print(f"[PREDICT] Output JSON saved to {args.output}")

if __name__ == "__main__":
    main()
