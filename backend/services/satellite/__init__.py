"""
WATERSCOPE Backend - Satellite Provider Factory
"""

from typing import Optional
from backend.services.satellite.base import SatelliteProvider
from backend.services.satellite.copernicus import CopernicusProvider
from backend.services.satellite.demo import DemoSatelliteProvider
from backend.services.satellite.bhuvan import BhuvanProvider, SrishtiDrishtiProvider
from backend.config import settings

def get_satellite_provider(provider_name: Optional[str] = None) -> SatelliteProvider:
    """
    Returns configured or requested satellite provider.
    Defaults to DemoSatelliteProvider if DEMO_MODE=True or if requested provider is unavailable.
    """
    p_name = (provider_name or ("demo" if settings.DEMO_MODE else "copernicus")).lower()
    
    if p_name == "copernicus":
        return CopernicusProvider()
    elif p_name == "bhuvan":
        return BhuvanProvider()
    elif p_name == "srishti_drishti":
        return SrishtiDrishtiProvider()
    else:
        return DemoSatelliteProvider()
