import { CircleCheck, CircleAlert, Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { useBackendStatus } from '@/hooks/useBackendStatus';

export default function Settings() {
  const status = useBackendStatus();

  return (
    <div>
      <PageHeader title="Settings" subtitle="Configure appearance and review system status." />

      <div className="max-w-2xl space-y-6 p-6">
        <section className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          <h3 className="mb-3 text-sm font-medium">Appearance</h3>
          <div className="flex items-center justify-between">
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Theme</span>
            <ThemeToggle />
          </div>
        </section>

        <section className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          <h3 className="mb-3 text-sm font-medium">AI Configuration</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span style={{ color: 'var(--text-muted)' }}>Backend status</span>
              <span className="flex items-center gap-1.5">
                {status.status === 'checking' && <Loader2 size={13} className="animate-spin" style={{ color: 'var(--text-muted)' }} />}
                {status.status === 'connected' && <CircleCheck size={13} style={{ color: 'var(--color-vegetation)' }} />}
                {status.status === 'offline' && <CircleAlert size={13} style={{ color: 'var(--color-alert)' }} />}
                {status.status === 'connected' ? 'Online' : status.status === 'checking' ? 'Checking…' : 'Offline'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span style={{ color: 'var(--text-muted)' }}>Mode</span>
              <span style={{ fontFamily: 'var(--font-data)' }}>
                {status.mode ?? '—'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span style={{ color: 'var(--text-muted)' }}>Gemini connection</span>
              <span>{status.gemini_connected ? 'Connected' : 'API key required'}</span>
            </div>

          </div>
        </section>

        <section className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          <h3 className="mb-2 text-sm font-medium">About SatQuery AI</h3>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
            SatQuery AI is a multimodal remote sensing assistant for satellite image analysis,
            question answering, and change detection. Built with React, FastAPI, and Google Gemini.
          </p>
        </section>
      </div>
    </div>
  );
}
