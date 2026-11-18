import { useEffect, useState } from 'react';
import { Loader2, Trash2, Download, ScanSearch, GitCompareArrows, MessagesSquare, Inbox } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { api, ApiError } from '@/services/api';
import type { HistoryRecord } from '@/types';

const TYPE_ICON: Record<string, typeof ScanSearch> = {
  analysis: ScanSearch,
  ask: MessagesSquare,
  change_detection: GitCompareArrows,
};

export default function History() {
  const [items, setItems] = useState<HistoryRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = () => {
    api
      .history()
      .then(setItems)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Could not load history.'));
  };

  useEffect(load, []);

  const remove = async (id: string) => {
    setBusyId(id);
    try {
      await api.deleteHistory(id);
      setItems((prev) => prev?.filter((i) => i.id !== id) ?? null);
    } catch {
      setError('Could not delete this item.');
    } finally {
      setBusyId(null);
    }
  };

  const downloadReport = async (id: string) => {
    setBusyId(id);
    try {
      const blob = await api.report(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SatQueryAI-Report-${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Could not generate the report.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <PageHeader title="History" subtitle="Every analysis is saved automatically." />

      <div className="p-6">
        {!items && !error && (
          <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
            <Loader2 size={14} className="animate-spin" /> Loading history…
          </div>
        )}

        {error && (
          <div className="rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
            {error}
          </div>
        )}

        {items && items.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-16 text-center">
            <Inbox size={22} style={{ color: 'var(--text-faint)' }} />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No analyses yet — run one from Image Analysis or Change Detection.</p>
          </div>
        )}

        {items && items.length > 0 && (
          <div className="space-y-2">
            {items.map((item) => {
              const Icon = TYPE_ICON[item.analysis_type] ?? ScanSearch;
              return (
                <div
                  key={item.id}
                  className="flex items-center gap-4 rounded-xl border p-4"
                  style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg" style={{ background: 'var(--surface-2)', color: 'var(--accent)' }}>
                    <Icon size={16} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium">{item.filename}</span>
                      <span
                        className="shrink-0 rounded-full px-2 py-0.5 text-[10px] uppercase"
                        style={{ background: 'var(--surface-2)', color: 'var(--text-faint)' }}
                      >
                        {item.analysis_type.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="mt-0.5 truncate text-xs" style={{ color: 'var(--text-muted)' }}>
                      {item.summary || 'No summary available'}
                    </p>
                    <p className="mt-0.5 text-[11px]" style={{ color: 'var(--text-faint)', fontFamily: 'var(--font-data)' }}>
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => downloadReport(item.id)}
                      disabled={busyId === item.id}
                      className="flex h-8 w-8 items-center justify-center rounded-lg border disabled:opacity-50"
                      style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
                      aria-label="Download report"
                    >
                      <Download size={14} />
                    </button>
                    <button
                      type="button"
                      onClick={() => remove(item.id)}
                      disabled={busyId === item.id}
                      className="flex h-8 w-8 items-center justify-center rounded-lg border disabled:opacity-50"
                      style={{ borderColor: 'var(--border)', color: 'var(--color-alert)' }}
                      aria-label="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
