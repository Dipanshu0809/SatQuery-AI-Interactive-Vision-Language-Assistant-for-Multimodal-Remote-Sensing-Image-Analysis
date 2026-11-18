import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { AppMode } from '@/types';

interface BackendStatusState {
  status: 'checking' | 'connected' | 'offline';
  mode: AppMode | null;
  gemini_connected: boolean | null;
}

export function useBackendStatus() {
  const [state, setState] = useState<BackendStatusState>({
    status: 'checking',
    mode: null,
    gemini_connected: null,
  });

  useEffect(() => {
    let cancelled = false;
    api
      .health()
      .then((res) => {
        if (!cancelled) setState({ status: 'connected', mode: res.mode, gemini_connected: res.gemini_connected });
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'offline', mode: null, gemini_connected: null });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
