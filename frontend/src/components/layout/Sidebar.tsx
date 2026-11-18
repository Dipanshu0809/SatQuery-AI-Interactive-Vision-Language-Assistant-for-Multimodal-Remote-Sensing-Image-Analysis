import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Satellite,
  LayoutGrid,
  ScanSearch,
  MessagesSquare,
  GitCompareArrows,
  Map,
  FileText,
  History,
  Settings,
  ChevronsLeft,
  ChevronsRight,
  Menu,
  X,
  CircleDot,
  Globe2,
  Flame,
  BellRing,
  Brain,
  Rocket,
  Bot,
  Clock,
  Sprout,
  Droplets,
  Moon,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { cn } from '@/lib/utils';
import { useBackendStatus } from '@/hooks/useBackendStatus';
import { PAGE_ACCENT, type PageKey } from '@/lib/theme-colors';

type NavItem = { to: string; label: string; icon: typeof LayoutGrid; end?: boolean; key: PageKey };

const NAV_GROUPS: { section: string; items: NavItem[] }[] = [
  {
    section: '',
    items: [{ to: '/dashboard', label: 'Dashboard', icon: LayoutGrid, end: true, key: 'dashboard' }],
  },
  {
    section: 'Analyze',
    items: [
      { to: '/dashboard/analyze', label: 'Image Analysis', icon: ScanSearch, key: 'analyze' },
      { to: '/dashboard/ask', label: 'Ask SatQuery', icon: MessagesSquare, key: 'ask' },
      { to: '/dashboard/change', label: 'Change Detection', icon: GitCompareArrows, key: 'change' },
    ],
  },
  {
    section: 'Live Earth',
    items: [
      { to: '/dashboard/live-earth', label: 'Live Earth', icon: Globe2, key: 'liveearth' },
      { to: '/dashboard/events', label: 'Events', icon: Flame, key: 'events' },
      { to: '/dashboard/monitoring', label: 'Monitoring', icon: BellRing, key: 'monitoring' },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { to: '/dashboard/analyst', label: 'Earth Analyst', icon: Brain, key: 'analyst' },
      { to: '/dashboard/mission', label: 'Mission Mode', icon: Rocket, key: 'mission' },
      { to: '/dashboard/copilot', label: 'AI Map Copilot', icon: Bot, key: 'copilot' },
      { to: '/dashboard/map', label: 'Satellite Map', icon: Map, key: 'map' },
      { to: '/dashboard/time-machine', label: 'Time Machine', icon: Clock, key: 'timemachine' },
    ],
  },
  {
    section: 'Insights',
    items: [
      { to: '/dashboard/vegetation', label: 'Vegetation', icon: Sprout, key: 'vegetation' },
      { to: '/dashboard/water', label: 'Water Intelligence', icon: Droplets, key: 'water' },
      { to: '/dashboard/night-lights', label: 'Night Lights', icon: Moon, key: 'nightlights' },
    ],
  },
  {
    section: 'System',
    items: [
      { to: '/dashboard/reports', label: 'Reports', icon: FileText, key: 'reports' },
      { to: '/dashboard/history', label: 'History', icon: History, key: 'history' },
      { to: '/dashboard/settings', label: 'Settings', icon: Settings, key: 'settings' },
    ],
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const status = useBackendStatus();

  const content = (
    <>
      <div
        className="flex items-center gap-2 px-4 py-5"
        style={{ fontFamily: 'var(--font-display)' }}
      >
        <Satellite size={20} style={{ color: 'var(--accent)' }} strokeWidth={2.2} />
        {!collapsed && <span className="text-sm font-semibold tracking-tight">SATQUERY AI</span>}
      </div>

      <nav className="flex-1 space-y-3 overflow-y-auto px-2 pb-2">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi}>
            {group.section && !collapsed && (
              <div
                className="px-3 pt-2 pb-1 text-[10px] font-medium tracking-wider uppercase"
                style={{ color: 'var(--text-faint)' }}
              >
                {group.section}
              </div>
            )}
            <div className="space-y-0.5">
              {group.items.map(({ to, label, icon: Icon, end, key }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors"
                  style={({ isActive }) => ({
                    color: isActive ? PAGE_ACCENT[key] : 'var(--text-muted)',
                    background: isActive ? 'var(--surface-2)' : 'transparent',
                    fontWeight: isActive ? 500 : 400,
                    borderLeft: isActive ? `2px solid ${PAGE_ACCENT[key]}` : '2px solid transparent',
                  })}
                  title={collapsed ? label : undefined}
                >
                  <Icon size={17} strokeWidth={2} />
                  {!collapsed && <span>{label}</span>}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="space-y-3 border-t px-3 py-4" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2 px-1 text-xs" style={{ color: 'var(--text-faint)' }}>
          <CircleDot
            size={10}
            style={{
              color: status.status === 'connected' ? 'var(--color-vegetation)' : 'var(--color-alert)',
            }}
          />
          {!collapsed && (
            <span>
              {status.status === 'connected'
                ? `Backend online \u00b7 ${status.mode ?? 'demo'} mode`
                : status.status === 'checking'
                  ? 'Connecting\u2026'
                  : 'Backend offline'}
            </span>
          )}
        </div>
        <div className={cn('flex items-center', collapsed ? 'justify-center' : 'justify-between')}>
          {!collapsed && <ThemeToggle />}
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="hidden h-7 w-7 items-center justify-center rounded-md md:flex"
            style={{ color: 'var(--text-muted)' }}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
          </button>
        </div>
      </div>
    </>
  );

  return (
    <>
      <div
        className="flex items-center justify-between border-b px-4 py-3 md:hidden"
        style={{ borderColor: 'var(--border)', background: 'var(--bg)' }}
      >
        <div className="flex items-center gap-2" style={{ fontFamily: 'var(--font-display)' }}>
          <Satellite size={18} style={{ color: 'var(--accent)' }} />
          <span className="text-sm font-semibold">SATQUERY AI</span>
        </div>
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation"
          style={{ color: 'var(--text-muted)' }}
        >
          <Menu size={20} />
        </button>
      </div>

      <motion.aside
        animate={{ width: collapsed ? 68 : 240 }}
        transition={{ type: 'tween', duration: 0.18 }}
        className="hidden shrink-0 flex-col border-r md:flex"
        style={{ borderColor: 'var(--border)', background: 'var(--bg-elevated)' }}
      >
        {content}
      </motion.aside>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/40 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col md:hidden"
              style={{ background: 'var(--bg-elevated)' }}
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'tween', duration: 0.2 }}
            >
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="absolute top-4 right-3"
                style={{ color: 'var(--text-muted)' }}
                aria-label="Close navigation"
              >
                <X size={18} />
              </button>
              {content}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
