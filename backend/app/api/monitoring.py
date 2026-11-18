from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.records import MonitoringTarget
from app.schemas.live_schemas import MonitoringTargetCreate, MonitoringTargetResponse
from app.services.monitoring_worker import _check_target

router=APIRouter()
@router.post('/monitoring',response_model=MonitoringTargetResponse)
def create_target(payload:MonitoringTargetCreate,db:Session=Depends(get_db)):
    t=MonitoringTarget(**payload.model_dump()); db.add(t); db.commit(); db.refresh(t); return t
@router.get('/monitoring',response_model=list[MonitoringTargetResponse])
def list_targets(db:Session=Depends(get_db)): return db.query(MonitoringTarget).order_by(MonitoringTarget.created_at.desc()).all()
@router.delete('/monitoring/{target_id}')
def delete_target(target_id:str,db:Session=Depends(get_db)):
    t=db.query(MonitoringTarget).filter(MonitoringTarget.id==target_id).first()
    if not t: raise HTTPException(404,'Monitoring target not found.')
    db.delete(t); db.commit(); return {'deleted':True,'id':target_id}
@router.post('/monitoring/{target_id}/refresh',response_model=MonitoringTargetResponse)
async def refresh_target(target_id:str,db:Session=Depends(get_db)):
    t=db.query(MonitoringTarget).filter(MonitoringTarget.id==target_id).first()
    if not t: raise HTTPException(404,'Monitoring target not found.')
    # Same live checks as the background watcher, but only for this target.
    status,details=await _check_target(t)
    t.last_checked_at=datetime.now(timezone.utc); t.last_status=status; t.last_detail=details
    db.commit(); db.refresh(t); return t
