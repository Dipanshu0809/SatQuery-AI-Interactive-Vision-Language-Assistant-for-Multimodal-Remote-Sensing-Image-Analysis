import asyncio
import os
from fastapi import APIRouter, HTTPException
from app.schemas.live_schemas import ChangeIndexRequest, ChangeIndexResponse, EarthAnalyzeRequest, EarthAnalyzeResponse, VegetationResponse, WaterIndexResponse
from app.services.earth_analyst_service import analyze_location
from app.services.earth_change_index import compute_change_index
from app.services.firms_service import get_active_fires
from app.services.earth_analyst_service import haversine_km
from app.services.cdse_service import raw_indices, SatelliteUnavailableError
from app.services.image_processing import InvalidImageError, to_rgb_array, validate_and_load
from app.services.vegetation_service import compute_exg_index, index_to_heatmap_rgb as veg_heatmap
from app.services.water_service import compute_water_index, index_to_heatmap_rgb as water_heatmap
from app.utils.file_utils import enforce_size_limit, safe_filename
from fastapi import File, UploadFile
from PIL import Image
from app.config import get_settings

router=APIRouter(); settings=get_settings()

def _sat_error(e): return HTTPException(status_code=503,detail=str(e))

@router.post('/earth/analyze',response_model=EarthAnalyzeResponse)
async def earth_analyze(payload:EarthAnalyzeRequest):
    try:return EarthAnalyzeResponse(**await analyze_location(payload.latitude,payload.longitude,payload.objective))
    except Exception as e:raise _sat_error(e)

@router.post('/earth/query',response_model=EarthAnalyzeResponse)
async def earth_query(payload:EarthAnalyzeRequest):
    try:return EarthAnalyzeResponse(**await analyze_location(payload.latitude,payload.longitude,payload.objective))
    except Exception as e:raise _sat_error(e)

@router.get('/earth/indices')
def earth_indices(lat:float,lon:float,date:str|None=None):
    try:
        stats,scene=raw_indices(lat,lon,date)
        return {'indices':stats,'scene':scene,'live':True,'source':'Copernicus Data Space Sentinel-2 L2A'}
    except Exception as e:raise _sat_error(e)

@router.post('/vegetation',response_model=VegetationResponse)
async def vegetation_analysis(file:UploadFile=File(...)):
    # Uploaded imagery remains supported as a real analysis path, never demo data.
    b=await file.read(); enforce_size_limit(b)
    try: img,_=validate_and_load(b,file.content_type)
    except InvalidImageError as e:raise HTTPException(400,str(e))
    rgb=to_rgb_array(img); result=compute_exg_index(rgb); heatmap=veg_heatmap(result['index_array']); name=safe_filename('vegetation_heatmap.png'); Image.fromarray(heatmap).save(os.path.join(settings.upload_dir,name))
    return VegetationResponse(mean_index=result['mean_index'],zones=result['zones'],heatmap_url=f'/uploads/{name}',is_proxy=True,note='RGB-only uploaded image analysis. For live satellite NDVI use GET /api/earth/indices with a location.')

@router.post('/water',response_model=WaterIndexResponse)
async def water_analysis(file:UploadFile=File(...)):
    b=await file.read(); enforce_size_limit(b)
    try: img,_=validate_and_load(b,file.content_type)
    except InvalidImageError as e:raise HTTPException(400,str(e))
    rgb=to_rgb_array(img); result=compute_water_index(rgb); heatmap=water_heatmap(result['index_array']); name=safe_filename('water_heatmap.png'); Image.fromarray(heatmap).save(os.path.join(settings.upload_dir,name))
    return WaterIndexResponse(coverage_pct=result['coverage_pct'],heatmap_url=f'/uploads/{name}',is_proxy=True,note='RGB-only uploaded image analysis. For live satellite NDWI use GET /api/earth/indices with a location.')

@router.post('/earth/change-index',response_model=ChangeIndexResponse)
async def earth_change_index(payload:ChangeIndexRequest):
    if payload.latitude is None or payload.longitude is None:
        raise HTTPException(400,'Latitude and longitude are required for live Earth Change Index.')
    try:
        stats,scene=await asyncio.to_thread(raw_indices,payload.latitude,payload.longitude)
        fires_note=''
        try:
            fires=await get_active_fires(1); fire_count=sum(1 for f in fires['fires'] if haversine_km(payload.latitude,payload.longitude,f['latitude'],f['longitude'])<=150)
        except Exception as fe:  # FIRMS down: index still computed from Sentinel-2, clearly noted
            fire_count=0; fires_note=f' NASA FIRMS was unavailable ({fe}); fire count treated as 0.'
        result=compute_change_index(vegetation_delta_pct=abs(stats['mean_ndvi'])*100,water_delta_pct=abs(stats['mean_ndwi'])*100,built_up_delta_pct=max(0,stats['mean_ndbi'])*100,nearby_fire_count=fire_count)
        result['methodology']='Live composite using current Sentinel-2 L2A NDVI/NDWI/NDBI proxies plus NASA FIRMS active-fire count; not an official government index.'+fires_note
        result['source_scene']=scene
        return ChangeIndexResponse(**result)
    except Exception as e:raise _sat_error(e)
