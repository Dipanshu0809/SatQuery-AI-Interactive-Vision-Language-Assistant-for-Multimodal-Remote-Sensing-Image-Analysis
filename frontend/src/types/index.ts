// Shared frontend types. These mirror the FastAPI Pydantic schemas
// defined in backend/app/schemas so the two stay in sync as the
// API is implemented in later phases.

export type AppMode = 'real';

export interface LandCoverBreakdown {
  vegetation?: number;
  water?: number;
  built_up?: number;
  bare_land?: number;
}

export interface CVSceneMetrics {
  image_width: number | null;
  image_height: number | null;
  brightness: number | null;
  contrast: number | null;
  edge_density_pct: number | null;
  candidate_count: number;
  candidate_regions: { x: number; y: number; width: number; height: number; area_pct: number }[];
  scene_profile: string | null;
  method: string | null;
  overlay_url: string | null;
}

export interface AnalysisResult {
  id: string;
  filename: string;
  summary: string;
  land_cover: LandCoverBreakdown | null;
  observations: string[];
  confidence: number | null;
  is_demo: boolean;
  image_url: string | null;
  created_at: string;
  cv_metrics?: CVSceneMetrics | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChangeDetectionResult {
  id: string;
  change_percentage: number | null;
  changed_regions: string[];
  summary: string;
  is_demo: boolean;
  created_at: string;
}

export interface HistoryRecord {
  id: string;
  filename: string;
  analysis_type: 'analysis' | 'ask' | 'change_detection';
  timestamp: string;
  location: string | null;
  summary: string;
  status: 'completed' | 'failed' | 'processing';
}

export interface BackendStatus {
  status: 'ok' | 'error';
  mode: AppMode;
  gemini_connected: boolean;
  cv_available?: boolean;
  live_fires_connected?: boolean;
  weather_connected?: boolean;
}

// ---- Live Earth ----

export interface FireDetection {
  latitude: number;
  longitude: number;
  brightness: number | null;
  confidence: string | null;
  satellite: string | null;
  acq_time: string | null;
}

export interface WeatherData {
  temperature_c: number | null;
  humidity_pct: number | null;
  wind_kmh: number | null;
  precipitation_mm: number | null;
  cloud_cover_pct: number | null;
  pressure_hpa: number | null;
  condition: string | null;
}

// ---- Earth Intelligence ----

export interface EarthAnalysis {
  summary: string;
  evidence: {
    location: { latitude: number; longitude: number };
    nearby_fires: FireDetection[];
    fire_source: string;
    weather: WeatherData;
    weather_source: string;
    sentinel2: { mean_ndvi: number; mean_ndwi: number; mean_ndbi: number; vegetation_pct: number; water_pct: number; built_up_pct: number; valid_pixels: number; scene: SatelliteScene };
    earthquakes: LiveEarthquake[];
    natural_events: NaturalEvent[];
    event_sources: string[];
  };
  is_demo: boolean;
}

export interface VegetationResult {
  mean_index: number;
  zones: { healthy: number; moderate: number; low: number; bare_or_none: number };
  heatmap_url: string;
  is_proxy: boolean;
  note: string;
}

export interface WaterResult {
  coverage_pct: number;
  heatmap_url: string;
  is_proxy: boolean;
  note: string;
}

export interface ChangeIndexResult {
  /** null when Sentinel-2 data could not be retrieved for this run */
  score: number | null;
  label: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | 'Not available';
  components: Partial<{ vegetation: number; water: number; built_up: number; fire_activity: number }>;
  methodology: string;
}

// ---- Mission Mode ----

export interface MissionStep {
  label: string;
  status: 'done' | 'warning' | 'failed' | 'pending';
  detail: string | null;
}

export interface MissionResult {
  steps: MissionStep[];
  report: {
    objective: string;
    location: { latitude: number; longitude: number; label: string | null };
    summary: string;
    evidence: EarthAnalysis['evidence'];
    change_index: ChangeIndexResult;
    is_demo: boolean;
  } | null;
  is_demo: boolean;
}

// ---- AI Map Copilot ----

export interface MapCommandResult {
  action: 'show_layer' | 'hide_layer' | 'zoom_to' | 'analyze_location' | 'unknown';
  layer: 'active_fires' | 'weather' | 'vegetation' | 'water' | null;
  location_name: string | null;
  latitude: number | null;
  longitude: number | null;
  explanation: string;
  is_demo: boolean;
}

// ---- Monitoring ----

export interface MonitoringTarget {
  id: string;
  label: string;
  latitude: number;
  longitude: number;
  radius_km: number;
  watch_fire: boolean;
  watch_vegetation_change: boolean;
  watch_flood: boolean;
  watch_water_change: boolean;
  watch_urban_expansion: boolean;
  last_checked_at: string | null;
  last_status: 'unchecked' | 'clear' | 'alert';
  last_detail: string[] | null;
  created_at: string;
}

export interface SatelliteScene { id: string | null; datetime: string | null; cloud_cover: number | null; platform?: string | null; constellation?: string | null; bbox?: number[] | null; }
export interface SatelliteIndices { mean_ndvi: number; mean_ndwi: number; mean_ndbi: number; vegetation_pct: number; water_pct: number; built_up_pct: number; valid_pixels: number; }
export interface SatelliteIndicesResponse { indices: SatelliteIndices; scene: SatelliteScene; source: string; fetched_at: string; live: boolean; }
export interface LiveEarthquake { id: string; type: string; title: string; magnitude: number | null; time: string | null; latitude: number; longitude: number; depth_km: number | null; url?: string | null; }
export interface NaturalEvent { id: string; type: string; title: string; category?: string | null; latitude: number | null; longitude: number | null; time?: string | null; source?: string | null; }
