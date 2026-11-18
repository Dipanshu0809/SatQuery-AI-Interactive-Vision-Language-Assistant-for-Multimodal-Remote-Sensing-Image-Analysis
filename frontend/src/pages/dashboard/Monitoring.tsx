import { useEffect, useState } from 'react';
import { BellRing, Loader2, Plus, RefreshCw, Trash2, Inbox } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { api, ApiError } from '@/services/api';
import type { MonitoringTarget } from '@/types';
import { PAGE_ACCENT } from '@/lib/theme-colors';

const CONDITIONS: { key: keyof MonitoringTarget; label: string }[] = [
  { key: 'watch_fire', label: 'Fire detected' },
  { key: 'watch_vegetation_change', label: 'Significant vegetation change' },
  { key: 'watch_flood', label: 'Flood detected' },
  { key: 'watch_water_change', label: 'Water coverage change' },
  { key: 'watch_urban_expansion', label: 'Urban expansion' },
];

export default function Monitoring() {
  const [targets, setTargets] = useState<MonitoringTarget[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [label, setLabel] = useState('');
  const [lat, setLat] = useState('');
  const [lon, setLon] = useState('');
  const [flags, setFlags] = useState<Record<string, boolean>>({ watch_fire: true });
  const [creating, setCreating] = useState(false);

  const load = () => {
    api
      .monitoringList()
      .then(setTargets)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Could not load monitoring targets.'));
  };

  useEffect(load, []);

  const create = async () => {
    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);
    if (!label.trim() || Number.isNaN(latNum) || Number.isNaN(lonNum)) {
      setError('Enter a label and valid coordinates.');
      return;
    }
    setCreating(true);
    setError(null);
    try {
      await api.monitoringCreate({
        label,
        latitude: latNum,
        longitude: lonNum,
        radius_km: 100,
        watch_fire: !!flags.watch_fire,
        watch_vegetation_change: !!flags.watch_vegetation_change,
        watch_flood: !!flags.watch_flood,
        watch_water_change: !!flags.watch_water_change,
        watch_urban_expansion: !!flags.watch_urban_expansion,
      });
      setLabel('');
      setLat('');
      setLon('');
      setFlags({ watch_fire: true });
      setShowForm(false);
      load();
    } catch {
      setError('Could not create monitoring target.');
    } finally {
      setCreating(false);
    }
  };

  const refresh = async (id: string) => {
    setBusyId(id);
    try {
      const updated = await api.monitoringRefresh(id);
      setTargets((prev) => prev?.map((t) => (t.id === id ? updated : t)) ?? null);
    } catch {
      setError('Could not refresh this target.');
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (id: string) => {
    setBusyId(id);
    try {
      await api.monitoringDelete(id);
      setTargets((prev) => prev?.filter((t) => t.id !== id) ?? null);
    } catch {
      setError('Could not delete this target.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Monitoring"
        subtitle="Watch an area for fire and change conditions. Manual refresh only — no background polling."
        action={
          <button
            type="button"
            onClick={() => setShowForm((s) => !s)}
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium"
            style={{ background: PAGE_ACCENT.monitoring, color: '#2a0805' }}
          >
            <Plus size={13} /> New target
          </button>
        }
      />

      <div className="space-y-4 p-6">
        {error && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>{error}</div>
        )}

        {showForm && (
          <div className="space-y-3 rounded-xl border p-4" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Label, e.g. Amazon watch"
              className="w-full rounded-lg border px-3 py-2 text-sm"
              style={{ borderColor: 'var(--border)', background: 'var(--surface-2)' }}
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                placeholder="Latitude"
                className="rounded-lg border px-3 py-2 text-sm"
                style={{ borderColor: 'var(--border)', background: 'var(--surface-2)' }}
              />
              <input
                value={lon}
                onChange={(e) => setLon(e.target.value)}
                placeholder="Longitude"
                className="rounded-lg border px-3 py-2 text-sm"
                style={{ borderColor: 'var(--border)', background: 'var(--surface-2)' }}
              />
            </div>
            <div className="space-y-1.5">
              {CONDITIONS.map((c) => (
                <label key={c.key} className="flex items-center gap-2 text-xs">
                  <input
                    type="checkbox"
                    checked={!!flags[c.key]}
                    onChange={(e) => setFlags((f) => ({ ...f, [c.key]: e.target.checked }))}
                  />
                  {c.label}
                </label>
              ))}
            </div>
            <button
              type="button"
              onClick={create}
              disabled={creating}
              className="rounded-lg px-4 py-2 text-xs font-medium disabled:opacity-50"
              style={{ background: PAGE_ACCENT.monitoring, color: '#2a0805' }}
            >
              {creating ? 'Creating…' : 'Create target'}
            </button>
          </div>
        )}

        {!targets && !error && (
          <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin" /> Loading…
          </div>
        )}

        {targets?.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-16 text-center">
            <Inbox size={22} style={{ color: 'var(--text-faint)' }} />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No monitoring targets yet.</p>
          </div>
        )}

        {targets?.map((t) => (
          <div key={t.id} className="flex items-center gap-4 rounded-xl border p-4" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <div
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
              style={{
                background: 'var(--surface-2)',
                color: t.last_status === 'alert' ? 'var(--color-alert)' : PAGE_ACCENT.monitoring,
              }}
            >
              <BellRing size={16} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">{t.label}</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {t.latitude.toFixed(3)}, {t.longitude.toFixed(3)} · {t.radius_km}km radius
              </p>
              <p className="mt-0.5 text-xs" style={{ color: t.last_status === 'alert' ? 'var(--color-alert)' : 'var(--text-faint)' }}>
                {t.last_checked_at
                  ? `${t.last_status === 'alert' ? 'Alert' : 'Clear'} — checked ${new Date(t.last_checked_at).toLocaleString()}`
                  : 'Not checked yet'}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              <button
                type="button"
                onClick={() => refresh(t.id)}
                disabled={busyId === t.id}
                className="flex h-8 w-8 items-center justify-center rounded-lg border disabled:opacity-50"
                style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
                aria-label="Refresh"
              >
                {busyId === t.id ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              </button>
              <button
                type="button"
                onClick={() => remove(t.id)}
                disabled={busyId === t.id}
                className="flex h-8 w-8 items-center justify-center rounded-lg border disabled:opacity-50"
                style={{ borderColor: 'var(--border)', color: 'var(--color-alert)' }}
                aria-label="Delete"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
