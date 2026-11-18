"""SQLAlchemy ORM models: Analysis, Conversation, Report."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, JSON

from app.database.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Analysis(Base):
    """A single analysis record: image analysis, ask, or change detection."""

    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=_uuid)
    filename = Column(String, nullable=False)
    analysis_type = Column(String, nullable=False)  # analysis | ask | change_detection
    summary = Column(Text, nullable=True)
    land_cover = Column(JSON, nullable=True)
    observations = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)
    changed_regions = Column(JSON, nullable=True)
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_demo = Column(Boolean, default=False)
    status = Column(String, default="completed")  # completed | failed | processing
    image_path = Column(String, nullable=True)
    image_path_b = Column(String, nullable=True)  # second image, for change detection
    created_at = Column(DateTime, default=_now)


class Conversation(Base):
    """A single chat turn tied to an analysis (Ask SatQuery)."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=_uuid)
    analysis_id = Column(String, nullable=True)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now)


class Report(Base):
    """A generated PDF report tied to an analysis."""

    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=_uuid)
    analysis_id = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=_now)


class MonitoringTarget(Base):
    """A user-defined area to watch for fire/change conditions. Checked
    manually via POST /api/monitoring/{id}/refresh in this version — no
    background scheduler is running by default."""

    __tablename__ = "monitoring_targets"

    id = Column(String, primary_key=True, default=_uuid)
    label = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_km = Column(Float, default=100)
    watch_fire = Column(Boolean, default=True)
    watch_vegetation_change = Column(Boolean, default=False)
    watch_flood = Column(Boolean, default=False)
    watch_water_change = Column(Boolean, default=False)
    watch_urban_expansion = Column(Boolean, default=False)
    last_checked_at = Column(DateTime, nullable=True)
    last_status = Column(String, default="unchecked")  # unchecked | clear | alert
    last_detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now)
