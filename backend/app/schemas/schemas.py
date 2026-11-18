"""Pydantic request/response schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: str = "ok"
    mode: str  # always "real" in the live build
    gemini_connected: bool
    cv_available: bool = True
    live_fires_connected: bool = False
    weather_connected: bool = True


# ---------- Analysis ----------

class LandCoverBreakdown(BaseModel):
    vegetation: float | None = None
    water: float | None = None
    built_up: float | None = None
    bare_land: float | None = None


class CVSceneMetrics(BaseModel):
    image_width: int | None = None
    image_height: int | None = None
    brightness: float | None = None
    contrast: float | None = None
    edge_density_pct: float | None = None
    candidate_count: int = 0
    candidate_regions: list[dict] = Field(default_factory=list)
    scene_profile: str | None = None
    method: str | None = None
    overlay_url: str | None = None


class AnalysisResponse(BaseModel):
    id: str
    filename: str
    summary: str
    land_cover: LandCoverBreakdown | None = None
    observations: list[str] = Field(default_factory=list)
    confidence: float | None = None
    is_demo: bool
    image_url: str | None = None
    created_at: datetime
    cv_metrics: CVSceneMetrics | None = None

    class Config:
        from_attributes = True


# ---------- Ask ----------

class ChatMessageIn(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str
    analysis_id: str | None = None
    history: list[ChatMessageIn] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    is_demo: bool


# ---------- Change detection ----------

class ChangeDetectionResponse(BaseModel):
    id: str
    change_percentage: float | None = None
    changed_regions: list[str] = Field(default_factory=list)
    summary: str
    is_demo: bool
    heatmap_url: str | None = None
    image_a_url: str | None = None
    image_b_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- History ----------

class HistoryItem(BaseModel):
    id: str
    filename: str
    analysis_type: str
    timestamp: datetime
    location: str | None = None
    summary: str | None = None
    status: str

    class Config:
        from_attributes = True


class HistoryDetail(HistoryItem):
    land_cover: LandCoverBreakdown | None = None
    observations: list[str] = Field(default_factory=list)
    confidence: float | None = None
    change_percentage: float | None = None
    changed_regions: list[str] = Field(default_factory=list)
    is_demo: bool = False


# ---------- Report ----------

class ReportRequest(BaseModel):
    analysis_id: str
