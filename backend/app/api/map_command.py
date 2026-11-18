from fastapi import APIRouter, HTTPException

from app.schemas.live_schemas import MapCommandRequest, MapCommandResponse
from app.services.map_copilot_service import parse_command

router = APIRouter()


@router.post("/map/command", response_model=MapCommandResponse)
def map_command(payload: MapCommandRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Command text cannot be empty.")
    result = parse_command(payload.text)
    return MapCommandResponse(**result)
