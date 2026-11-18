import asyncio, logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.records import MonitoringTarget
from app.services.firms_service import get_active_fires
from app.services.cdse_service import raw_indices
from app.services.earth_analyst_service import haversine_km

logger=logging.getLogger('satquery.monitoring')

async def _check_target(t):
    details=[]; alert=False
    if t.watch_fire:
        try:
            fires=await get_active_fires(1)
            nearby=[f for f in fires['fires'] if haversine_km(t.latitude,t.longitude,f['latitude'],f['longitude'])<=t.radius_km]
            if nearby: alert=True; details.append({'type':'fire','count':len(nearby),'source':fires['source'],'detections':nearby[:20]})
            else: details.append({'type':'fire','count':0,'source':fires['source']})
        except Exception as e:
            details.append({'type':'fire','error':str(e)[:300]})
    if t.watch_vegetation_change or t.watch_water_change or t.watch_urban_expansion:
        try:
            stats,scene=await asyncio.to_thread(raw_indices,t.latitude,t.longitude,None,30)
            details.append({'type':'sentinel2','scene':scene,'indices':stats})
            if t.watch_vegetation_change and stats['mean_ndvi'] < 0.2: alert=True
            if t.watch_water_change and stats['mean_ndwi'] > 0.2: alert=True
            if t.watch_urban_expansion and stats['mean_ndbi'] > 0.1: alert=True
        except Exception as e:
            details.append({'type':'sentinel2','error':str(e)[:300]})
    errors=[d for d in details if 'error' in d]
    status='alert' if alert else ('error' if errors and len(errors)==len(details) else 'clear')
    return status, details


async def refresh_all_targets():
    db=SessionLocal()
    try:
        targets=db.query(MonitoringTarget).all()
        for t in targets:
            # Each target is checked on its own, so one failing source never blocks the others.
            status,details=await _check_target(t)
            t.last_checked_at=datetime.now(timezone.utc); t.last_status=status; t.last_detail=details
            db.commit()
    except Exception:
        logger.exception('Live monitoring refresh failed')
        db.rollback()
    finally: db.close()

async def monitoring_loop(interval_seconds=900):
    while True:
        try: await refresh_all_targets()
        except Exception: logger.exception('Monitoring loop iteration failed')
        await asyncio.sleep(interval_seconds)
