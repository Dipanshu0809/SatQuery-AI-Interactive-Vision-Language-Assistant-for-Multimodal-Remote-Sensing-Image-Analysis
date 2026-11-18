// Centralized API client. Every request to the FastAPI backend goes
// through this module rather than components calling fetch() directly.

import type {
  AnalysisResult,
  ChangeDetectionResult,
  HistoryRecord,
  BackendStatus,
  FireDetection,
  WeatherData,
  EarthAnalysis,
  VegetationResult,
  WaterResult,
  ChangeIndexResult,
  MissionResult,
  MapCommandResult,
  MonitoringTarget,
  SatelliteScene, SatelliteIndicesResponse, LiveEarthquake, NaturalEvent,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const UNREACHABLE_MESSAGE =
  'Could not reach the SatQuery AI backend. If it is hosted on Render (free plan) it may be waking up - ' +
  'wait about a minute and try again. When running locally, make sure the backend is running on port 8000.';

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Turn a FastAPI error body into a readable message (422 errors arrive as a list). */
async function errorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === 'string' && detail) return detail;
    if (Array.isArray(detail) && detail.length) {
      return detail
        .map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc ?? []).slice(1).join('.') || 'input'}: ${d.msg ?? 'invalid'}`)
        .join('; ');
    }
  } catch {
    // not JSON - use the fallback
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method ?? 'GET').toUpperCase();
  // GET requests are retried (a sleeping free-tier server or a brief network drop).
  const attempts = method === 'GET' ? 3 : 1;
  let res: Response | null = null;
  for (let i = 0; i < attempts; i++) {
    try {
      res = await fetch(`${API_BASE_URL}${path}`, init);
    } catch {
      if (i === attempts - 1) throw new ApiError(UNREACHABLE_MESSAGE);
      await wait(2000 * (i + 1));
      continue;
    }
    if (method === 'GET' && [502, 504].includes(res.status) && i < attempts - 1) {
      await wait(2000 * (i + 1));
      continue;
    }
    break;
  }
  if (!res) throw new ApiError(UNREACHABLE_MESSAGE);

  if (!res.ok) {
    throw new ApiError(await errorMessage(res, `Request failed with status ${res.status}`), res.status);
  }

  return res.json() as Promise<T>;
}

/** POST that returns a file (PDF reports). */
async function requestBlob(path: string, body: unknown, fallback: string): Promise<Blob> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(UNREACHABLE_MESSAGE);
  }
  if (!res.ok) throw new ApiError(await errorMessage(res, fallback), res.status);
  return res.blob();
}

function resolveUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${API_BASE_URL}${path}`;
}

