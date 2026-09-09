"""
WATERSCOPE Backend - Copernicus Data Space Ecosystem (CDSE) Satellite Provider
Queries Sentinel-2 MSI level-2A and 1C STAC catalogs.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from backend.services.satellite.base import SatelliteProvider
from backend.config import settings

class CopernicusProvider(SatelliteProvider):
    @property
    def provider_name(self) -> str:
        return "copernicus"

    def __init__(self, stac_url: str = settings.COPERNICUS_STAC_URL):
        self.stac_url = stac_url.rstrip("/")

    def search_scenes(
        self,
        latitude: float,
        longitude: float,
        target_date: datetime,
        window_days: int = 15,
        max_cloud_cover: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        Executes STAC search on Copernicus Catalogue.
        """
        start_dt = target_date - timedelta(days=window_days)
        end_dt = target_date + timedelta(days=window_days)
        
        # Bounding box around point (approx 0.05 deg = ~5.5km)
        delta = 0.05
        bbox = [longitude - delta, latitude - delta, longitude + delta, latitude + delta]
        
        datetime_str = f"{start_dt.strftime('%Y-%m-%dT00:00:00Z')}/{end_dt.strftime('%Y-%m-%dT23:59:59Z')}"
        
        payload = {
            "collections": ["SENTINEL-2"],
            "bbox": bbox,
            "datetime": datetime_str,
            "limit": 10,
            "query": {
                "cloudCover": {"lte": max_cloud_cover}
            }
        }
        
        scenes = []
        try:
            resp = requests.post(
                f"{self.stac_url}/search",
                json=payload,
                timeout=5
            )
            if resp.status_code == 200:
                features = resp.json().get("features", [])
                for f in features:
                    props = f.get("properties", {})
                    scenes.append({
                        "scene_id": f.get("id"),
                        "provider": self.provider_name,
                        "acquisition_date": props.get("datetime", target_date.isoformat()),
                        "cloud_cover": float(props.get("cloudCover", 0.0)),
                        "resolution_meters": 10.0,
                        "geometry": f.get("geometry"),
                        "thumbnail": f.get("assets", {}).get("thumbnail", {}).get("href", ""),
                        "bands": ["B02", "B03", "B04", "B08", "B11"]
                    })
        except Exception as e:
            # If external Copernicus CDSE is unreachable or unconfigured
            print(f"[COPERNICUS] STAC query fallback: {e}")
            
        return scenes

    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.stac_url}/collections/SENTINEL-2/items/{scene_id}", timeout=5)
            if resp.status_code == 200:
                f = resp.json()
                props = f.get("properties", {})
                return {
                    "scene_id": f.get("id"),
                    "provider": self.provider_name,
                    "acquisition_date": props.get("datetime"),
                    "cloud_cover": float(props.get("cloudCover", 0.0)),
                    "geometry": f.get("geometry")
                }
        except Exception:
            pass
        return None
