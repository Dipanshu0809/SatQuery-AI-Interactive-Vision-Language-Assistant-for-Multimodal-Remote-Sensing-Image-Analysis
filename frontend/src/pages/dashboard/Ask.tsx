import { useRef, useState } from 'react';
import { Send, Loader2, Trash2, Copy, Sparkles, ImageIcon } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { ImageDropzone } from '@/components/ui/ImageDropzone';
import { api, ApiError } from '@/services/api';
import type { ChatMessage } from '@/types';

const SUGGESTED = [
  'Describe this image',
  'Identify water bodies',
  'Analyze vegetation',
  'Identify urban regions',
  'What are the major features?',
  'Is there evidence of development?',
];

export default function AskSatQuery() {
  const [file, setFile] = useState<File | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const previewUrl = file ? URL.createObjectURL(file) : null;

  const send = async (question: string) => {
    if (!file || !question.trim() || loading) return;
    setError(null);
    const userMsg: ChatMessage = { role: 'user', content: question, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await api.ask(file, question, history);
      setIsDemo(res.is_demo);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.answer, timestamp: new Date().toISOString() }]);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Unable to get an answer right now.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader title="Ask SatQuery" subtitle="Have a conversation about your satellite imagery." />

      <div className="grid gap-0 lg:grid-cols-[360px_1fr] lg:divide-x" style={{ borderColor: 'var(--border)' }}>
        {/* Image viewer */}
        <div className="space-y-4 p-6">
          {previewUrl ? (
            <div>
              <img src={previewUrl} alt="uploaded" className="w-full rounded-xl border object-cover" style={{ borderColor: 'var(--border)' }} />
              <button
                type="button"
                onClick={() => {
                  setFile(null);
                  setMessages([]);
                }}
                className="mt-2 text-xs"
                style={{ color: 'var(--text-muted)' }}
              >
                Change image
              </button>
            </div>
          ) : (
            <ImageDropzone label="Drop an image to start chatting" file={file} onFile={setFile} />
          )}

          {file && (
            <div className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <ImageIcon size={14} style={{ color: 'var(--accent)' }} />
              <span className="truncate">{file.name}</span>
            </div>
          )}
        </div>

        {/* Chat */}
        <div className="flex min-h-[60vh] flex-col p-6">
          <div className="flex-1 space-y-4 overflow-y-auto pb-4">
            {messages.length === 0 && (
              <div>
                <p className="mb-3 text-sm" style={{ color: 'var(--text-muted)' }}>
                  {file ? 'Ask anything about this image, or try a suggestion:' : 'Upload an image, then ask a question.'}
                </p>
                {file && (
                  <div className="flex flex-wrap gap-2">
                    {SUGGESTED.map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => send(q)}
                        className="rounded-full border px-3 py-1.5 text-xs"
                        style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {isDemo && messages.length > 0 && (
              <div className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs" style={{ borderColor: 'var(--color-thermal)', color: 'var(--color-thermal)' }}>
                <Sparkles size={12} /> Live AI answer
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className="group relative max-w-[85%] rounded-xl px-4 py-2.5 text-sm"
                  style={{
                    background: m.role === 'user' ? 'var(--accent)' : 'var(--surface)',
                    color: m.role === 'user' ? 'var(--accent-contrast)' : 'var(--text)',
                    border: m.role === 'assistant' ? '1px solid var(--border)' : 'none',
                  }}
                >
                  {m.content}
                  {m.role === 'assistant' && (
                    <button
                      type="button"
                      onClick={() => navigator.clipboard.writeText(m.content)}
                      className="absolute -bottom-2 -right-2 hidden h-6 w-6 items-center justify-center rounded-full border group-hover:flex"
                      style={{ borderColor: 'var(--border)', background: 'var(--bg)', color: 'var(--text-muted)' }}
                      aria-label="Copy"
                    >
                      <Copy size={11} />
                    </button>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                <Loader2 size={14} className="animate-spin" /> Consulting SatQuery AI…
              </div>
            )}

            {error && (
              <div className="rounded-lg border p-3 text-sm" style={{ borderColor: 'var(--color-alert)', color: 'var(--color-alert)' }}>
                {error}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="mt-auto flex items-center gap-2 border-t pt-4" style={{ borderColor: 'var(--border)' }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send(input)}
              placeholder={file ? 'Ask a question about this image…' : 'Upload an image first'}
              disabled={!file}
              className="flex-1 rounded-lg border px-3 py-2.5 text-sm outline-none disabled:opacity-50"
              style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
            />
            {messages.length > 0 && (
              <button
                type="button"
                onClick={() => setMessages([])}
                className="flex h-10 w-10 items-center justify-center rounded-lg border"
                style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
                aria-label="Clear conversation"
              >
                <Trash2 size={15} />
              </button>
            )}
            <button
              type="button"
              onClick={() => send(input)}
              disabled={!file || !input.trim() || loading}
              className="flex h-10 w-10 items-center justify-center rounded-lg disabled:opacity-50"
              style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
              aria-label="Send"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
