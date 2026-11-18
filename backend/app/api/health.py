from fastapi import APIRouter
from app.config import get_settings
from app.schemas.schemas import HealthResponse

router=APIRouter()
@router.get('/health',response_model=HealthResponse)
def health():
    s=get_settings()
    return HealthResponse(status='ok',mode='real',gemini_connected=bool(s.gemini_api_key),cv_available=True,live_fires_connected=bool(s.firms_api_key),weather_connected=True)
