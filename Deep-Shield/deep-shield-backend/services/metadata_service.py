from io import BytesIO
from typing import Any, Dict, Optional

import exifread
from PIL import Image


def _get_gps_from_tags(tags: Any) -> Optional[Dict[str, Any]]:
    """Extract GPS coordinates from EXIF tags if present."""
    gps_lat = tags.get("GPS GPSLatitude")
    gps_lon = tags.get("GPS GPSLongitude")
    gps_lat_ref = tags.get("GPS GPSLatitudeRef")
    gps_lon_ref = tags.get("GPS GPSLongitudeRef")
    if not all([gps_lat, gps_lon, gps_lat_ref, gps_lon_ref]):
        return None
    try:
        lat = _convert_ratio_to_float(gps_lat.values)
        lon = _convert_ratio_to_float(gps_lon.values)
        if str(gps_lat_ref) == "S":
            lat = -lat
        if str(gps_lon_ref) == "W":
            lon = -lon
        return {"lat": round(lat, 6), "lon": round(lon, 6)}
    except (TypeError, ZeroDivisionError):
        return None


def _convert_ratio_to_float(ratio_values: Any) -> float:
    """Convert exifread ratio (e.g. [Degrees, Minutes, Seconds]) to decimal degrees."""
    if not ratio_values or len(ratio_values) < 3:
        return 0.0
    d = float(ratio_values[0].num) / float(ratio_values[0].den or 1)
    m = float(ratio_values[1].num) / float(ratio_values[1].den or 1)
    s = float(ratio_values[2].num) / float(ratio_values[2].den or 1)
    return d + (m / 60.0) + (s / 3600.0)


def extract_metadata(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extract basic image info and EXIF metadata from image bytes.
    Returns basic info (format, dimensions), exif dict, and gps if present.
    """
    try:
        image = Image.open(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError("Invalid or corrupted image file.") from exc

    basic: Dict[str, Any] = {
        "format": image.format,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "size_bytes": len(file_bytes),
    }

    tags = exifread.process_file(BytesIO(file_bytes), details=False)
    exif: Dict[str, Any] = {}
    skip = ("JPEG Thumbnail", "TIFF Thumbnail", "Filename", "EXIF MakerNote")
    for tag, value in tags.items():
        if tag in skip or "Thumbnail" in tag or "MakerNote" in tag:
            continue
        exif[tag] = str(value)

    gps = _get_gps_from_tags(tags) if tags else None

    return {
        "basic": basic,
        "exif": exif if exif else None,
        "gps": gps,
    }
