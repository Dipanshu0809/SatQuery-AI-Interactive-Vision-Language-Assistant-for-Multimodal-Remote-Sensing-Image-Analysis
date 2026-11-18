import asyncio
import json
import logging
import math

from app.services.cdse_service import raw_indices
from app.services.events_service import get_earthquakes, get_natural_events
from app.services.firms_service import get_active_fires
from app.services.gemini_service import GeminiService, GeminiUnavailableError
from app.services.weather_service import get_weather

logger = logging.getLogger("satquery.earth_analyst")

ANALYST_PROMPT = """You are SatQuery AI, a remote-sensing analyst. Summarize only the retrieved evidence below. Never invent measurements. Distinguish satellite acquisition time from current weather/event retrieval time. If evidence is missing (see "unavailable_sources"), say so briefly. Location: {location}. Evidence JSON: {evidence}. Return concise plain prose."""

EMPTY_WEATHER = {
    "temperature_c": None, "humidity_pct": None, "wind_kmh": None, "precipitation_mm": None,
    "cloud_cover_pct": None, "pressure_hpa": None, "condition": "Unavailable",
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _near(items, lat, lon, radius_km):
    out = []
    for e in items or []:
        try:
            if e.get("latitude") is not None and e.get("longitude") is not None and \
                    haversine_km(lat, lon, float(e["latitude"]), float(e["longitude"])) <= radius_km:
                out.append(e)
        except (TypeError, ValueError):
            continue
    return out


async def gather_evidence(lat, lon, radius_km=150):
    """Fetch every live source in parallel. A source that fails is listed in
    "unavailable_sources" instead of failing the whole investigation."""
    names = ["NASA FIRMS active fires", "Open-Meteo weather", "Copernicus Sentinel-2", "USGS earthquakes", "NASA EONET events"]
    results = await asyncio.gather(
        get_active_fires(days=1),
        get_weather(lat, lon),
        asyncio.to_thread(raw_indices, lat, lon, None, 30),
        get_earthquakes(),
        get_natural_events(),
        return_exceptions=True,
    )
    unavailable = []
    for name, res in zip(names, results):
        if isinstance(res, BaseException):
            logger.warning("Evidence source failed: %s: %s", name, res)
            unavailable.append({"source": name, "reason": str(res)[:300] or type(res).__name__})
    fires, weather, sat, quakes, natural = (None if isinstance(r, BaseException) else r for r in results)

    if sat is not None:
        sat_stats, sat_scene = sat
        sentinel2 = {**sat_stats, "scene": sat_scene, "available": True}
    else:
        sentinel2 = {"available": False, "reason": unavailable[[u["source"] for u in unavailable].index("Copernicus Sentinel-2")]["reason"]}

    return {
        "location": {"latitude": lat, "longitude": lon},
        "sentinel2": sentinel2,
        "nearby_fires": _near(fires["fires"], lat, lon, radius_km) if fires else [],
        "fire_source": fires["source"] if fires else "NASA FIRMS (unavailable right now)",
        "weather": weather["weather"] if weather else dict(EMPTY_WEATHER),
        "weather_source": weather["source"] if weather else "Open-Meteo (unavailable right now)",
        "earthquakes": _near(quakes["events"], lat, lon, radius_km) if quakes else [],
        "natural_events": _near(natural["events"], lat, lon, radius_km) if natural else [],
        "event_sources": [q["source"] for q in (quakes, natural) if q],
        "unavailable_sources": unavailable,
    }


def evidence_summary(evidence: dict, location: str) -> str:
    """Plain, factual summary built from the evidence when Gemini cannot answer."""
    parts = [f"Live evidence for {location}:"]
    s2 = evidence.get("sentinel2") or {}
    if s2.get("available"):
        scene = s2.get("scene") or {}
        parts.append(
            f"Sentinel-2 scene from {scene.get('datetime', 'an unknown date')} (cloud {scene.get('cloud_cover', 'n/a')}%) "
            f"gives mean NDVI {s2.get('mean_ndvi', 0):.3f}, NDWI {s2.get('mean_ndwi', 0):.3f} and NDBI {s2.get('mean_ndbi', 0):.3f}."
        )
    parts.append(f"{len(evidence.get('nearby_fires') or [])} active fire detection(s) within 150 km in the last 24 hours.")
    w = evidence.get("weather") or {}
    if w.get("temperature_c") is not None:
        parts.append(f"Current weather: {w.get('condition')}, {w.get('temperature_c')}°C, wind {w.get('wind_kmh')} km/h.")
    parts.append(
        f"{len(evidence.get('earthquakes') or [])} earthquake(s) and {len(evidence.get('natural_events') or [])} "
        "open NASA EONET event(s) nearby."
    )
    missing = [u["source"] for u in evidence.get("unavailable_sources") or []]
    if missing:
        parts.append("Not available right now: " + ", ".join(missing) + ".")
    return " ".join(parts)


async def analyze_location(lat, lon, objective=None, evidence=None):
    if evidence is None:
        evidence = await gather_evidence(lat, lon)
    location = objective or f"{lat:.4f}, {lon:.4f}"
    ai_note = None
    try:
        gemini = GeminiService()
        summary = await asyncio.to_thread(
            gemini.generate_text, [ANALYST_PROMPT.format(location=location, evidence=json.dumps(evidence, default=str)[:30000])]
        )
    except GeminiUnavailableError as e:
        logger.warning("Gemini unavailable for Earth Analyst; using evidence summary: %s", e)
        ai_note = str(e)
        summary = evidence_summary(evidence, location) + f" (AI narrative unavailable: {e})"
    return {"summary": summary, "evidence": evidence, "is_demo": False, "ai_note": ai_note}
