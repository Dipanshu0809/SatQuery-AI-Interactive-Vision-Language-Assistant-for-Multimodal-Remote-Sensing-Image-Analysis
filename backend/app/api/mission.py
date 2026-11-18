import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.schemas.live_schemas import InvestigationReportRequest, MissionRequest, MissionResponse
from app.services.mission_service import run_mission
from app.services.report_service import generate_investigation_report

router = APIRouter()

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")


@router.post("/mission/investigate", response_model=MissionResponse)
async def mission_investigate(payload: MissionRequest):
    result = await run_mission(payload.objective, payload.latitude, payload.longitude)
    return MissionResponse(**result)


@router.post("/mission/report")
def mission_report(payload: InvestigationReportRequest):
    import uuid

    report_id = uuid.uuid4().hex[:10]
    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, f"satquery-investigation-{report_id}.pdf")

    generate_investigation_report(
        output_path=output_path,
        objective=payload.objective,
        location_label=payload.location.get("label"),
        latitude=float(payload.location.get("latitude") or 0.0),
        longitude=float(payload.location.get("longitude") or 0.0),
        summary=payload.summary,
        evidence=payload.evidence,
        change_index=payload.change_index,
        is_demo=payload.is_demo,
    )

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"SatQueryAI-Investigation-{report_id}.pdf",
    )
