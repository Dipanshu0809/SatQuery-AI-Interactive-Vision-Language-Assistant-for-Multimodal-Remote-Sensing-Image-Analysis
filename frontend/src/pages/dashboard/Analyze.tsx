import { useState } from 'react';
import { Loader2, Download, ScanSearch, RotateCcw, Sparkles } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { PageHeader } from '@/components/ui/PageHeader';
import { ImageDropzone } from '@/components/ui/ImageDropzone';
import { api, ApiError } from '@/services/api';
import type { AnalysisResult } from '@/types';

const LC_COLORS: Record<string, string> = {
  vegetation: 'var(--color-vegetation)',
  water: 'var(--color-water)',
  built_up: 'var(--color-thermal)',
  bare_land: 'var(--text-faint)',
};

export default function ImageAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  const runAnalysis = async (f: File) => {
    setFile(f);
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await api.analyze(f);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Unable to analyze this image.');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async () => {
    if (!result) return;
    setReportLoading(true);
    try {
      const blob = await api.report(result.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SatQueryAI-Report-${result.id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Could not generate the report. Please try again.');
    } finally {
      setReportLoading(false);
    }
  };

  const landCoverData = result?.land_cover
    ? Object.entries(result.land_cover)
        .filter(([, v]) => v !== null && v !== undefined)
        .map(([key, value]) => ({ key, name: key.replace('_', ' '), value: value as number }))
    : [];

  return (
    <div>
      <PageHeader title="Image Analysis" subtitle="Upload satellite imagery for AI-powered analysis." />

      <div className="grid gap-6 p-6 lg:grid-cols-[380px_1fr]">
        <div className="space-y-4">
          <ImageDropzone file={file} onFile={runAnalysis} />
          {file && !loading && (
            <button
              type="button"
              onClick={() => runAnalysis(file)}
              className="flex w-full items-center justify-center gap-2 rounded-lg border py-2 text-sm"
              style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
            >
              <RotateCcw size={14} /> Re-analyze
            </button>
          )}
          {file && (
            <div className="rounded-lg border p-3 text-xs" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <div className="flex justify-between py-0.5">
                <span style={{ color: 'var(--text-muted)' }}>Filename</span>
                <span className="truncate pl-2">{file.name}</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span style={{ color: 'var(--text-muted)' }}>Size</span>
                <span>{(file.size / 1024).toFixed(0)} KB</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span style={{ color: 'var(--text-muted)' }}>Format</span>
                <span>{file.type || 'unknown'}</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span style={{ color: 'var(--text-muted)' }}>Status</span>
                <span style={{ color: loading ? 'var(--color-thermal)' : 'var(--color-vegetation)' }}>
                  {loading ? 'Processing…' : result ? 'Complete' : 'Ready'}
                </span>
              </div>
            </div>
          )}
        </div>

        <div>
          {loading && (
            <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-xl border" style={{ borderColor: 'var(--border)' }}>
              <Loader2 className="animate-spin" size={22} style={{ color: 'var(--accent)' }} />
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Consulting SatQuery AI…</p>
            </div>
          )}

          {error && !loading && (
            <div className="rounded-xl border p-4 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
              {error}
            </div>
          )}

          {!loading && !result && !error && (
            <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-xl border text-center" style={{ borderColor: 'var(--border)' }}>
              <ScanSearch size={22} style={{ color: 'var(--text-faint)' }} />
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                Upload an image to see AI analysis results here.
              </p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5">
              {result.is_demo && (
                <div className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs" style={{ borderColor: 'var(--color-thermal)', color: 'var(--color-thermal)' }}>
                  <Sparkles size={12} /> Live AI analysis
                </div>
              )}

              <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                <h3 className="mb-2 text-sm font-medium">AI Summary</h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{result.summary}</p>
              </div>

              {landCoverData.length > 0 && (
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <h3 className="mb-4 text-sm font-medium">Land Cover</h3>
                  <div className="flex flex-col items-center gap-4 sm:flex-row">
                    <ResponsiveContainer width={180} height={180}>
                      <PieChart>
                        <Pie data={landCoverData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} paddingAngle={2}>
                          {landCoverData.map((d) => (
                            <Cell key={d.key} fill={LC_COLORS[d.key] ?? 'var(--text-faint)'} stroke="none" />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="grid flex-1 grid-cols-2 gap-2">
                      {landCoverData.map((d) => (
                        <div key={d.key} className="rounded-lg p-2.5 text-xs" style={{ background: 'var(--surface-2)' }}>
                          <div className="flex items-center gap-1.5" style={{ color: 'var(--text-muted)' }}>
                            <span className="h-2 w-2 rounded-full" style={{ background: LC_COLORS[d.key] }} />
                            {d.name}
                          </div>
                          <div className="mt-0.5 text-base font-semibold">{d.value}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {result.cv_metrics && (
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium">Computer Vision Analysis</h3>
                      <p className="mt-1 text-xs" style={{ color: 'var(--text-faint)' }}>
                        OpenCV scene measurements and candidate-region detection. These are visual CV signals, not semantic ground truth.
                      </p>
                    </div>
                    <span className="rounded-full border px-2 py-1 text-[10px]" style={{ borderColor: 'var(--border)', color: 'var(--accent)' }}>CV BASELINE</span>
                  </div>
                  {result.cv_metrics.overlay_url && (
                    <img src={api.resolveUrl(result.cv_metrics.overlay_url)!} alt="Computer vision candidate region overlay" className="mb-4 w-full rounded-lg border" style={{ borderColor: 'var(--border)' }} />
                  )}
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    {[
                      ['Candidates', result.cv_metrics.candidate_count],
                      ['Brightness', result.cv_metrics.brightness ?? '—'],
                      ['Contrast', result.cv_metrics.contrast ?? '—'],
                      ['Edge density', result.cv_metrics.edge_density_pct != null ? `${result.cv_metrics.edge_density_pct}%` : '—'],
                    ].map(([label, value]) => (
                      <div key={String(label)} className="rounded-lg p-3" style={{ background: 'var(--surface-2)' }}>
                        <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-faint)' }}>{label}</div>
                        <div className="mt-1 text-base font-semibold" style={{ fontFamily: 'var(--font-data)' }}>{value}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 text-xs" style={{ color: 'var(--text-muted)' }}>Scene profile: <strong>{result.cv_metrics.scene_profile ?? '—'}</strong></div>
                </div>
              )}

              {result.observations.length > 0 && (
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <h3 className="mb-3 text-sm font-medium">Key Observations</h3>
                  <ul className="space-y-2">
                    {result.observations.map((obs, i) => (
                      <li key={i} className="flex gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                        <span style={{ color: 'var(--accent)' }}>•</span>
                        {obs}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.confidence !== null && (
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-medium">AI Confidence</span>
                    <span style={{ fontFamily: 'var(--font-data)' }}>{Math.round((result.confidence ?? 0) * 100)}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full" style={{ background: 'var(--surface-2)' }}>
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${Math.round((result.confidence ?? 0) * 100)}%`, background: 'var(--accent)' }}
                    />
                  </div>
                </div>
              )}

              <button
                type="button"
                onClick={downloadReport}
                disabled={reportLoading}
                className="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-60"
                style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
              >
                {reportLoading ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />}
                Download Report
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
