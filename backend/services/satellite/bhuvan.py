"""
WATERSCOPE Backend - ISRO Bhuvan & Srishti-Drishti Satellite Providers
Indian National Remote Sensing Centre (NRSC) / ISRO thematic integration.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.services.satellite.base import SatelliteProvider
from backend.config import settings

class BhuvanProvider(SatelliteProvider):
    @property
    def provider_name(self) -> str:
        return "bhuvan"

    def __init__(self, api_token: str = settings.BHUVAN_API_TOKEN):
        self.api_token = api_token

    def search_scenes(
        self,
        latitude: float,
        longitude: float,
        target_date: datetime,
        window_days: int = 15,
        max_cloud_cover: float = 30.0
    ) -> List[Dict[str, Any]]:
        # In absence of active enterprise ISRO token, return empty list or fallback
        if not self.api_token:
            return []
        return []

    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        return None

class SrishtiDrishtiProvider(SatelliteProvider):
    @property
    def provider_name(self) -> str:
        return "srishti_drishti"

    def __init__(
        self,
        base_url: str = settings.SRISHTI_DRISHTI_BASE_URL,
        api_key: str = settings.SRISHTI_DRISHTI_API_KEY,
        enabled: bool = settings.SRISHTI_DRISHTI_ENABLED
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.enabled = enabled

    def search_scenes(
        self,
        latitude: float,
        longitude: float,
        target_date: datetime,
        window_days: int = 15,
        max_cloud_cover: float = 30.0
    ) -> List[Dict[str, Any]]:
        if not self.enabled or not self.api_key:
            return []
        return []

    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        return None
