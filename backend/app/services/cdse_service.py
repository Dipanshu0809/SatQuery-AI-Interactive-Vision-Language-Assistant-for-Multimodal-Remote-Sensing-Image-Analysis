"""Live Sentinel-2 L2A access through Copernicus Data Space Sentinel Hub APIs."""
from __future__ import annotations

import io
import math
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import httpx
import numpy as np
import rasterio
from rasterio.io import MemoryFile

from app.config import get_settings
from app.services.resilience import MemoCache, describe_transport_error, make_key, request_with_retry

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
BASE_URL = "https://sh.dataspace.copernicus.eu"
PROCESS_URL = f"{BASE_URL}/api/v1/process"
CATALOG_URL = f"{BASE_URL}/catalog/v1/search"

class SatelliteUnavailableError(RuntimeError):
    pass


def _require_credentials() -> tuple[str, str]:
    s = get_settings()
    if not s.cdse_client_id or not s.cdse_client_secret:
        raise SatelliteUnavailableError(
            "Copernicus Data Space credentials are required. Set CDSE_CLIENT_ID and CDSE_CLIENT_SECRET in backend/.env."
        )
    return s.cdse_client_id, s.cdse_client_secret


@lru_cache(maxsize=1)
def _token_cached() -> tuple[str, float]:
    client_id, client_secret = _require_credentials()
    try:
        r = request_with_retry(
            "POST", TOKEN_URL, timeout=httpx.Timeout(30.0, connect=15.0),
            data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except httpx.TransportError as e:
        raise SatelliteUnavailableError(describe_transport_error(e, "Copernicus login")) from e
    if r.status_code in (400, 401, 403):
        raise SatelliteUnavailableError(
            "Copernicus rejected the login. Check CDSE_CLIENT_ID and CDSE_CLIENT_SECRET in backend/.env."
        )
    if not r.is_success:
        raise SatelliteUnavailableError(f"Copernicus login failed ({r.status_code}). Please try again shortly.")
    data = r.json()
    expires = float(data.get("expires_in", 3600))
    return data["access_token"], datetime.now(timezone.utc).timestamp() + expires - 60


def _token() -> str:
    try:
        token, expiry = _token_cached()
        if datetime.now(timezone.utc).timestamp() < expiry:
            return token
    except SatelliteUnavailableError:
        _token_cached.cache_clear()
        raise
    _token_cached.cache_clear()
    token, _ = _token_cached()
    return token


def _bbox(lat: float, lon: float, size_deg: float = 0.04) -> list[float]:
    half = size_deg / 2
    cos_lat = max(0.2, abs(math.cos(math.radians(lat))))
    lon_half = half / cos_lat
    return [lon - lon_half, lat - half, lon + lon_half, lat + half]


def _time_range(days_back: int, end: datetime | None = None) -> tuple[str, str]:
    # Aligned to the hour so repeated requests within the hour hit the cache.
    end = end or datetime.now(timezone.utc).replace(minute=59, second=59, microsecond=0)
    start = end - timedelta(days=days_back)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ"), end.strftime("%Y-%m-%dT%H:%M:%SZ")


_CATALOG_CACHE = MemoCache(max_items=256)
_PROCESS_CACHE = MemoCache(max_items=96)
CATALOG_TTL_S = 30 * 60
PROCESS_TTL_S = 60 * 60


def _post_with_auth(url: str, body: dict, timeout: httpx.Timeout, service: str) -> httpx.Response:
    """POST to Sentinel Hub with retries; refreshes the token once on 401."""
    try:
        headers = {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}
        r = request_with_retry("POST", url, json=body, headers=headers, timeout=timeout, attempts=3, backoff=1.5)
        if r.status_code == 401:
            _token_cached.cache_clear()
            headers["Authorization"] = f"Bearer {_token()}"
            r = request_with_retry("POST", url, json=body, headers=headers, timeout=timeout, attempts=2, backoff=1.5)
        return r
    except httpx.TransportError as e:
        raise SatelliteUnavailableError(describe_transport_error(e, service)) from e


def _catalog_search(bbox: list[float], start: str, end: str, limit: int = 100) -> list[dict]:
    body = {
        "bbox": [round(v, 6) for v in bbox],
        "datetime": f"{start}/{end}",
        "collections": ["sentinel-2-l2a"],
        "limit": max(1, min(int(limit), 100)),
    }
    key = make_key("catalog", body)
    cached = _CATALOG_CACHE.get(key)
    if cached is not None:
        return cached
    r = _post_with_auth(CATALOG_URL, body, httpx.Timeout(60.0, connect=15.0), "Copernicus Sentinel-2 catalog")
    if r.status_code == 429:
        raise SatelliteUnavailableError("Copernicus rate limit reached. Please wait a minute and try again.")
    if not r.is_success:
        # Surface Copernicus' own explanation instead of a bare "400 Bad Request".
        raise SatelliteUnavailableError(
            f"Sentinel-2 catalog search failed ({r.status_code}) for datetime "
            f"'{body['datetime']}': {r.text[:500]}"
        )
    features = r.json().get("features", [])
    _CATALOG_CACHE.set(key, features, CATALOG_TTL_S)
    return features


def search_scenes(lat: float, lon: float, start_date: str, end_date: str, limit: int = 20) -> list[dict]:
    """Scenes in the window, newest first (the catalog does not guarantee an order)."""
    start_date, end_date = str(start_date)[:10], str(end_date)[:10]
    features = _catalog_search(_bbox(lat, lon), f"{start_date}T00:00:00Z", f"{end_date}T23:59:59Z", 100)
    scenes = []
    for f in features:
        p = f.get("properties", {})
        scenes.append({
            "id": f.get("id"),
            "datetime": f.get("properties", {}).get("datetime") or f.get("datetime"),
            "cloud_cover": p.get("eo:cloud_cover"),
            "platform": p.get("platform"),
            "constellation": p.get("constellation", "Sentinel-2"),
            "bbox": f.get("bbox"),
        })
    scenes.sort(key=lambda sc: sc.get("datetime") or "", reverse=True)
    return scenes[:limit]


def _pick_scene(scenes: list[dict]) -> dict:
    """Newest scene the processing filter will actually use (cloud cover <= 80%)."""
    for sc in scenes:
        cc = sc.get("cloud_cover")
        if cc is None or cc <= 80:
            return sc
    return scenes[0]


def _process(lat: float, lon: float, start: str, end: str, evalscript: str, width: int = 512, height: int = 512, fmt: str = "image/png") -> bytes:
    body = {
        "input": {
            "bounds": {"bbox": [round(v, 6) for v in _bbox(lat, lon)], "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {"from": start, "to": end},
                    "maxCloudCoverage": 80,
                    "mosaickingOrder": "mostRecent",
                },
            }],
        },
        "output": {"width": width, "height": height, "responses": [{"identifier": "default", "format": {"type": fmt}}]},
        "evalscript": evalscript,
    }
    key = make_key("process", body)
    cached = _PROCESS_CACHE.get(key)
    if cached is not None:
        return cached
    r = _post_with_auth(PROCESS_URL, body, httpx.Timeout(120.0, connect=15.0), "Copernicus Sentinel-2 processing")
    if r.status_code == 429:
        raise SatelliteUnavailableError("Copernicus processing quota or rate limit reached. Please wait a minute and try again.")
    if not r.is_success:
        raise SatelliteUnavailableError(f"Sentinel-2 processing request failed ({r.status_code}): {r.text[:500]}")
    _PROCESS_CACHE.set(key, r.content, PROCESS_TTL_S)
    return r.content