export const api = {
  baseUrl: API_BASE_URL,
  resolveUrl,

  health: () => request<BackendStatus>('/api/health'),

  analyze: (file: File, location?: string) => {
    const form = new FormData();
    form.append('file', file);
    if (location) form.append('location', location);
    return request<AnalysisResult>('/api/analyze', { method: 'POST', body: form });
  },

  ask: (
    file: File,
    question: string,
    history: { role: string; content: string }[],
    analysisId?: string,
  ) => {
    const form = new FormData();
    form.append('file', file);
    form.append('question', question);
    form.append('history', JSON.stringify(history));
    if (analysisId) form.append('analysis_id', analysisId);
    return request<{ answer: string; is_demo: boolean }>('/api/ask', {
      method: 'POST',
      body: form,
    });
  },

  changeDetection: (imageA: File, imageB: File) => {
    const form = new FormData();
    form.append('image_a', imageA);
    form.append('image_b', imageB);
    return request<ChangeDetectionResult & { heatmap_url: string; image_a_url: string; image_b_url: string }>(
      '/api/change-detection',
      { method: 'POST', body: form },
    );
  },

  report: (analysisId: string): Promise<Blob> =>
    requestBlob('/api/report', { analysis_id: analysisId }, 'Could not generate the report.'),

  history: () => request<HistoryRecord[]>('/api/history'),

  historyDetail: (id: string) => request<HistoryRecord & Record<string, unknown>>(`/api/history/${id}`),

  deleteHistory: (id: string) =>
    request<{ deleted: boolean; id: string }>(`/api/history/${id}`, { method: 'DELETE' }),

  // ---- Live Earth ----
  liveFires: (days = 1) =>
    request<{ fires: FireDetection[]; is_demo: boolean; source: string; fetched_at: string; from_cache: boolean }>(
      `/api/live/fires?days=${days}`,
    ),

  liveWeather: (lat: number, lon: number) =>
    request<{ weather: WeatherData; is_demo: boolean; source: string; fetched_at: string; from_cache: boolean }>(
      `/api/live/weather?lat=${lat}&lon=${lon}`,
    ),

  liveEarthquakes: () => request<{ events: LiveEarthquake[]; source: string; fetched_at: string }>('/api/live/earthquakes'),
  liveNaturalEvents: () => request<{ events: NaturalEvent[]; source: string; fetched_at: string }>('/api/live/natural-events'),

  liveSummary: () =>
    request<{ active_fires: number; fires_is_demo: boolean; fires_source: string; fetched_at: string }>(
      '/api/live/summary',
    ),

  // ---- Earth Intelligence ----
  earthAnalyze: (latitude: number, longitude: number, objective?: string) =>
    request<EarthAnalysis>('/api/earth/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude, longitude, objective }),
    }),

  earthQuery: (latitude: number, longitude: number, objective?: string) =>
    request<EarthAnalysis>('/api/earth/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude, longitude, objective }),
    }),

  vegetation: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<VegetationResult>('/api/vegetation', { method: 'POST', body: form });
  },

  water: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<WaterResult>('/api/water', { method: 'POST', body: form });
  },

  changeIndex: (
    veg: number,
    water: number,
    built: number,
    lat?: number,
    lon?: number,
  ) =>
    request<ChangeIndexResult>('/api/earth/change-index', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vegetation_delta_pct: veg,
        water_delta_pct: water,
        built_up_delta_pct: built,
        latitude: lat,
        longitude: lon,
      }),
    }),

  // ---- Mission Mode ----
  missionInvestigate: (objective: string, latitude?: number, longitude?: number) =>
    request<MissionResult>('/api/mission/investigate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ objective, latitude, longitude }),
    }),

  missionReport: (report: NonNullable<MissionResult['report']>): Promise<Blob> =>
    requestBlob('/api/mission/report', report, 'Could not generate the investigation report.'),

  // ---- AI Map Copilot ----
  mapCommand: (text: string) =>
    request<MapCommandResult>('/api/map/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }),

  // ---- Monitoring ----
  monitoringList: () => request<MonitoringTarget[]>('/api/monitoring'),

  monitoringCreate: (target: Omit<MonitoringTarget, 'id' | 'last_checked_at' | 'last_status' | 'last_detail' | 'created_at'>) =>
    request<MonitoringTarget>('/api/monitoring', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(target),
    }),

  monitoringRefresh: (id: string) =>
    request<MonitoringTarget>(`/api/monitoring/${id}/refresh`, { method: 'POST' }),

  satelliteScenes: (lat: number, lon: number, start: string, end: string, limit = 10) => request<{ scenes: SatelliteScene[]; source: string; fetched_at: string }>(`/api/satellite/scenes?lat=${lat}&lon=${lon}&start_date=${start}&end_date=${end}&limit=${limit}`),
  satelliteScene: (lat: number, lon: number, days = 30) => request<{ scene: SatelliteScene; source: string; fetched_at: string }>(`/api/satellite/scene?lat=${lat}&lon=${lon}&days_back=${days}`),
  satelliteImageUrl: (lat: number, lon: number, date?: string) => `${API_BASE_URL}/api/satellite/image?lat=${lat}&lon=${lon}${date ? `&date=${date}` : ''}`,
  satelliteIndices: (lat: number, lon: number, date?: string) => request<SatelliteIndicesResponse>(`/api/satellite/indices?lat=${lat}&lon=${lon}${date ? `&date=${date}` : ''}`),
  satelliteChange: (lat: number, lon: number, dateA: string, dateB: string) => request<any>(`/api/satellite/change?lat=${lat}&lon=${lon}&date_a=${dateA}&date_b=${dateB}`),
  nasaWms: (lat: number, lon: number, layer: string, date?: string) => request<{ url: string; source: string; layer: string; date?: string | null; live: boolean }>(`/api/imagery/nasa-wms?lat=${lat}&lon=${lon}&layer=${encodeURIComponent(layer)}${date ? `&date=${date}` : ''}`),

  monitoringDelete: (id: string) =>
    request<{ deleted: boolean; id: string }>(`/api/monitoring/${id}`, { method: 'DELETE' }),
};

export { ApiError };
