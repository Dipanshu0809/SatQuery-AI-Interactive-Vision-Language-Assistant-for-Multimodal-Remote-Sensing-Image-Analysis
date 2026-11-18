import type { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { AmbientBackground } from '@/components/three/AmbientBackground';
import { PAGE_ACCENT, type PageKey } from '@/lib/theme-colors';

function pageKeyFromPath(pathname: string): PageKey {
  if (pathname.startsWith('/dashboard/analyze')) return 'analyze';
  if (pathname.startsWith('/dashboard/ask')) return 'ask';
  if (pathname.startsWith('/dashboard/change')) return 'change';
  if (pathname.startsWith('/dashboard/map')) return 'map';
  if (pathname.startsWith('/dashboard/reports')) return 'reports';
  if (pathname.startsWith('/dashboard/history')) return 'history';
  if (pathname.startsWith('/dashboard/settings')) return 'settings';
  if (pathname.startsWith('/dashboard/live-earth')) return 'liveearth';
  if (pathname.startsWith('/dashboard/events')) return 'events';
  if (pathname.startsWith('/dashboard/monitoring')) return 'monitoring';
  if (pathname.startsWith('/dashboard/analyst')) return 'analyst';
  if (pathname.startsWith('/dashboard/mission')) return 'mission';
  if (pathname.startsWith('/dashboard/copilot')) return 'copilot';
  if (pathname.startsWith('/dashboard/time-machine')) return 'timemachine';
  if (pathname.startsWith('/dashboard/vegetation')) return 'vegetation';
  if (pathname.startsWith('/dashboard/water')) return 'water';
  if (pathname.startsWith('/dashboard/night-lights')) return 'nightlights';
  return 'dashboard';
}

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const accent = PAGE_ACCENT[pageKeyFromPath(location.pathname)];

  return (
    <div className="flex h-screen flex-col md:flex-row">
      <AmbientBackground accent={accent} />
      <Sidebar />
      <main className="relative flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