RGB_SCRIPT = """//VERSION=3\nfunction setup(){return {input:[{bands:[\"B04\",\"B03\",\"B02\",\"SCL\"]}],output:{bands:4,sampleType:\"AUTO\"}}}\nfunction evaluatePixel(s){if(s.SCL===3||s.SCL===8||s.SCL===9||s.SCL===10||s.SCL===11)return [0,0,0,0];return [2.5*s.B04,2.5*s.B03,2.5*s.B02,1];}"""
RAW_SCRIPT = """//VERSION=3\nfunction setup(){return {input:[{bands:[\"B03\",\"B04\",\"B08\",\"B11\"]}],output:{bands:4,sampleType:\"FLOAT32\"}}}\nfunction evaluatePixel(s){return [s.B03,s.B04,s.B08,s.B11];}"""
NDVI_SCRIPT = """//VERSION=3\nfunction setup(){return {input:[{bands:[\"B04\",\"B08\"]}],output:{bands:1,sampleType:\"FLOAT32\"}}}\nfunction evaluatePixel(s){return [(s.B08-s.B04)/(s.B08+s.B04+1e-6)];}"""
NDWI_SCRIPT = """//VERSION=3\nfunction setup(){return {input:[{bands:[\"B03\",\"B08\"]}],output:{bands:1,sampleType:\"FLOAT32\"}}}\nfunction evaluatePixel(s){return [(s.B03-s.B08)/(s.B03+s.B08+1e-6)];}"""


