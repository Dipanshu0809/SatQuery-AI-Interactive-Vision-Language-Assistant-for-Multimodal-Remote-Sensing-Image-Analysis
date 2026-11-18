"""Application configuration, loaded from environment variables / .env."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    # Tried in order when the main model is overloaded or out of quota (comma separated).
    gemini_fallback_models: str = "gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-2.5-flash"
    firms_api_key: str | None = None  # NASA FIRMS MAP_KEY — free, https://firms.modaps.eosdis.nasa.gov/api/
    nasa_api_key: str | None = None
    cdse_client_id: str | None = None
    cdse_client_secret: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    database_url: str = "sqlite:///./data/satquery.db"
    max_upload_mb: int = 15
    upload_dir: str = "uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
