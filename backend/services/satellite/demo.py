"""
WATERSCOPE Backend - High-Fidelity Demo Satellite Provider
Provides reproducible, deterministic bi-temporal Sentinel-2 scenes linked to real
Maharashtra raster composites for local processing and testing.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
from backend.services.satellite.base import SatelliteProvider
from backend.config import settings

class DemoSatelliteProvider(SatelliteProvider):
    @property
    def provider_name(self) -> str:
        return "demo"

    def search_scenes(
        self,
        latitude: float,
        longitude: float,
        target_date: datetime,
        window_days: int = 15,
        max_cloud_cover: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        Generates realistic, deterministic Sentinel-2 scenes within the requested ±window_days.
        """
        scenes = []
        # Sentinel-2 revisit cycle is 5 days
        offsets = [-10, -5, 0, 5, 10]
        valid_offsets = [o for o in offsets if abs(o) <= window_days]
        
        for idx, offset in enumerate(valid_offsets):
            acq_dt = target_date + timedelta(days=offset)
            date_str = acq_dt.strftime("%Y%m%d")
            
            # Deterministic hash for tile name and cloud cover
            hash_input = f"{latitude:.2f}_{longitude:.2f}_{date_str}"
            h_val = int(hashlib.md5(hash_input.encode()).hexdigest()[:6], 16)
            cloud = round((h_val % 250) / 10.0, 1) # 0.0 to 25.0%
            
            if cloud > max_cloud_cover:
                continue
                
            scene_id = f"S2A_MSIL2A_{date_str}T054651_N0500_R048_T43QDA_{idx:02d}"
            
            # 10km x 10km bounding polygon
            delta = 0.05
            poly = {
                "type": "Polygon",
                "coordinates": [[
                    [round(longitude - delta, 4), round(latitude - delta, 4)],
                    [round(longitude + delta, 4), round(latitude - delta, 4)],
                    [round(longitude + delta, 4), round(latitude + delta, 4)],
                    [round(longitude - delta, 4), round(latitude + delta, 4)],
                    [round(longitude - delta, 4), round(latitude - delta, 4)]
                ]]
            }
            
            scenes.append({
                "scene_id": scene_id,
                "provider": self.provider_name,
                "acquisition_date": acq_dt.isoformat() + "Z",
                "cloud_cover": cloud,
                "resolution_meters": 10.0,
                "geometry": poly,
                "thumbnail": f"/api/preset-image/Akola_Akhatwada_0/t1",
                "bands": ["B02_Blue", "B03_Green", "B04_Red", "B08_NIR", "B11_SWIR"]
            })
            
        return sorted(scenes, key=lambda s: s["acquisition_date"])

    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        return {
            "scene_id": scene_id,
            "provider": self.provider_name,
            "acquisition_date": datetime.utcnow().isoformat() + "Z",
            "cloud_cover": 4.2,
            "resolution_meters": 10.0,
            "bands": ["B02_Blue", "B03_Green", "B04_Red", "B08_NIR", "B11_SWIR"]
        }
