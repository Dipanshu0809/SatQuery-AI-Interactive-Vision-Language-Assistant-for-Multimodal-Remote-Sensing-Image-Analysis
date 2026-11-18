from app.services.earth_analyst_service import analyze_location, gather_evidence
from app.services.earth_change_index import compute_change_index
from app.services.map_copilot_service import KNOWN_LOCATIONS


def resolve_location(objective):
    t = objective.lower()
    for name, (lat, lon) in KNOWN_LOCATIONS.items():
        if name in t:
            return lat, lon, name.title()
    return None


async def run_mission(objective, latitude=None, longitude=None):
    steps = []

    def step(label, status="done", detail=None):
        steps.append({"label": label, "status": status, "detail": detail})

    lat, lon, label = latitude, longitude, None
    if lat is None or lon is None:
        r = resolve_location(objective)
        if not r:
            step("Location identified", "failed", "Provide coordinates or a recognizable place name.")
            return {"steps": steps, "report": None, "is_demo": False}
        lat, lon, label = r
        step("Location identified", detail=f"Live geocoded context: {label}")
    else:
        step("Location identified", detail=f"Using coordinates {lat:.5f}, {lon:.5f}")

    # One parallel pass over every live source (satellite, fires, weather, quakes, events).
    ev = await gather_evidence(lat, lon)
    reasons = {u["source"]: u["reason"] for u in ev.get("unavailable_sources", [])}

    s2 = ev.get("sentinel2") or {}
    if s2.get("available"):
        scene = s2.get("scene") or {}
        step("Sentinel-2 acquisition found", detail=f"{scene.get('datetime')} · cloud {scene.get('cloud_cover')}%")
        step(
            "Multispectral indices computed",
            detail=f"NDVI {s2['mean_ndvi']:.3f} · NDWI {s2['mean_ndwi']:.3f} · NDBI {s2['mean_ndbi']:.3f}",
        )
    else:
        step("Sentinel-2 acquisition found", "failed", reasons.get("Copernicus Sentinel-2", "Satellite data unavailable."))

    event_failures = [n for n in ("NASA FIRMS active fires", "USGS earthquakes", "NASA EONET events") if n in reasons]
    step(
        "Live events checked",
        "warning" if event_failures else "done",
        f"{len(ev['nearby_fires'])} fires · {len(ev['earthquakes'])} earthquakes · {len(ev['natural_events'])} NASA EONET events"
        + (f" (unavailable: {', '.join(event_failures)})" if event_failures else ""),
    )
    if "Open-Meteo weather" in reasons:
        step("Current weather checked", "warning", reasons["Open-Meteo weather"])
    else:
        step("Current weather checked", detail=f"{ev['weather'].get('condition')} · {ev['weather'].get('temperature_c')}°C")

    if s2.get("available"):
        change = compute_change_index(
            vegetation_delta_pct=abs(s2["mean_ndvi"]) * 100,
            water_delta_pct=abs(s2["mean_ndwi"]) * 100,
            built_up_delta_pct=max(0, s2["mean_ndbi"]) * 100,
            nearby_fire_count=len(ev["nearby_fires"]),
        )
        change["methodology"] = "Live Sentinel-2 L2A indices plus NASA FIRMS fire count; not an official government index."
        step("Earth Change Index computed", detail=f"{change['label']} ({change['score']}/100)")
    else:
        change = {
            "score": None,
            "label": "Not available",
            "components": {},
            "methodology": "The Earth Change Index needs Sentinel-2 indices, which could not be retrieved for this run. Try again in a minute.",
        }
        step("Earth Change Index computed", "failed", "Needs Sentinel-2 data")

    analysis = await analyze_location(lat, lon, objective=label or objective, evidence=ev)
    if analysis.get("ai_note"):
        step("AI investigation completed", "warning", "Gemini was busy, so a factual evidence summary was written instead")
    else:
        step("AI investigation completed", detail="Gemini grounded on retrieved live evidence")

    report = {
        "objective": objective,
        "location": {"latitude": lat, "longitude": lon, "label": label or f"{lat:.5f}, {lon:.5f}"},
        "summary": analysis["summary"],
        "evidence": ev,
        "change_index": change,
        "is_demo": False,
    }
    return {"steps": steps, "report": report, "is_demo": False}
