"""Pydantic schemas for the Live Earth / Intelligence upgrade endpoints.
Kept in a separate file from schemas.py so the original file is untouched."""

from datetime import datetime
from pydantic import BaseModel, Field


class FireDetection(BaseModel):
    latitude: float
    longitude: float
    brightness: float | None = None
    confidence: str | None = None
    satellite: str | None = None
    acq_time: str | None = None


class FiresResponse(BaseModel):
    fires: list[FireDetection]
    is_demo: bool
    source: str
    fetched_at: str
    from_cache: bool


class WeatherData(BaseModel):
    temperature_c: float | None = None
    humidity_pct: float | None = None
    wind_kmh: float | None = None
    precipitation_mm: float | None = None
    cloud_cover_pct: float | None = None
    pressure_hpa: float | None = None
    condition: str | None = None


class WeatherResponse(BaseModel):
    weather: WeatherData
    is_demo: bool
    source: str
    fetched_at: str
    from_cache: bool


class LiveSummaryResponse(BaseModel):
    active_fires: int
    fires_is_demo: bool
    fires_source: str
    fetched_at: str


class EarthAnalyzeRequest(BaseModel):
    latitude: float
    longitude: float
    objective: str | None = None


class EarthAnalyzeResponse(BaseModel):
    summary: str
    evidence: dict
    is_demo: bool


class VegetationResponse(BaseModel):
    mean_index: float
    zones: dict
    heatmap_url: str
    is_proxy: bool = True
    note: str = "RGB-based vegetation proxy (ExG index) — not true satellite NDVI, which requires a near-infrared band."


class WaterIndexResponse(BaseModel):
    coverage_pct: float
    heatmap_url: str
    is_proxy: bool = True
    note: str = "RGB-based water-likelihood proxy — not true satellite NDWI, which requires a near-infrared band."


class ChangeIndexRequest(BaseModel):
    vegetation_delta_pct: float = 0.0
    water_delta_pct: float = 0.0
    built_up_delta_pct: float = 0.0
    latitude: float | None = None
    longitude: float | None = None


class ChangeIndexResponse(BaseModel):
    score: float
    label: str
    components: dict
    methodology: str


class MapCommandRequest(BaseModel):
    text: str


class MapCommandResponse(BaseModel):
    action: str
    layer: str | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    explanation: str
    is_demo: bool


class MissionRequest(BaseModel):
    objective: str
    latitude: float | None = None
    longitude: float | None = None


class MissionStep(BaseModel):
    label: str
    status: str
    detail: str | None = None


class MissionResponse(BaseModel):
    steps: list[MissionStep]
    report: dict | None
    is_demo: bool


class MonitoringTargetCreate(BaseModel):
    label: str
    latitude: float
    longitude: float
    radius_km: float = 100
    watch_fire: bool = True
    watch_vegetation_change: bool = False
    watch_flood: bool = False
    watch_water_change: bool = False
    watch_urban_expansion: bool = False


class MonitoringTargetResponse(BaseModel):
    id: str
    label: str
    latitude: float
    longitude: float
    radius_km: float
    watch_fire: bool
    watch_vegetation_change: bool
    watch_flood: bool
    watch_water_change: bool
    watch_urban_expansion: bool
    last_checked_at: datetime | None = None
    last_status: str
    last_detail: dict | list | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvestigationReportRequest(BaseModel):
    objective: str
    location: dict  # {latitude, longitude, label}
    summary: str
    evidence: dict
    change_index: dict
    is_demo: bool
