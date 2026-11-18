import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.records import Analysis
from app.schemas.schemas import HistoryDetail, HistoryItem

router = APIRouter()


@router.get("/history", response_model=list[HistoryItem])
def list_history(db: Session = Depends(get_db), limit: int = 50):
    records = (
        db.query(Analysis).order_by(desc(Analysis.created_at)).limit(limit).all()
    )
    return [
        HistoryItem(
            id=r.id,
            filename=r.filename,
            analysis_type=r.analysis_type,
            timestamp=r.created_at,
            location=r.location,
            summary=r.summary,
            status=r.status,
        )
        for r in records
    ]


@router.get("/history/{item_id}", response_model=HistoryDetail)
def get_history_item(item_id: str, db: Session = Depends(get_db)):
    r = db.query(Analysis).filter(Analysis.id == item_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="History item not found.")
    return HistoryDetail(
        id=r.id,
        filename=r.filename,
        analysis_type=r.analysis_type,
        timestamp=r.created_at,
        location=r.location,
        summary=r.summary,
        status=r.status,
        land_cover=r.land_cover,
        observations=r.observations or [],
        confidence=r.confidence,
        change_percentage=r.change_percentage,
        changed_regions=r.changed_regions or [],
        is_demo=r.is_demo,
    )


@router.delete("/history/{item_id}")
def delete_history_item(item_id: str, db: Session = Depends(get_db)):
    r = db.query(Analysis).filter(Analysis.id == item_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="History item not found.")

    for path in (r.image_path, r.image_path_b):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    db.delete(r)
    db.commit()
    return {"deleted": True, "id": item_id}
