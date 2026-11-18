"""Live NASA FIRMS active-fire service. No sample-data fallback."""
import csv, io
from datetime import datetime, timezone
import httpx
from app.config import get_settings
from app.services.cache import cache
from app.services.resilience import arequest_with_retry, describe_transport_error

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
CACHE_TTL_SECONDS = 10 * 60

class FireDataUnavailableError(RuntimeError): pass

async def _fetch_live(days: int = 1, region: str = "world") -> list[dict]:
    key=get_settings().firms_api_key
    if not key: raise FireDataUnavailableError("FIRMS_API_KEY is required for live fire data.")
    url=f"{FIRMS_BASE}/{key}/VIIRS_NOAA21_NRT/{region}/{max(1,min(days,5))}"
    try:
        r = await arequest_with_retry("GET", url, timeout=httpx.Timeout(90.0, connect=15.0), attempts=3, backoff=2.0)
    except httpx.TransportError as e:
        raise FireDataUnavailableError(describe_transport_error(e, "NASA FIRMS")) from e
    if r.status_code == 429:
        raise FireDataUnavailableError("NASA FIRMS rate limit reached. Please wait a few minutes and try again.")
    if not r.is_success:
        raise FireDataUnavailableError(f"NASA FIRMS returned HTTP {r.status_code}. Please try again shortly.")
    if "latitude" not in r.text[:500].lower():
        raise FireDataUnavailableError(f"NASA FIRMS did not return fire data: {r.text[:200].strip()}")
    fires=[]
    for row in csv.DictReader(io.StringIO(r.text)):
        try:
            acq_date=row.get("acq_date",""); acq_time=row.get("acq_time","")
            hhmm=acq_time.zfill(4)[:4]
            iso=f"{acq_date}T{hhmm[:2]}:{hhmm[2:]}:00Z" if acq_date else None
            fires.append({"latitude":float(row["latitude"]),"longitude":float(row["longitude"]),"brightness":float(row.get("bright_ti4") or row.get("brightness") or 0),"confidence":row.get("confidence","unknown"),"satellite":row.get("satellite","VIIRS_NOAA21"),"acq_time":iso})
        except (KeyError,ValueError): continue
    return fires

async def get_active_fires(days:int=1)->dict:
    fires,fetched_at,from_cache=await cache.get_or_fetch(f"firms:{days}",CACHE_TTL_SECONDS,lambda:_fetch_live(days))
    return {"fires":fires,"is_demo":False,"source":"NASA FIRMS (VIIRS NOAA-21 NRT)","fetched_at":datetime.fromtimestamp(fetched_at,tz=timezone.utc).isoformat(),"from_cache":from_cache}
