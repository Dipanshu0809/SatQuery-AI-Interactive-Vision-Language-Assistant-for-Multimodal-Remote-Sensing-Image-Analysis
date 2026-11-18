"""
Geospatial helper service.

Provides lightweight geospatial utilities for the Satellite Map page.
This baseline implementation does not call any paid satellite-imagery
API (Sentinel Hub, Planet, etc.) — it works with coordinates the user
selects on the map, and is structured so a real provider can be plugged
in later (see NOTES below).

NOTES for extending this service:
- To pull real Sentinel-2 / Landsat scenes for a bounding box, integrate
  the Copernicus Data Space Ecosystem API or Google Earth Engine here.
- Keep any provider API keys server-side, following the same pattern as
  GEMINI_API_KEY in app/config.py.
"""

from dataclasses import dataclass


@dataclass
class LocationContext:
    latitude: float
    longitude: float
    label: str


def describe_coordinates(lat: float, lon: float) -> LocationContext:
    """Produce a human-readable label for a coordinate pair.

    This baseline implementation returns a formatted coordinate string.
    Swap in a reverse-geocoding call (e.g. Nominatim) for place names.
    """
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    label = f"{abs(lat):.4f}\u00b0{lat_dir}, {abs(lon):.4f}\u00b0{lon_dir}"
    return LocationContext(latitude=lat, longitude=lon, label=label)


def bounding_box_area_km2(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Rough planar approximation of the area (km^2) of a lat/lon bounding
    box. Adequate for small regions of interest; not geodesically exact."""
    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.320 * abs(_cos_deg((lat1 + lat2) / 2))
    height_km = abs(lat2 - lat1) * km_per_deg_lat
    width_km = abs(lon2 - lon1) * km_per_deg_lon
    return round(height_km * width_km, 2)


def _cos_deg(deg: float) -> float:
    import math

    return math.cos(math.radians(deg))
