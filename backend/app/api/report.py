import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.db import get_db
from app.models.records import Analysis, Report
from app.schemas.schemas import ReportRequest
from app.services.gemini_service import GeminiService, GeminiUnavailableError
from app.services.report_service import generate_report

router = APIRouter()
logger = logging.getLogger("satquery.report")

# Absolute path (backend/reports) so it works no matter where uvicorn is started from.
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")


@router.post("/report")
def create_report(payload: ReportRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    record = db.query(Analysis).filter(Analysis.id == payload.analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    ai_conclusion = None
    try:
        gemini = GeminiService()
        ai_conclusion = gemini.generate_report_summary({
            "summary": record.summary,
            "land_cover": record.land_cover,
            "observations": record.observations,
            "confidence": record.confidence,
            "change_percentage": record.change_percentage,
        })
    except GeminiUnavailableError as e:
        # The PDF is still generated; only the AI-written conclusion is replaced.
        logger.warning("Gemini unavailable for report conclusion, using a computed one: %s", e)
        ai_conclusion = _computed_conclusion(record)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, f"satquery-report-{record.id}.pdf")

    generate_report(
        output_path=output_path,
        filename=record.filename,
        analysis_type=record.analysis_type,
        summary=record.summary or "",
        land_cover=record.land_cover,
        observations=record.observations or [],
        confidence=record.confidence,
        change_percentage=record.change_percentage,
        changed_regions=record.changed_regions,
        location=record.location,
        is_demo=False,
        ai_conclusion=ai_conclusion,
        image_path=record.image_path,
    )

    db.add(Report(analysis_id=record.id, file_path=output_path))
    db.commit()

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"SatQueryAI-Report-{record.id[:8]}.pdf",
    )


def _computed_conclusion(record: Analysis) -> str:
    parts = []
    if record.change_percentage is not None:
        parts.append(f"The pixel-level comparison measured {record.change_percentage:.1f}% change between the two images.")
    if record.land_cover:
        ranked = sorted(((v or 0, k.replace("_", " ")) for k, v in record.land_cover.items()), reverse=True)
        top = ", ".join(f"{name} ({pct:.0f}%)" for pct, name in ranked[:3] if pct > 0)
        if top:
            parts.append(f"The dominant land-cover classes are {top}.")
    if record.confidence is not None:
        parts.append(f"The model's reported confidence was {record.confidence:.0%}.")
    parts.append(
        "This conclusion was generated from the computed metrics because the Gemini AI service was busy when the "
        "report was created; regenerate the report later for an AI-written conclusion."
    )
    return " ".join(parts)
