"""
WATERSCOPE Backend - Automated Field Photo EXIF & Ingestion Service
Extracts camera parameters, GPS coordinates, timestamps, generates thumbnails,
and associates images with interventions according to rigorous geospatial integrity.
"""

import os
import uuid
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from PIL import Image, ExifTags

from backend.config import settings
from backend.database.models import FieldImage, Intervention

def dms_to_decimal(dms: Tuple, ref: str) -> Optional[float]:
    """Converts GPS degrees, minutes, seconds tuple to signed decimal degrees."""
    try:
        def to_float(val):
            if isinstance(val, (int, float)):
                return float(val)
            if hasattr(val, "numerator") and hasattr(val, "denominator"):
                return float(val.numerator) / float(val.denominator)
            if isinstance(val, tuple) and len(val) == 2:
                return float(val[0]) / float(val[1])
            return float(val)

        deg = to_float(dms[0])
        minutes = to_float(dms[1])
        seconds = to_float(dms[2])

        decimal = deg + (minutes / 60.0) + (seconds / 3600.0)
        if ref.upper() in ["S", "W"]:
            decimal = -decimal
        return round(decimal, 6)
    except Exception as e:
        return None

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in meters between two coordinates."""
    r = 6371000.0 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

class PhotoProcessingService:
    """
    Parses EXIF metadata, verifies image file integrity, generates thumbnails,
    and performs spatial association with watershed interventions.
    """
    def __init__(self, upload_dir: Path = settings.UPLOAD_DIR, thumb_dir: Path = settings.THUMBNAIL_DIR):
        self.upload_dir = upload_dir
        self.thumb_dir = thumb_dir

    def extract_exif(self, img: Image.Image) -> Dict[str, Any]:
        """Extracts camera metadata and GPS coordinates from image EXIF tags."""
        exif_raw = img.getexif()
        metadata = {
            "make": None,
            "model": None,
            "capture_date": None,
            "latitude": None,
            "longitude": None,
            "gps_status": "GPS_MISSING",
            "camera_software": None
        }

        if not exif_raw:
            return metadata

        # Map basic EXIF tags
        for tag_id, val in exif_raw.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            if tag_name == "Make":
                metadata["make"] = str(val).strip()
            elif tag_name == "Model":
                metadata["model"] = str(val).strip()
            elif tag_name == "Software":
                metadata["camera_software"] = str(val).strip()
            elif tag_name in ["DateTime", "DateTimeOriginal"]:
                metadata["capture_date"] = str(val)

        # Map GPS IFD sub-tags (Tag 34853 / 0x8825)
        gps_ifd = exif_raw.get_ifd(0x8825)
        if gps_ifd:
            gps_data = {}
            for t_id, t_val in gps_ifd.items():
                t_name = ExifTags.GPSTAGS.get(t_id, t_id)
                gps_data[t_name] = t_val

            lat_dms = gps_data.get("GPSLatitude")
            lat_ref = gps_data.get("GPSLatitudeRef", "N")
            lon_dms = gps_data.get("GPSLongitude")
            lon_ref = gps_data.get("GPSLongitudeRef", "E")

            if lat_dms and lon_dms:
                lat = dms_to_decimal(lat_dms, lat_ref)
                lon = dms_to_decimal(lon_dms, lon_ref)
                
                # Coordinate validity check
                if lat is not None and lon is not None:
                    if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                        metadata["latitude"] = lat
                        metadata["longitude"] = lon
                        metadata["gps_status"] = "GPS_AVAILABLE"

        return metadata

    def generate_thumbnail(self, img: Image.Image, output_path: Path, max_size=(256, 256)) -> str:
        """Generates low-latency RGB thumbnail preserving aspect ratio."""
        thumb = img.copy()
        thumb.thumbnail(max_size, Image.Resampling.LANCZOS)
        thumb.convert("RGB").save(output_path, format="JPEG", quality=85)
        return str(output_path)

    def process_upload(
        self,
        file_bytes: bytes,
        filename: str,
        image_type: str = "UNKNOWN",
        target_intervention_id: Optional[str] = None,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Executes complete ingestion pipeline:
        Reads EXIF, extracts GPS, writes original + thumbnail,
        associates with nearest intervention if applicable.
        """
        file_id = f"img-{uuid.uuid4().hex[:12]}"
        ext = Path(filename).suffix.lower() or ".jpg"
        if ext not in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
            ext = ".jpg"

        dest_orig = self.upload_dir / f"{file_id}{ext}"
        dest_thumb = self.thumb_dir / f"{file_id}_thumb.jpg"

        with open(dest_orig, "wb") as f:
            f.write(file_bytes)

        with Image.open(dest_orig) as img:
            exif_info = self.extract_exif(img)
            self.generate_thumbnail(img, dest_thumb)

        # Parse capture date
        capture_dt = None
        if exif_info.get("capture_date"):
            try:
                capture_dt = datetime.strptime(exif_info["capture_date"], "%Y:%m:%d %H:%M:%S")
            except Exception:
                try:
                    capture_dt = datetime.fromisoformat(exif_info["capture_date"])
                except Exception:
                    capture_dt = None

        if capture_dt is None:
            capture_dt = datetime.utcnow()

        # Spatial intervention association
        lat = exif_info.get("latitude")
        lon = exif_info.get("longitude")
        matched_intervention_id = target_intervention_id

        if matched_intervention_id is None and lat is not None and lon is not None and db_session is not None:
            # Query active interventions and find nearest within 1000m
            interventions = db_session.query(Intervention).filter(
                Intervention.latitude.isnot(None),
                Intervention.longitude.isnot(None)
            ).all()

            nearest_int = None
            min_dist = float("inf")
            for int_rec in interventions:
                dist = haversine_distance_meters(lat, lon, int_rec.latitude, int_rec.longitude)
                if dist < min_dist:
                    min_dist = dist
                    nearest_int = int_rec

            if nearest_int and min_dist <= 1000.0:
                matched_intervention_id = nearest_int.id

        # Create FieldImage database record
        field_img = FieldImage(
            id=file_id,
            intervention_id=matched_intervention_id,
            file_path=str(dest_orig),
            thumbnail_path=str(dest_thumb),
            latitude=lat,
            longitude=lon,
            gps_status=exif_info["gps_status"],
            geometry_geojson={"type": "Point", "coordinates": [lon, lat]} if lat is not None else None,
            capture_date=capture_dt,
            image_type=image_type.upper(),
            exif_metadata=exif_info,
            source="field_photo_upload"
        )

        if db_session is not None:
            db_session.add(field_img)
            db_session.commit()
            db_session.refresh(field_img)

        return {
            "id": file_id,
            "intervention_id": matched_intervention_id,
            "file_path": str(dest_orig),
            "thumbnail_path": str(dest_thumb),
            "latitude": lat,
            "longitude": lon,
            "gps_status": exif_info["gps_status"],
            "capture_date": capture_dt.isoformat() if capture_dt else None,
            "image_type": image_type.upper(),
            "exif_metadata": exif_info
        }
