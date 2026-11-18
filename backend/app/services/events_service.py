"""Live public event feeds: USGS earthquakes and NASA EONET natural events."""
from datetime import datetime, timezone
import httpx
from app.services.cache import cache
from app.services.resilience import arequest_with_retry, describe_transport_error

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events/geojson"

class EventsUnavailableError(RuntimeError):
    pass


async def _get_json(url: str, service: str, params: dict | None = None) -> dict:
    try:
        r = await arequest_with_retry("GET", url, params=params, timeout=httpx.Timeout(40.0, connect=15.0), attempts=3)
    except httpx.TransportError as e:
        raise EventsUnavailableError(describe_transport_error(e, service)) from e
    if not r.is_success:
        raise EventsUnavailableError(f"{service} returned HTTP {r.status_code}. Please try again shortly.")
    return r.json()


async def get_earthquakes() -> dict:
    data, _, _ = await cache.get_or_fetch("usgs:all_day", 5 * 60, lambda: _get_json(USGS_URL, "USGS earthquake feed"))
    events=[]
    for f in data.get("features", []):
        p=f.get("properties",{}); g=f.get("geometry",{}); c=(g.get("coordinates") or [None,None,None])
        if c[0] is None or c[1] is None: continue
        events.append({"id":f.get("id"),"type":"earthquake","title":p.get("title"),"magnitude":p.get("mag"),"time":datetime.fromtimestamp(p["time"]/1000,tz=timezone.utc).isoformat() if p.get("time") else None,"latitude":c[1],"longitude":c[0],"depth_km":c[2],"url":p.get("url")})
    return {"events":events,"source":"USGS Earthquake Hazards Program","fetched_at":datetime.now(timezone.utc).isoformat()}

async def get_natural_events(limit: int = 100) -> dict:
    params={"status":"open","limit":limit}
    data, _, _ = await cache.get_or_fetch(f"eonet:{limit}", 15 * 60, lambda: _get_json(EONET_URL, "NASA EONET", params))
    events=[]
    for f in data.get("features",[]):
        geom=f.get("geometry") or [{}]
        g=geom[-1] if isinstance(geom,list) else geom
        coords=g.get("coordinates") if g else None
        lat=lon=None
        if isinstance(coords,list) and len(coords)>=2 and isinstance(coords[0],(int,float)):
            lon,lat=coords[0],coords[1]
        events.append({"id":f.get("id"),"type":"natural_event","title":f.get("title"),"category":(f.get("categories") or [{}])[0].get("title"),"latitude":lat,"longitude":lon,"time":g.get("date") if g else None,"source":((f.get("sources") or [{}])[0].get("url"))})
    return {"events":events,"source":"NASA EONET","fetched_at":datetime.now(timezone.utc).isoformat()}
