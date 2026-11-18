"""Live Open-Meteo weather service. No fabricated fallback data."""
from datetime import datetime, timezone
import httpx
from app.services.cache import cache
from app.services.resilience import arequest_with_retry, describe_transport_error

OPEN_METEO_URL="https://api.open-meteo.com/v1/forecast"
CACHE_TTL_SECONDS=5*60
class WeatherUnavailableError(RuntimeError): pass

def _weather_code_label(code):
    mapping={0:"Clear sky",1:"Mostly clear",2:"Partly cloudy",3:"Overcast",45:"Fog",48:"Fog",51:"Light drizzle",53:"Drizzle",55:"Heavy drizzle",61:"Light rain",63:"Moderate rain",65:"Heavy rain",71:"Light snow",73:"Snow",75:"Heavy snow",80:"Rain showers",81:"Rain showers",82:"Heavy rain showers",95:"Thunderstorm",96:"Thunderstorm with hail",99:"Thunderstorm with hail"}
    return mapping.get(code,"Unknown")

async def _fetch_live(lat,lon):
    params={"latitude":lat,"longitude":lon,"current":"temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,cloud_cover,pressure_msl,weather_code","timezone":"auto"}
    try:
        r = await arequest_with_retry("GET", OPEN_METEO_URL, params=params, timeout=httpx.Timeout(30.0, connect=15.0), attempts=3)
    except httpx.TransportError as e:
        raise WeatherUnavailableError(describe_transport_error(e, "Open-Meteo")) from e
    if not r.is_success:
        raise WeatherUnavailableError(f"Open-Meteo returned HTTP {r.status_code}. Please try again shortly.")
    current = r.json().get("current", {})
    return {"temperature_c":current.get("temperature_2m"),"humidity_pct":current.get("relative_humidity_2m"),"wind_kmh":current.get("wind_speed_10m"),"precipitation_mm":current.get("precipitation"),"cloud_cover_pct":current.get("cloud_cover"),"pressure_hpa":current.get("pressure_msl"),"condition":_weather_code_label(current.get("weather_code"))}

async def get_weather(lat,lon):
    weather,fetched_at,from_cache=await cache.get_or_fetch(f"weather:{round(lat,3)}:{round(lon,3)}",CACHE_TTL_SECONDS,lambda:_fetch_live(lat,lon))
    return {"weather":weather,"is_demo":False,"source":"Open-Meteo current conditions","fetched_at":datetime.fromtimestamp(fetched_at,tz=timezone.utc).isoformat(),"from_cache":from_cache}
