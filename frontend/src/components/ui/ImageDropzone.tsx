import { useCallback, useRef, useState } from 'react';
import { UploadCloud, ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImageDropzoneProps {
  label?: string;
  file: File | null;
  onFile: (file: File) => void;
  compact?: boolean;
}

const ACCEPTED = ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff'];

export function ImageDropzone({ label, file, onFile, compact }: ImageDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const previewUrl = file ? URL.createObjectURL(file) : null;

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const f = files?.[0];
      if (!f) return;
      if (!ACCEPTED.includes(f.type)) return;
      onFile(f);
    },
    [onFile],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={cn(
        'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed text-center transition-colors',
        compact ? 'p-4' : 'p-10',
      )}
      style={{
        borderColor: dragOver ? 'var(--accent)' : 'var(--border-strong)',
        background: dragOver ? 'var(--surface-2)' : 'var(--surface)',
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(',')}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {previewUrl ? (
        <img
          src={previewUrl}
          alt={file?.name ?? 'preview'}
          className={cn('rounded-lg object-cover', compact ? 'h-24 w-full' : 'h-48 w-full max-w-md')}
        />
      ) : (
        <>
          <div
            className="flex h-11 w-11 items-center justify-center rounded-full"
            style={{ background: 'var(--surface-2)', color: 'var(--accent)' }}
          >
            {compact ? <ImageIcon size={18} /> : <UploadCloud size={20} />}
          </div>
          <p className="text-sm font-medium">{label ?? 'Drop satellite imagery here'}</p>
          {!compact && (
            <p className="text-xs" style={{ color: 'var(--text-faint)' }}>
              PNG, JPG, JPEG, or TIFF
            </p>
          )}
        </>
      )}

      {file && (
        <p className="max-w-full truncate text-xs" style={{ color: 'var(--text-muted)' }}>
          {file.name} · {(file.size / 1024).toFixed(0)} KB
        </p>
      )}
    </div>
  );
}
