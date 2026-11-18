import { useRef, useState } from 'react';
import { MoveHorizontal } from 'lucide-react';

export function CompareSlider({ beforeUrl, afterUrl }: { beforeUrl: string; afterUrl: string }) {
  const [pos, setPos] = useState(50);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const updateFromClientX = (clientX: number) => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setPos(Math.min(100, Math.max(0, pct)));
  };

  return (
    <div
      ref={containerRef}
      className="relative aspect-video w-full select-none overflow-hidden rounded-xl border"
      style={{ borderColor: 'var(--border)' }}
      onMouseMove={(e) => dragging.current && updateFromClientX(e.clientX)}
      onMouseUp={() => (dragging.current = false)}
      onMouseLeave={() => (dragging.current = false)}
      onTouchMove={(e) => updateFromClientX(e.touches[0].clientX)}
    >
      <img src={afterUrl} alt="after" className="absolute inset-0 h-full w-full object-cover" draggable={false} />
      <div className="absolute inset-0 overflow-hidden" style={{ width: `${pos}%` }}>
        <img
          src={beforeUrl}
          alt="before"
          className="h-full object-cover"
          style={{ width: containerRef.current?.clientWidth ?? '100%' }}
          draggable={false}
        />
      </div>

      <div
        className="absolute inset-y-0 flex w-0.5 cursor-ew-resize items-center justify-center"
        style={{ left: `${pos}%`, background: 'var(--accent)' }}
        onMouseDown={() => (dragging.current = true)}
        onTouchStart={() => (dragging.current = true)}
      >
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full shadow"
          style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
        >
          <MoveHorizontal size={15} />
        </div>
      </div>

      <span className="absolute top-2 left-2 rounded-md px-2 py-0.5 text-xs" style={{ background: 'rgba(0,0,0,0.55)', color: '#fff' }}>
        Before
      </span>
      <span className="absolute top-2 right-2 rounded-md px-2 py-0.5 text-xs" style={{ background: 'rgba(0,0,0,0.55)', color: '#fff' }}>
        After
      </span>
    </div>
  );
}
