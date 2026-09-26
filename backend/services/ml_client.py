"""
WATERSCOPE Backend - ML Service Connector
Communicates with the Siamese Bi-Temporal Change Detection engine.
"""

from typing import Dict, Any, Optional
import os
import requests
from backend.config import settings

class MLServiceClient:
    def __init__(self, service_url: str = settings.ML_SERVICE_URL):
        self.service_url = service_url.rstrip("/")

    def predict_change(
        self,
        t0_input: Any,
        t1_input: Any,
        mode: str = "satellite",
        intervention_type: str = "farm_pond",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes prediction either via direct in-process pipeline or over HTTP.
        """
        try:
            # Direct in-process invocation for optimal speed and reliability
            from src.inference.pipeline import ChangeDetectionPipeline
            pipe = ChangeDetectionPipeline(
                model_path=str(settings.DATA_DIR.parent / "models" / "fpcd_siamese_v1.pt"),
                model_type="siamese"
            )
            result = pipe.predict(t0_input, t1_input, mode=mode)
            return result
        except Exception as e:
            # Fallback to HTTP call
            try:
                files = {
                    "image_t0": open(t0_input, "rb") if isinstance(t0_input, str) else t0_input,
                    "image_t1": open(t1_input, "rb") if isinstance(t1_input, str) else t1_input
                }
                data = {"mode": mode}
                resp = requests.post(f"{self.service_url}/ml/predict", files=files, data=data, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
            except Exception as http_err:
                pass
                
            raise RuntimeError(f"ML_SERVICE_UNAVAILABLE: {e}")
