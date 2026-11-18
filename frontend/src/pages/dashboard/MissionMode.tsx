import { useState } from 'react';
import { Rocket, Loader2, CheckCircle2, XCircle, AlertTriangle, Sparkles, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageHeader } from '@/components/ui/PageHeader';
import { api, ApiError } from '@/services/api';
import type { MissionResult } from '@/types';
import { PAGE_ACCENT } from '@/lib/theme-colors';
import { ScanningGlobe } from '@/components/three/ScanningGlobe';

export default function MissionMode() {
  const [objective, setObjective] = useState('Investigate environmental changes around Amritsar');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MissionResult | null>(null);
  const [visibleSteps, setVisibleSteps] = useState(0);
  const [downloadingReport, setDownloadingReport] = useState(false);

  const downloadReport = async () => {
    if (!result?.report) return;
    setDownloadingReport(true);
    try {
      const blob = await api.missionReport(result.report);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'SatQueryAI-Investigation-Report.pdf';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Could not generate the investigation report.');
    } finally {
      setDownloadingReport(false);
    }
  };

  const run = async () => {
    if (!objective.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setVisibleSteps(0);
    try {
      const res = await api.missionInvestigate(objective);
      setResult(res);
      // reveal steps one at a time for the "workflow in progress" feel
      res.steps.forEach((_, i) => {
        setTimeout(() => setVisibleSteps((v) => Math.max(v, i + 1)), i * 350);
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Mission could not be started.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader title="Mission Mode" subtitle="Give SatQuery AI a natural-language objective and let it run a structured investigation." />

      <div className="max-w-2xl space-y-4 p-6">
        <textarea
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          rows={2}
          className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
          placeholder="e.g. Investigate environmental changes around Amritsar"
        />

        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={run}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-50"
            style={{ background: PAGE_ACCENT.mission, color: '#241c00' }}
          >
            {loading ? <Loader2 size={15} className="animate-spin" /> : <Rocket size={15} />}
            Launch Investigation
          </button>
          {(loading || result) && <ScanningGlobe color={PAGE_ACCENT.mission} active={loading} />}
        </div>

        {error && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="space-y-1.5 rounded-xl border p-4" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <AnimatePresence>
                {result.steps.slice(0, visibleSteps).map((step, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-start gap-2 text-sm"
                  >
                    {step.status === 'done' ? (
                      <CheckCircle2 size={15} className="mt-0.5 shrink-0" style={{ color: 'var(--color-vegetation)' }} />
                    ) : step.status === 'warning' ? (
                      <AlertTriangle size={15} className="mt-0.5 shrink-0" style={{ color: 'var(--color-amber)' }} />
                    ) : (
                      <XCircle size={15} className="mt-0.5 shrink-0" style={{ color: 'var(--color-alert)' }} />
                    )}
                    <div>
                      <span>{step.label}</span>
                      {step.detail && <p className="text-xs" style={{ color: 'var(--text-faint)' }}>{step.detail}</p>}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {result.report && visibleSteps >= result.steps.length && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                {result.report.is_demo && (
                  <div className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs" style={{ borderColor: PAGE_ACCENT.mission, color: PAGE_ACCENT.mission }}>
                    <Sparkles size={12} /> Live evidence used
                  </div>
                )}
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <h3 className="mb-2 text-sm font-medium">Investigation summary</h3>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{result.report.summary}</p>
                </div>
                <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium">Earth Change Index</h3>
                    <span
                      className="rounded-full px-2.5 py-0.5 text-xs font-medium"
                      style={{ background: 'var(--surface-2)', color: PAGE_ACCENT.mission }}
                    >
                      {result.report.change_index.score === null
                        ? result.report.change_index.label
                        : `${result.report.change_index.label} · ${result.report.change_index.score}/100`}
                    </span>
                  </div>
                  <p className="mt-2 text-xs" style={{ color: 'var(--text-faint)' }}>{result.report.change_index.methodology}</p>
                </div>
                <button
                  type="button"
                  onClick={downloadReport}
                  disabled={downloadingReport}
                  className="flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-60"
                  style={{ background: PAGE_ACCENT.mission, color: '#241c00' }}
                >
                  {downloadingReport ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />}
                  Download Investigation Report
                </button>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
