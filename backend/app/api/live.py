from fastapi import APIRouter, HTTPException
from app.schemas.live_schemas import FiresResponse, LiveSummaryResponse, WeatherResponse
from app.services.firms_service import get_active_fires
from app.services.weather_service import get_weather
from app.services.events_service import get_earthquakes, get_natural_events

router=APIRouter()

def _err(e): return HTTPException(status_code=503,detail=str(e))

@router.get('/live/fires',response_model=FiresResponse)
async def live_fires(days:int=1):
    try:return FiresResponse(**await get_active_fires(days))
    except Exception as e:raise _err(e)

@router.get('/live/weather',response_model=WeatherResponse)
async def live_weather(lat:float,lon:float):
    try:return WeatherResponse(**await get_weather(lat,lon))
    except Exception as e:raise _err(e)

@router.get('/live/summary',response_model=LiveSummaryResponse)
async def live_summary():
    try:
        fires=await get_active_fires(1)
        return LiveSummaryResponse(active_fires=len(fires['fires']),fires_is_demo=False,fires_source=fires['source'],fetched_at=fires['fetched_at'])
    except Exception as e:raise _err(e)

@router.get('/live/earthquakes')
async def live_earthquakes():
    try:return await get_earthquakes()
    except Exception as e:raise _err(e)

@router.get('/live/natural-events')
async def live_natural_events():
    try:return await get_natural_events()
    except Exception as e:raise _err(e)
