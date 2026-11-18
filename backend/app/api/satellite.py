from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from app.services.cdse_service import SatelliteUnavailableError, latest_scene, raw_indices, scene_image, index_image, search_scenes
from app.services.gibs_service import wms_image_url, point_bbox, TRUE_COLOR_LAYER, NIGHT_LIGHT_LAYER

router=APIRouter()

def _err(e):
    return HTTPException(status_code=503, detail=str(e))

@router.get('/satellite/scenes')
def satellite_scenes(lat:float, lon:float, start_date:str, end_date:str, limit:int=10):
    try: return {'scenes':search_scenes(lat,lon,start_date,end_date,min(limit,50)),'source':'Copernicus Data Space Sentinel-2 L2A','fetched_at':datetime.now(timezone.utc).isoformat()}
    except Exception as e: raise _err(e)

@router.get('/satellite/scene')
def satellite_scene(lat:float, lon:float, days_back:int=30):
    try:
        scene=latest_scene(lat,lon,days_back)
        return {'scene':scene,'source':'Copernicus Data Space Sentinel-2 L2A','fetched_at':datetime.now(timezone.utc).isoformat()}
    except Exception as e: raise _err(e)

@router.get('/satellite/image')
def satellite_image(lat:float, lon:float, date:str|None=None, days_back:int=30):
    try:
        data,scene=scene_image(lat,lon,date,days_back)
        return Response(content=data,media_type='image/png',headers={'X-Satellite-Source':'Copernicus Data Space Sentinel-2 L2A','X-Satellite-Acquisition':str(scene.get('datetime') or '')})
    except Exception as e: raise _err(e)

@router.get('/satellite/indices')
def satellite_indices(lat:float, lon:float, date:str|None=None, days_back:int=30):
    try:
        stats,scene=raw_indices(lat,lon,date,days_back)
        return {'indices':stats,'scene':scene,'source':'Copernicus Data Space Sentinel-2 L2A','fetched_at':datetime.now(timezone.utc).isoformat(),'live':True}
    except Exception as e: raise _err(e)

@router.get('/satellite/index-image')
def satellite_index_image(lat:float,lon:float,index:str=Query(...,pattern='^(ndvi|ndwi)$'),date:str|None=None,days_back:int=30):
    try:
        data,scene=index_image(lat,lon,index,date,days_back)
        # Raw float TIFF is scientifically useful but not directly viewable. Keep the raw response available for processing clients.
        return Response(content=data,media_type='image/tiff',headers={'X-Satellite-Acquisition':str(scene.get('datetime') or ''),'X-Index':index})
    except Exception as e: raise _err(e)

@router.get('/satellite/change')
def satellite_change(lat:float,lon:float,date_a:str,date_b:str):
    try:
        a,sa=raw_indices(lat,lon,date_a); b,sb=raw_indices(lat,lon,date_b)
        ndvi_delta=b['mean_ndvi']-a['mean_ndvi']; ndwi_delta=b['mean_ndwi']-a['mean_ndwi']; ndbi_delta=b['mean_ndbi']-a['mean_ndbi']
        score=min(100.0,round((abs(ndvi_delta)+abs(ndwi_delta)+abs(ndbi_delta))*100,2))
        return {'date_a':sa,'date_b':sb,'before':a,'after':b,'delta':{'ndvi':ndvi_delta,'ndwi':ndwi_delta,'ndbi':ndbi_delta},'change_score':score,'source':'Copernicus Data Space Sentinel-2 L2A','fetched_at':datetime.now(timezone.utc).isoformat(),'live':True}
    except Exception as e: raise _err(e)

@router.get('/imagery/nasa-wms')
def nasa_wms(lat:float,lon:float,layer:str=TRUE_COLOR_LAYER,date:str|None=None):
    allowed={TRUE_COLOR_LAYER,NIGHT_LIGHT_LAYER}
    if layer not in allowed: raise HTTPException(400,'Unsupported NASA GIBS layer')
    return {'url':wms_image_url(layer,point_bbox(lat,lon,4.0),1200,700,date),'source':'NASA GIBS / Worldview','layer':layer,'date':date,'live':True,'fetched_at':datetime.now(timezone.utc).isoformat()}
