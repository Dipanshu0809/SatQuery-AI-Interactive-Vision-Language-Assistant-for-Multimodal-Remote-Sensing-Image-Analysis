# SatQuery AI — LIVE setup

This build is **live-data only**. It does not silently substitute fabricated/sample data. If a required external source is unavailable, the API returns an explicit error.

## Required credentials

Create `backend/.env` from `backend/.env.example` and set:

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.6-flash
GEMINI_FALLBACK_MODELS=gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-2.5-flash
FIRMS_API_KEY=...
CDSE_CLIENT_ID=...
CDSE_CLIENT_SECRET=...
```

- **Gemini**: Google AI Studio API key.
- **NASA FIRMS**: free MAP_KEY for active-fire data.
- **Copernicus Data Space**: create an OAuth client in User Settings and use its client ID/secret for Sentinel-2.
- NASA GIBS/Worldview imagery and Open-Meteo weather do not require another key in this build.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health: `http://127.0.0.1:8000/api/health`
Docs: `http://127.0.0.1:8000/docs`

The health endpoint reports `mode: real`. Missing credentials are reported as configuration errors rather than demo mode.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

If the frontend runs on another origin, update `CORS_ORIGINS` in `backend/.env`.

## Live sources

- Sentinel-2 L2A: Copernicus Data Space Sentinel Hub Process/Catalog APIs.
- Active fires: NASA FIRMS VIIRS NOAA-21 NRT.
- Earthquakes: USGS all-day GeoJSON feed.
- Natural events: NASA EONET.
- Weather: Open-Meteo current conditions.
- Current satellite visualization/night lights: NASA GIBS/Worldview.
- AI interpretation: Gemini 3.6 Flash.

## Important timing note

"Live" means the freshest data the upstream provider currently exposes. Satellite observations are not continuous video: acquisition and processing latency depends on the satellite and provider. Each satellite result includes an acquisition timestamp where available.
