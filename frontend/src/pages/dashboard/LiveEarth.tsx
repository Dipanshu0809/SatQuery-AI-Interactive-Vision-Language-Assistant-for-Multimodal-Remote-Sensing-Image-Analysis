import { useEffect, useState } from 'react';
import { Flame, CloudSun, Satellite as SatelliteIcon, Loader2, RefreshCw } from 'lucide-react';
import { MapContainer, TileLayer, WMSTileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/StatCard';
import { api, ApiError } from '@/services/api';
import type { FireDetection, WeatherData } from '@/types';
import { PALETTE, PAGE_ACCENT } from '@/lib/theme-colors';

export default function LiveEarth() {
  const [fires, setFires] = useState<FireDetection[] | null>(null);
  const [firesSource, setFiresSource] = useState('');
  const [weather, setWeather] = useState<WeatherData | null>(null);

  const [weatherSource, setWeatherSource] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [fireRes, weatherRes] = await Promise.all([
        api.liveFires(1),
        api.liveWeather(28.6139, 77.209), // default reference point: New Delhi
      ]);
      setFires(fireRes.fires);
      setFiresSource(fireRes.source);
      setFetchedAt(fireRes.fetched_at);
      setWeather(weatherRes.weather);
      setWeatherSource(weatherRes.source);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load Live Earth data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <PageHeader
        title="Live Earth"
        subtitle="Near-real-time Earth observation signals."
        action={
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs disabled:opacity-50"
            style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
          >
            {loading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
            Refresh Data
          </button>
        }
      />

      <div className="space-y-6 p-6">
        {error && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
            {error}
          </div>
        )}

        {false && (
          <div className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs" style={{ borderColor: PAGE_ACCENT.liveearth, color: PAGE_ACCENT.liveearth }}>
            Live sources only
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-3">
          <StatCard label="Active Fires (24h)" value={fires ? String(fires.length) : '—'} icon={Flame} accent={PAGE_ACCENT.liveearth} />
          <StatCard label="Reference Weather" value={weather ? `${weather.temperature_c ?? '—'}°C` : '—'} icon={CloudSun} accent={PAGE_ACCENT.water} />
          <StatCard label="Imagery Status" value="NASA GIBS live layer" icon={SatelliteIcon} accent={PALETTE.orbit} />
        </div>

        <p className="text-xs" style={{ color: 'var(--text-faint)' }}>
          Fires: {firesSource} {fetchedAt && `· fetched ${new Date(fetchedAt).toLocaleTimeString()}`} · Weather: {weatherSource}
        </p>

        <div className="overflow-hidden rounded-xl border" style={{ borderColor: 'var(--border)' }}>
          <MapContainer center={[20, 10]} zoom={2} style={{ height: 420, width: '100%' }} scrollWheelZoom={false}>
            <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <WMSTileLayer url="https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi" layers="VIIRS_SNPP_CorrectedReflectance_TrueColor" format="image/png" transparent opacity={0.85} />
            {fires?.map((f, i) => (
              <CircleMarker
                key={i}
                center={[f.latitude, f.longitude]}
                radius={6}
                pathOptions={{ color: PAGE_ACCENT.liveearth, fillColor: PAGE_ACCENT.liveearth, fillOpacity: 0.7 }}
              >
                <Popup>
                  <div style={{ fontSize: 12 }}>
                    <strong>Active fire detection</strong>
                    <br />
                    {f.latitude.toFixed(3)}, {f.longitude.toFixed(3)}
                    <br />
                    Confidence: {f.confidence ?? 'n/a'}
                    <br />
                    Source: {f.satellite ?? 'n/a'}
                    <br />
                    Detected: {f.acq_time ?? 'n/a'}
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
