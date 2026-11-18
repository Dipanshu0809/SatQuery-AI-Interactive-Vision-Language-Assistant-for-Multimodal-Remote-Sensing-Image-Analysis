import { useRef, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Send, Loader2, Bot, Flame } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { api, ApiError } from '@/services/api';
import type { FireDetection } from '@/types';
import { PAGE_ACCENT } from '@/lib/theme-colors';

const SUGGESTED = ['Show active fires', 'Zoom to Mumbai', 'Zoom to Tokyo', 'Hide fires', 'Analyze this location'];

function FlyTo({ target }: { target: [number, number] | null }) {
  const map = useMap();
  if (target) map.flyTo(target, 6, { duration: 1.1 });
  return null;
}

export default function MapCopilot() {
  const [input, setInput] = useState('');
  const [log, setLog] = useState<{ text: string; explanation: string; isDemo: boolean }[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFires, setShowFires] = useState(false);
  const [fires, setFires] = useState<FireDetection[]>([]);
  const [flyTarget, setFlyTarget] = useState<[number, number] | null>(null);
  const fetchedFires = useRef(false);

  const ensureFires = async () => {
    if (fetchedFires.current) return;
    fetchedFires.current = true;
    try {
      const res = await api.liveFires(1);
      setFires(res.fires);
    } catch {
      // silently leave layer empty if unavailable
    }
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    setInput('');
    setLoading(true);
    try {
      const res = await api.mapCommand(text);
      if (res.action === 'show_layer' && res.layer === 'active_fires') {
        await ensureFires();
        setShowFires(true);
      } else if (res.action === 'hide_layer' && res.layer === 'active_fires') {
        setShowFires(false);
      } else if (res.action === 'zoom_to' && res.latitude !== null && res.longitude !== null) {
        setFlyTarget([res.latitude, res.longitude]);
      }
      setLog((prev) => [...prev, { text, explanation: res.explanation, isDemo: res.is_demo }]);
    } catch (e) {
      setLog((prev) => [
        ...prev,
        { text, explanation: e instanceof ApiError ? e.message : 'Command failed.', isDemo: false },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-0px)] flex-col">
      <PageHeader title="AI Map Copilot" subtitle="Type an instruction — Gemini proposes a command, the backend validates it, the frontend executes it." />

      <div className="relative flex-1">
        <MapContainer center={[20, 10]} zoom={2} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
          <FlyTo target={flyTarget} />
          {showFires &&
            fires.map((f, i) => (
              <CircleMarker
                key={i}
                center={[f.latitude, f.longitude]}
                radius={5}
                pathOptions={{ color: PAGE_ACCENT.events, fillColor: PAGE_ACCENT.events, fillOpacity: 0.7 }}
              />
            ))}
        </MapContainer>

        <div
          className="absolute top-4 left-4 flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs shadow"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
        >
          <Flame size={13} style={{ color: showFires ? PAGE_ACCENT.events : 'var(--text-faint)' }} />
          Fires layer: {showFires ? 'on' : 'off'}
        </div>

        <div
          className="absolute right-4 bottom-4 left-4 mx-auto max-w-xl rounded-xl border shadow-lg"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
        >
          {log.length > 0 && (
            <div className="max-h-40 space-y-2 overflow-y-auto border-b p-3 text-xs" style={{ borderColor: 'var(--border)' }}>
              {log.map((entry, i) => (
                <div key={i}>
                  <p className="font-medium">"{entry.text}"</p>
                  <p style={{ color: 'var(--text-muted)' }}>
                    {entry.explanation} {entry.isDemo && <span style={{ color: PAGE_ACCENT.copilot }}>(demo parser)</span>}
                  </p>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2 p-2">
            <Bot size={16} style={{ color: PAGE_ACCENT.copilot }} className="ml-1 shrink-0" />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              placeholder="Try: show active fires, or zoom to Tokyo"
              className="flex-1 bg-transparent text-sm outline-none"
            />
            <button
              type="button"
              onClick={send}
              disabled={loading || !input.trim()}
              className="flex h-8 w-8 items-center justify-center rounded-lg disabled:opacity-50"
              style={{ background: PAGE_ACCENT.copilot, color: '#2b0518' }}
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            </button>
          </div>
          {log.length === 0 && (
            <div className="flex flex-wrap gap-1.5 px-3 pb-3">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setInput(s)}
                  className="rounded-full border px-2.5 py-1 text-[11px]"
                  style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
