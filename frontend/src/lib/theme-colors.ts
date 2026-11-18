// Three.js materials need real hex values, not CSS var() strings — this
// file mirrors the palette defined in src/index.css so 3D scenes stay in
// sync with the rest of the design system. Keep these two in sync by hand.

export const PALETTE = {
  signal: '#5eead4',
  vegetation: '#7ed957',
  water: '#4fa8e0',
  thermal: '#f0a857',
  alert: '#e2665a',
  orbit: '#a78bfa',
  violet: '#c084fc',
  amber: '#fbbf24',
  rose: '#fb7185',
  fire: '#fb5607',
  sky: '#38bdf8',
  copilot: '#f472b6',
  mission: '#facc15',
  moon: '#94a3b8',
} as const;

export type PageKey =
  | 'landing'
  | 'dashboard'
  | 'analyze'
  | 'ask'
  | 'change'
  | 'map'
  | 'reports'
  | 'history'
  | 'settings'
  | 'liveearth'
  | 'events'
  | 'monitoring'
  | 'analyst'
  | 'mission'
  | 'copilot'
  | 'timemachine'
  | 'vegetation'
  | 'water'
  | 'nightlights';

/** Each area of the app gets its own accent so the whole product doesn't
 * read as one monochrome accent repeated everywhere. */
export const PAGE_ACCENT: Record<PageKey, string> = {
  landing: PALETTE.signal,
  dashboard: PALETTE.signal,
  analyze: PALETTE.vegetation,
  ask: PALETTE.water,
  change: PALETTE.thermal,
  map: PALETTE.orbit,
  reports: PALETTE.violet,
  history: PALETTE.amber,
  settings: PALETTE.rose,
  liveearth: PALETTE.fire,
  events: PALETTE.thermal,
  monitoring: PALETTE.alert,
  analyst: PALETTE.sky,
  mission: PALETTE.mission,
  copilot: PALETTE.copilot,
  timemachine: PALETTE.orbit,
  vegetation: PALETTE.vegetation,
  water: PALETTE.water,
  nightlights: PALETTE.moon,
};