def latest_scene(lat: float, lon: float, days_back: int = 30) -> dict:
    start, end = _time_range(days_back)
    scenes = search_scenes(lat, lon, start[:10], end[:10], limit=100)
    if not scenes:
        raise SatelliteUnavailableError("No Sentinel-2 L2A acquisition was found for this location and time window.")
    return _pick_scene(scenes)


def scene_image(lat: float, lon: float, date: str | None = None, days_back: int = 30) -> tuple[bytes, dict]:
    if date:
        start = f"{date}T00:00:00Z"
        end = f"{date}T23:59:59Z"
        scenes = search_scenes(lat, lon, date, date, limit=10)
    else:
        start, end = _time_range(days_back)
        scenes = search_scenes(lat, lon, start[:10], end[:10], limit=100)
    if not scenes:
        raise SatelliteUnavailableError("No Sentinel-2 L2A acquisition was found for the requested location/date.")
    scene = _pick_scene(scenes)
    image = _process(lat, lon, start, end, RGB_SCRIPT, fmt="image/png")
    return image, scene


def raw_indices(lat: float, lon: float, date: str | None = None, days_back: int = 30) -> tuple[dict, dict]:
    if date:
        start = f"{date}T00:00:00Z"; end = f"{date}T23:59:59Z"
        scenes = search_scenes(lat, lon, date, date, limit=10)
    else:
        start, end = _time_range(days_back)
        scenes = search_scenes(lat, lon, start[:10], end[:10], limit=100)
    if not scenes:
        raise SatelliteUnavailableError("No Sentinel-2 L2A acquisition was found for the requested location/date.")
    scene = _pick_scene(scenes)
    data = _process(lat, lon, start, end, RAW_SCRIPT, width=256, height=256, fmt="image/tiff")
    with MemoryFile(data) as mem:
        with mem.open() as ds:
            arr = ds.read().astype(np.float32)
    green, red, nir, swir = arr
    ndvi = (nir - red) / (nir + red + 1e-6)
    ndwi = (green - nir) / (green + nir + 1e-6)
    ndbi = (swir - nir) / (swir + nir + 1e-6)
    valid = np.isfinite(ndvi) & np.isfinite(ndwi) & np.isfinite(ndbi)
    if not np.any(valid):
        raise SatelliteUnavailableError("Sentinel-2 returned no valid pixels for the requested scene.")
    stats = {
        "mean_ndvi": float(np.nanmean(ndvi[valid])),
        "mean_ndwi": float(np.nanmean(ndwi[valid])),
        "mean_ndbi": float(np.nanmean(ndbi[valid])),
        "vegetation_pct": float(np.mean(ndvi[valid] > 0.3) * 100),
        "water_pct": float(np.mean(ndwi[valid] > 0.2) * 100),
        "built_up_pct": float(np.mean(ndbi[valid] > 0.1) * 100),
        "valid_pixels": int(np.sum(valid)),
    }
    return stats, scene


def index_image(lat: float, lon: float, index: str, date: str | None = None, days_back: int = 30) -> tuple[bytes, dict]:
    if date:
        start = f"{date}T00:00:00Z"; end = f"{date}T23:59:59Z"
        scenes = search_scenes(lat, lon, date, date, limit=10)
    else:
        start, end = _time_range(days_back)
        scenes = search_scenes(lat, lon, start[:10], end[:10], limit=100)
    if not scenes:
        raise SatelliteUnavailableError("No Sentinel-2 L2A acquisition was found for the requested location/date.")
    scene = _pick_scene(scenes)
    if index == "ndvi": script = NDVI_SCRIPT
    elif index == "ndwi": script = NDWI_SCRIPT
    else: raise ValueError("index must be ndvi or ndwi")
    return _process(lat, lon, start, end, script, width=512, height=512, fmt="image/tiff"), scene
