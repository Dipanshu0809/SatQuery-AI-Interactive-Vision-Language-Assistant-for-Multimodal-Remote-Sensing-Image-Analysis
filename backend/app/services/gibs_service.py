"""NASA GIBS/Worldview live imagery helpers. Public imagery requires no API key."""
from datetime import datetime, timezone
from urllib.parse import urlencode

GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"

# Current near-real-time/available layers exposed by NASA Worldview/GIBS.
TRUE_COLOR_LAYER = "VIIRS_SNPP_CorrectedReflectance_TrueColor"
NIGHT_LIGHT_LAYER = "VIIRS_SNPP_DayNightBand_At_Sensor_Radiance"
FIRE_LAYER = "VIIRS_SNPP_Thermal_Anomalies_375m_All"


def wms_image_url(layer: str, bbox: tuple[float, float, float, float], width: int = 900, height: int = 520, date: str | None = None) -> str:
    # WMS 1.1.1 uses lon/lat order for EPSG:4326 and is directly consumable by browsers.
    params = {
        "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap",
        "LAYERS": layer, "STYLES": "default", "SRS": "EPSG:4326",
        "BBOX": ",".join(str(v) for v in bbox), "WIDTH": width, "HEIGHT": height,
        "FORMAT": "image/png", "TRANSPARENT": "true",
    }
    if date:
        params["TIME"] = date
    return f"{GIBS_WMS}?{urlencode(params)}"


def point_bbox(lat: float, lon: float, size_deg: float = 1.0) -> tuple[float, float, float, float]:
    h = size_deg / 2
    return (lon - h, lat - h, lon + h, lat + h)


def metadata(source: str, layer: str) -> dict:
    return {"source": source, "layer": layer, "fetched_at": datetime.now(timezone.utc).isoformat(), "live": True}
