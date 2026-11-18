# SatQuery AI — Live Remote Sensing Platform

CSE471 course project, Lovely Professional University (School of Computer Science and Engineering).

| Member | Reg. No. | Roll No. | Section |
|---|---|---|---|
| Ayush Singh | 12409278 | 52 | K24KB |
| Dipanshu | 12414141 | 61 | K24KB |

SatQuery AI is a React + FastAPI remote-sensing application that combines real Earth-observation feeds with computer
vision and Gemini-based analysis. A user states an objective in plain language ("Investigate environmental changes
around Amritsar") and receives an assessment grounded in live observations. Every number is computed in code;
Gemini only writes the narrative.

## Live application

- Web app (Netlify): https://satquery-ai-lpu.netlify.app
- Backend API (Render): https://satquery-ai-api.onrender.com
- API docs: https://satquery-ai-api.onrender.com/docs

The free Render backend sleeps after 15 minutes without traffic; the first request after a pause can take about a minute.

## Modules

- **Image Analysis** — uploaded-image CV measurements (OpenCV) + Gemini interpretation.
- **Ask SatQuery** — Gemini answers grounded in the uploaded image.
- **Change Detection** — pixel-level change mask between two images + Gemini comparison narrative.
- **Live Earth** — NASA GIBS imagery + NASA FIRMS fires + live weather.
- **Events** — NASA FIRMS active fires, USGS earthquakes, NASA EONET natural events.
- **Monitoring** — saved locations refreshed every 15 minutes by a background worker.
- **Earth Analyst** — Sentinel-2 multispectral indices + fires + weather + USGS/EONET + Gemini.
- **Mission Mode** — seven-step investigation from one sentence (location, Sentinel-2 scene, indices, events, weather, Earth Change Index, report).
- **AI Map Copilot** — Gemini returns structured map commands, checked against an allowlist.
- **Satellite Map** — NASA GIBS satellite imagery layer.
- **Time Machine** — historical Sentinel-2 acquisition search and imagery.
- **Vegetation** — Sentinel-2 NDVI from B08/B04.
- **Water Intelligence** — Sentinel-2 NDWI from B03/B08.
- **Night Lights** — NASA VIIRS Day/Night Band (Black Marble) imagery through GIBS.
- **Reports** — PDF reports generated from the retrieved evidence (ReportLab).

## Architecture

```text
React 19 SPA (Netlify) ──HTTPS/JSON──► FastAPI backend (Render, Docker)
                                         ├─ Copernicus Data Space: Sentinel-2 L2A (OAuth, Catalog, Process)
                                         ├─ NASA FIRMS (VIIRS NOAA-21 NRT)
                                         ├─ USGS earthquakes · NASA EONET events · Open-Meteo weather
                                         ├─ Google Gemini (narrative only)
                                         └─ SQLite history · TTL cache · monitoring worker
Browser ──WMS──► NASA GIBS imagery (URLs built by the backend)
```

## Credentials

All keys live only in `backend/.env` (never committed). Copy `backend/.env.example` to `backend/.env` and fill in:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
# optional - tried in order when the main model is overloaded or out of quota
GEMINI_FALLBACK_MODELS=gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-2.5-flash
FIRMS_API_KEY=
CDSE_CLIENT_ID=
CDSE_CLIENT_SECRET=
CORS_ORIGINS=http://localhost:5173
```

- Gemini: Google AI Studio API key.
- NASA FIRMS: free MAP_KEY.
- Copernicus Data Space: OAuth client ID/secret (User Settings → OAuth clients).
- NASA GIBS, USGS, EONET and Open-Meteo need no key.

## Run locally (Windows PowerShell)

```powershell
# backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt     # or, from the project root: pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000     # health: http://127.0.0.1:8000/api/health

# frontend (second terminal)
cd frontend
npm install
npm run dev                                    # http://localhost:5173
```

`start-backend.bat` and `start-frontend.bat` do the same with one click. `docker-compose up --build` runs both in containers.

## Deploy

**Backend on Render** (Netlify cannot run Python):
1. New → Web Service → connect this repository; name `satquery-ai-api`; root directory `backend`; runtime Docker.
2. Environment variables: `GEMINI_API_KEY`, `GEMINI_MODEL`, `FIRMS_API_KEY`, `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET`,
   `PORT=8000`, `CORS_ORIGINS=https://satquery-ai-lpu.netlify.app` (optional: `GEMINI_FALLBACK_MODELS`).
3. Check `https://satquery-ai-api.onrender.com/api/health` reports `mode: real`.

**Frontend on Netlify** (settings come from `netlify.toml` in the project root):
1. Add new site → import this repository; site name `satquery-ai-lpu`.
2. Environment variable `VITE_API_URL=https://satquery-ai-api.onrender.com` (set before the first build).
3. Deploy and confirm the sidebar shows "Backend online · real mode".

## No fabricated fallback

SatQuery AI never substitutes sample or demo data. When a live source is temporarily unavailable:

- **Gemini busy / out of quota** - the next model in `GEMINI_FALLBACK_MODELS` answers. If every model is busy, Image
  Analysis, Change Detection, Reports, Earth Analyst and Mission Mode still return their *computed* results (OpenCV
  metrics, pixel change %, live evidence) with a clear "AI narrative unavailable" note; Map Copilot uses a keyword
  parser. Only Ask SatQuery (pure AI chat) returns a 503 asking you to retry.
- **Copernicus, FIRMS, weather, USGS, EONET** - requests are retried automatically (timeouts, 429, 5xx). Mission Mode
  and Earth Analyst continue with the sources that answered and mark the missing ones; single-source pages return an
  explicit 503 naming the source.

## Reliability and quota savings

- Gemini: model fallback chain, cool-down for overloaded models (respects Google's `retryDelay`), one-hour response
  cache for identical requests, large images downscaled before upload.
- Copernicus: 3 attempts with back-off, 60 s catalog / 120 s processing timeouts, newest usable scene selected,
  30-60 min caches so repeated views do not spend processing units.
- Mission Mode gathers all five sources in parallel in a single pass (previously three duplicate satellite requests).
- Blocking calls run in worker threads, so one slow request no longer freezes the whole backend.

## Fixes in this version

- Mission Mode and the monitoring worker passed `30` as the scene *date* instead of `days_back`, so Copernicus
  rejected the search (HTTP 400). Fixed in `mission_service.py` and `monitoring_worker.py`.
- Error responses now carry CORS headers, so the UI shows the real reason instead of "Could not reach the backend".
- Frontend production build (`npm run build`) fixed for TypeScript 6; `netlify.toml` added.
- Gemini "503 UNAVAILABLE - model is experiencing high demand" and 429 quota errors no longer break features (see above).
- Copernicus `httpx.ReadTimeout` in Mission Mode is retried instead of crashing with a 500.
- Mission report PDF crashed when the `reports` folder did not exist; the backend crashed on start when `uploads/`
  was missing (Git does not keep empty folders). Both folders are now created automatically.
- AI text containing `&` or `<` no longer breaks PDF generation; image URLs fixed on Windows paths.
- Monitoring: one failing target no longer cancels the others; "Refresh" checks only the selected target.
