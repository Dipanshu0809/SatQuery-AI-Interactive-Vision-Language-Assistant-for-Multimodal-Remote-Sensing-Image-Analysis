import { useState } from 'react';
import { Brain, Loader2, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { api, ApiError } from '@/services/api';
import type { EarthAnalysis } from '@/types';
import { PAGE_ACCENT } from '@/lib/theme-colors';

export default function EarthAnalyst() {
  const [lat, setLat] = useState('28.6139');
  const [lon, setLon] = useState('77.2090');
  const [objective, setObjective] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EarthAnalysis | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);

  const run = async () => {
    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);
    if (Number.isNaN(latNum) || Number.isNaN(lonNum)) {
      setError('Enter valid latitude and longitude.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.earthAnalyze(latNum, lonNum, objective || undefined);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not analyze this location.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader title="Earth Analyst" subtitle="Ask what's happening in a region — grounded in retrieved evidence, not invented." />

      <div className="max-w-2xl space-y-4 p-6">
        <div className="grid grid-cols-2 gap-3">
          <label className="text-xs">
            <span style={{ color: 'var(--text-muted)' }}>Latitude</span>
            <input
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
              style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
            />
          </label>
          <label className="text-xs">
            <span style={{ color: 'var(--text-muted)' }}>Longitude</span>
            <input
              value={lon}
              onChange={(e) => setLon(e.target.value)}
              className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
              style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
            />
          </label>
        </div>

        <label className="block text-xs">
          <span style={{ color: 'var(--text-muted)' }}>What do you want to know? (optional)</span>
          <input
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="e.g. What's happening in this region?"
            className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
            style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
          />
        </label>

        <button
          type="button"
          onClick={run}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-50"
          style={{ background: PAGE_ACCENT.analyst, color: '#06201d' }}
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Brain size={15} />}
          Analyze Location
        </button>

        {error && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-3">
            {result.is_demo && (
              <div className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs" style={{ borderColor: PAGE_ACCENT.analyst, color: PAGE_ACCENT.analyst }}>
                <Sparkles size={12} /> Live evidence only
              </div>
            )}
            <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <h3 className="mb-2 text-sm font-medium">Analysis</h3>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{result.summary}</p>
            </div>

            <button
              type="button"
              onClick={() => setShowEvidence((s) => !s)}
              className="flex items-center gap-1.5 text-xs"
              style={{ color: 'var(--text-muted)' }}
            >
              Why am I seeing this? {showEvidence ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>

            {showEvidence && (
              <div className="rounded-xl border p-4 text-xs" style={{ borderColor: 'var(--border)', background: 'var(--surface-2)' }}>
                <p className="mb-1"><strong>Nearby active fires (150km):</strong> {result.evidence.nearby_fires.length} — {result.evidence.fire_source}</p>
                <p className="mb-1"><strong>Weather:</strong> {result.evidence.weather.condition ?? '—'}{result.evidence.weather.temperature_c != null ? `, ${result.evidence.weather.temperature_c}°C` : ''} — {result.evidence.weather_source}</p>
                <p style={{ color: 'var(--text-faint)' }}>This is the complete evidence set Gemini was given — it was instructed not to add anything beyond it.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
