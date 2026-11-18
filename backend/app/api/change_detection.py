import asyncio
import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.db import get_db
from app.models.records import Analysis
from app.schemas.schemas import ChangeDetectionResponse
from app.services import change_detection as cd
from app.services.gemini_service import GeminiService, GeminiUnavailableError
from app.services.image_processing import (
    InvalidImageError,
    image_to_bytes,
    resize_for_model,
    to_rgb_array,
    validate_and_load,
)
from app.utils.file_utils import enforce_size_limit, safe_filename, save_upload

router = APIRouter()
logger = logging.getLogger("satquery.change_detection")


@router.post("/change-detection", response_model=ChangeDetectionResponse)
async def run_change_detection(
    image_a: UploadFile = File(...),
    image_b: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    settings = get_settings()

    bytes_a = await image_a.read()
    bytes_b = await image_b.read()
    enforce_size_limit(bytes_a)
    enforce_size_limit(bytes_b)

    try:
        img_a, _meta_a = validate_and_load(bytes_a, image_a.content_type)
        img_b, _meta_b = validate_and_load(bytes_b, image_b.content_type)
    except InvalidImageError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    path_a = save_upload(bytes_a, image_a.filename or "image_a.png")
    path_b = save_upload(bytes_b, image_b.filename or "image_b.png")

    # Real, computed change percentage + heatmap — never fabricated.
    cv_result = cd.compute_change(to_rgb_array(img_a), to_rgb_array(img_b))
    changed_regions = cd.region_summary(cv_result["diff_mask"])

    heatmap_name = safe_filename("heatmap.png")
    heatmap_path = os.path.join(settings.upload_dir, heatmap_name)
    with open(heatmap_path, "wb") as f:
        f.write(cv_result["heatmap_bytes"])

    is_demo = False
    try:
        gemini = GeminiService()
        small_a = resize_for_model(img_a); small_b = resize_for_model(img_b)
        narrative = await asyncio.to_thread(
            gemini.summarize_changes, image_to_bytes(small_a), "image/jpeg", image_to_bytes(small_b), "image/jpeg"
        )
        summary = narrative.get("summary") or ""
        if narrative.get("changed_regions"):
            changed_regions = narrative["changed_regions"]
    except GeminiUnavailableError as e:
        # The change percentage and heatmap are computed locally, so the feature still works.
        logger.warning("Gemini unavailable for /change-detection, returning CV-only result: %s", e)
        summary = (
            f"Pixel comparison found {cv_result['change_percentage']:.1f}% of the area changed between Image A and Image B "
            f"(see the heatmap). AI narrative unavailable right now: {e}"
        )

    record = Analysis(
        filename=f"{image_a.filename or 'image_a'} vs {image_b.filename or 'image_b'}",
        analysis_type="change_detection",
        summary=summary,
        change_percentage=cv_result["change_percentage"],
        changed_regions=changed_regions,
        is_demo=is_demo,
        status="completed",
        image_path=path_a,
        image_path_b=path_b,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ChangeDetectionResponse(
        id=record.id,
        change_percentage=record.change_percentage,
        changed_regions=record.changed_regions or [],
        summary=record.summary,
        is_demo=record.is_demo,
        heatmap_url=f"/uploads/{heatmap_name}",
        image_a_url=f"/uploads/{os.path.basename(path_a)}",
        image_b_url=f"/uploads/{os.path.basename(path_b)}",
        created_at=record.created_at,
    )
