"""
WATERSCOPE Backend - Satellite Provider Interface
Defines the abstract interface for querying and fetching bi-temporal satellite scenes.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, date

class SatelliteProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of provider, e.g. 'copernicus', 'sentinel_hub', 'demo'."""
        pass

    @abstractmethod
    def search_scenes(
        self,
        latitude: float,
        longitude: float,
        target_date: datetime,
        window_days: int = 15,
        max_cloud_cover: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        Searches available satellite scenes around a coordinate within ±window_days.
        Returns list of standardized scene metadata dicts.
        """
        pass

    @abstractmethod
    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific satellite scene by its unique identifier."""
        pass
