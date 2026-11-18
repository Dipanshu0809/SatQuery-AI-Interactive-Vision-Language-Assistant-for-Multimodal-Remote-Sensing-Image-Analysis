# Live-data upgrade notes

This release replaces the previous demonstration-data architecture with explicit live integrations.

## Added

- Copernicus Data Space Sentinel Hub OAuth + Catalog + Process API service.
- Sentinel-2 L2A RGB retrieval and multispectral B03/B04/B08/B11 processing.
- True NDVI, NDWI and NDBI calculations from Sentinel-2 bands.
- Historical Sentinel-2 acquisition search for Time Machine.
- NASA GIBS/Worldview live imagery and VIIRS night-light layer.
- NASA FIRMS VIIRS NOAA-21 NRT fire feed without sample fallback.
- USGS live earthquake feed.
- NASA EONET live natural-event feed.
- Background monitoring refresh loop.
- Gemini-only Map Copilot with no fallback parser.
- Live-only Mission Mode/Earth Analyst evidence pipeline.
- Dependency fix for `google-genai` and Pydantic compatibility.

## Data freshness

The application displays source/acquisition timestamps where available. Satellite data is observation-based rather than continuous video; upstream acquisition and processing latency remains outside SatQuery's control.
