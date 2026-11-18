import logging
import os
import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import analyze, ask, change_detection, earth, health, history, live, map_command, mission, monitoring, report, satellite
from app.config import get_settings
from app.database.db import init_db
from app.services.monitoring_worker import monitoring_loop
from app.services.cdse_service import SatelliteUnavailableError
from app.services.firms_service import FireDataUnavailableError
from app.services.gemini_service import GeminiUnavailableError
from app.services.weather_service import WeatherUnavailableError
from app.services.events_service import EventsUnavailableError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("satquery")

settings = get_settings()

# Create runtime folders before anything uses them. Git does not keep empty
# folders, so a fresh clone may not have uploads/ (StaticFiles would crash).
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(os.path.join(BACKEND_DIR, "reports"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("SatQuery AI backend started in LIVE mode")
    monitor_task = asyncio.create_task(monitoring_loop())
    yield
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="SatQuery AI API",
    description="Backend for SatQuery AI — a multimodal remote sensing assistant.",
    version="1.0.0",
    lifespan=lifespan,
)

# Catch-all for unexpected errors. It is registered BEFORE CORSMiddleware so it sits
# inside it: the 500 response then carries CORS headers and the browser can read it.
# (A handler registered with @app.exception_handler(Exception) runs outside CORS, so the
# browser blocked its response and the UI wrongly said "Could not reach the backend".)
@app.middleware("http")
async def catch_unhandled_errors(request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again."},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(ask.router, prefix="/api", tags=["Ask SatQuery"])
app.include_router(change_detection.router, prefix="/api", tags=["Change Detection"])
app.include_router(report.router, prefix="/api", tags=["Reports"])
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(live.router, prefix="/api", tags=["Live Earth"])
app.include_router(earth.router, prefix="/api", tags=["Earth Intelligence"])
app.include_router(mission.router, prefix="/api", tags=["Mission Mode"])
app.include_router(map_command.router, prefix="/api", tags=["Map Copilot"])
app.include_router(monitoring.router, prefix="/api", tags=["Monitoring"])
app.include_router(satellite.router, prefix="/api", tags=["Satellite Data"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    # Ensure clients always get a clean {"detail": "..."} shape, never a stack trace.
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def live_source_unavailable_handler(request, exc: Exception):
    # A required live source (Sentinel-2, Gemini, FIRMS, weather) failed: say which one and why.
    logger.warning("Live source unavailable on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


for _exc_class in (SatelliteUnavailableError, GeminiUnavailableError, FireDataUnavailableError, WeatherUnavailableError, EventsUnavailableError):
    app.add_exception_handler(_exc_class, live_source_unavailable_handler)


@app.exception_handler(httpx.HTTPError)
async def upstream_http_error_handler(request, exc: httpx.HTTPError):
    # Report only the host: some upstream URLs (e.g. NASA FIRMS) contain the API key.
    try:
        host = exc.request.url.host
    except RuntimeError:
        host = "an upstream service"
    if isinstance(exc, httpx.HTTPStatusError):
        detail = f"{host} returned {exc.response.status_code}: {exc.response.text[:300]}"
    else:
        detail = f"Could not reach {host}: {type(exc).__name__}"
    logger.warning("Upstream error on %s: %s", request.url.path, detail)
    return JSONResponse(status_code=502, content={"detail": detail})
