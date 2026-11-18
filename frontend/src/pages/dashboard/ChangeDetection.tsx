import { useState } from 'react';
import { Loader2, GitCompareArrows, Sparkles } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { ImageDropzone } from '@/components/ui/ImageDropzone';
import { CompareSlider } from '@/components/ui/CompareSlider';
import { api, ApiError } from '@/services/api';

interface ChangeResult {
  id: string;
  change_percentage: number | null;
  changed_regions: string[];
  summary: string;
  is_demo: boolean;
  heatmap_url: string;
  image_a_url: string;
  image_b_url: string;
}

export default function ChangeDetection() {
  const [imageA, setImageA] = useState<File | null>(null);
  const [imageB, setImageB] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChangeResult | null>(null);

  const run = async () => {
    if (!imageA || !imageB) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.changeDetection(imageA, imageB);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Unable to run change detection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader title="Change Detection" subtitle="Compare two images of the same location to detect real change." />

      <div className="space-y-6 p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <ImageDropzone label="Image A (earlier)" file={imageA} onFile={setImageA} />
          <ImageDropzone label="Image B (later)" file={imageB} onFile={setImageB} />
        </div>

        <button
          type="button"
          onClick={run}
          disabled={!imageA || !imageB || loading}
          className="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-50"
          style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <GitCompareArrows size={15} />}
          Run Change Detection
        </button>

        {error && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
            {error}
          </div>
        )}

        {loading && (
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Analyzing satellite features…</p>
        )}

        {result && !loading && (
          <div className="space-y-5">
            {result.is_demo && (
              <div className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs" style={{ borderColor: 'var(--color-thermal)', color: 'var(--color-thermal)' }}>
                <Sparkles size={12} /> Live AI narrative + computed change percentage
              </div>
            )}

            <div>
              <h3 className="mb-2 text-sm font-medium">Before / After comparison</h3>
              <CompareSlider beforeUrl={api.resolveUrl(result.image_a_url)!} afterUrl={api.resolveUrl(result.image_b_url)!} />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                <h3 className="mb-2 text-sm font-medium">Difference heatmap</h3>
                <img src={api.resolveUrl(result.heatmap_url)!} alt="heatmap" className="w-full rounded-lg border" style={{ borderColor: 'var(--border)' }} />
              </div>

              <div className="space-y-4">
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Change percentage (computed)</span>
                  <div className="mt-1 text-3xl font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--accent)' }}>
                    {result.change_percentage !== null ? `${result.change_percentage}%` : 'N/A'}
                  </div>
                </div>
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <h3 className="mb-2 text-sm font-medium">AI Summary</h3>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{result.summary}</p>
                </div>
              </div>
            </div>

            {result.changed_regions.length > 0 && (
              <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                <h3 className="mb-3 text-sm font-medium">Changed regions</h3>
                <ul className="space-y-2">
                  {result.changed_regions.map((r, i) => (
                    <li key={i} className="flex gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                      <span style={{ color: 'var(--color-thermal)' }}>•</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
