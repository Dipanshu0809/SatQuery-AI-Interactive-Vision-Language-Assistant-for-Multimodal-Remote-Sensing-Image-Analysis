import asyncio
import json
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.db import get_db
from app.models.records import Conversation
from app.schemas.schemas import AskResponse
from app.services.gemini_service import GeminiService, GeminiUnavailableError
from app.services.image_processing import (
    InvalidImageError,
    image_to_bytes,
    resize_for_model,
    validate_and_load,
)
from app.utils.file_utils import enforce_size_limit

router = APIRouter()
logger = logging.getLogger("satquery.ask")


@router.post("/ask", response_model=AskResponse)
async def ask_satquery(
    file: UploadFile = File(...),
    question: str = Form(...),
    analysis_id: str | None = Form(None),
    history: str = Form("[]"),
    db: Session = Depends(get_db),
):
    settings = get_settings()

    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    file_bytes = await file.read()
    enforce_size_limit(file_bytes)

    try:
        img, _meta = validate_and_load(file_bytes, file.content_type)
    except InvalidImageError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        history_list = json.loads(history) if history else []
    except json.JSONDecodeError:
        history_list = []

    try:
        gemini = GeminiService()
        small = resize_for_model(img)
        answer = await asyncio.to_thread(
            gemini.ask_about_image, image_to_bytes(small), "image/jpeg", question.strip(), history_list[-10:]
        )
    except GeminiUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    is_demo = False

    db.add(Conversation(analysis_id=analysis_id, role="user", content=question))
    db.add(Conversation(analysis_id=analysis_id, role="assistant", content=answer))
    db.commit()

    return AskResponse(answer=answer, is_demo=is_demo)
