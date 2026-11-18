import asyncio
import logging
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.db import get_db
from app.models.records import Analysis
from app.schemas.schemas import AnalysisResponse
from app.services.cv_pipeline import analyze_scene
from app.services.gemini_service import GeminiService, GeminiUnavailableError
from app.services.image_processing import (
    InvalidImageError,
    resize_for_model,
    to_rgb_array,
    validate_and_load,
)
from app.services.land_cover import estimate_land_cover
from app.utils.file_utils import enforce_size_limit, safe_filename, save_upload

router = APIRouter()
logger = logging.getLogger("satquery.analyze")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    location: str | None = Form(None),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    file_bytes = await file.read()
    enforce_size_limit(file_bytes)

    try:
        img, meta = validate_and_load(file_bytes, file.content_type)
    except InvalidImageError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    saved_path = save_upload(file_bytes, file.filename or "upload.png")
    rgb = to_rgb_array(img)
    land_cover_fallback = estimate_land_cover(rgb)
    cv_metrics = analyze_scene(rgb)
    cv_overlay_name = safe_filename("cv_overlay.png")
    cv_overlay_path = os.path.join(settings.upload_dir, cv_overlay_name)
    with open(cv_overlay_path, "wb") as f:
        f.write(cv_metrics.pop("overlay_bytes"))
    cv_metrics["overlay_url"] = f"/uploads/{cv_overlay_name}"
    try:
        gemini = GeminiService()
        small = resize_for_model(img)
        from app.services.image_processing import image_to_bytes
        # Run the blocking Gemini call in a worker thread so other requests keep flowing.
        result = await asyncio.to_thread(gemini.analyze_image, image_to_bytes(small), "image/jpeg")
        result["observations"] = list(result.get("observations") or [])
        result["observations"].append(f"Computer vision scene profile: {cv_metrics['scene_profile']}")
        if not result.get("land_cover") or not any(v is not None for v in result["land_cover"].values()):
            result["land_cover"] = land_cover_fallback
    except GeminiUnavailableError as e:
        # Gemini is busy / out of quota: still return the real computer-vision analysis.
        logger.warning("Gemini unavailable for /analyze, returning CV-only result: %s", e)
        result = _cv_only_result(land_cover_fallback, cv_metrics, str(e))

    record = Analysis(
        filename=file.filename or "upload",
        analysis_type="analysis",
        summary=result.get("summary", ""),
        land_cover=result.get("land_cover"),
        observations=result.get("observations", []),
        confidence=result.get("confidence"),
        location=location,
        is_demo=False,
        status="completed",
        image_path=saved_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return AnalysisResponse(
        id=record.id,
        filename=record.filename,
        summary=record.summary,
        land_cover=record.land_cover,
        observations=record.observations or [],
        confidence=record.confidence,
        is_demo=record.is_demo,
        image_url=f"/uploads/{os.path.basename(saved_path)}",
        created_at=record.created_at,
        cv_metrics=cv_metrics,
    )


def _cv_only_result(land_cover: dict, cv: dict, reason: str) -> dict:
    """Deterministic analysis from the OpenCV pipeline, used when Gemini cannot answer."""
    ranked = sorted(((v or 0, k.replace("_", " ")) for k, v in land_cover.items()), reverse=True)
    dominant = ", ".join(f"{name} ~{pct:.0f}%" for pct, name in ranked[:2] if pct > 0) or "no dominant class"
    summary = (
        f"Computer-vision analysis: the image ({cv['image_width']}x{cv['image_height']} px) looks like a "
        f"{cv['scene_profile']} scene. Estimated cover: {dominant}. "
        f"{cv['candidate_count']} candidate regions were detected (edge density {cv['edge_density_pct']}%)."
    )
    return {
        "summary": summary,
        "land_cover": land_cover,
        "observations": [
            f"AI narrative unavailable right now: {reason}",
            "Showing the computer-vision (OpenCV colour/edge) results instead; run the analysis again later for the Gemini description.",
            f"Brightness {cv['brightness']}, contrast {cv['contrast']}, edge density {cv['edge_density_pct']}%.",
            f"Computer vision scene profile: {cv['scene_profile']}",
        ],
        "confidence": None,
    }
