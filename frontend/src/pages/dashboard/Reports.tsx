import { useEffect, useState } from 'react';
import { Loader2, FileText, Download, Inbox } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { api, ApiError } from '@/services/api';
import type { HistoryRecord } from '@/types';

export default function Reports() {
  const [items, setItems] = useState<HistoryRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    api
      .history()
      .then(setItems)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Could not load analyses.'));
  }, []);

  const generate = async (id: string) => {
    setBusyId(id);
    setError(null);
    try {
      const blob = await api.report(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SatQueryAI-Report-${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Could not generate the report. Please try again.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <PageHeader title="Reports" subtitle="Generate a professional PDF report for any past analysis." />

      <div className="p-6">
        {!items && !error && (
          <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin" /> Loading analyses…
          </div>
        )}

        {error && (
          <div className="mb-4 rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
            {error}
          </div>
        )}

        {items && items.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-16 text-center">
            <Inbox size={22} style={{ color: 'var(--text-faint)' }} />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              No analyses to report on yet. Run an analysis first.
            </p>
          </div>
        )}

        {items && items.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <div key={item.id} className="rounded-xl border p-4" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: 'var(--surface-2)', color: 'var(--accent)' }}>
                  <FileText size={16} />
                </div>
                <p className="truncate text-sm font-medium">{item.filename}</p>
                <p className="mt-1 line-clamp-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                  {item.summary || 'No summary available'}
                </p>
                <button
                  type="button"
                  onClick={() => generate(item.id)}
                  disabled={busyId === item.id}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg py-2 text-xs font-medium disabled:opacity-60"
                  style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
                >
                  {busyId === item.id ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
                  Generate & Download
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
