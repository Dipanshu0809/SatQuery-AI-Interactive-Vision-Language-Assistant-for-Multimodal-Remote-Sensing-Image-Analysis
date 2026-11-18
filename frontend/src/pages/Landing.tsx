import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Satellite,
  ArrowRight,
  ScanSearch,
  MessagesSquare,
  GitCompareArrows,
  Map,
  FileText,
  History,
  Leaf,
  Droplets,
  CircleCheck,
  Radio,
  Orbit,
  Activity,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { AmbientBackground } from '@/components/three/AmbientBackground';
import { HeroGlobe } from '@/components/three/HeroGlobe';
import { PAGE_ACCENT } from '@/lib/theme-colors';

const TECH = ['Gemini', 'FastAPI', 'React', 'PyTorch', 'Computer Vision', 'Geospatial AI'];

const FEATURES = [
  { icon: ScanSearch, title: 'AI Image Analysis', desc: 'Upload satellite imagery and get an instant AI-generated summary, land-cover breakdown, and confidence score.', color: PAGE_ACCENT.analyze },
  { icon: MessagesSquare, title: 'Multimodal Q&A', desc: 'Ask natural-language questions about any image and get grounded, image-specific answers.', color: PAGE_ACCENT.ask },
  { icon: GitCompareArrows, title: 'Change Detection', desc: 'Compare two images of the same location and get a real, computed change percentage with a visual heatmap.', color: PAGE_ACCENT.change },
  { icon: Map, title: 'Geospatial Intelligence', desc: 'Explore locations on an interactive map with coordinate and area context.', color: PAGE_ACCENT.map },
  { icon: FileText, title: 'AI Reports', desc: 'Generate a polished PDF report summarizing any analysis, ready to share or archive.', color: PAGE_ACCENT.reports },
  { icon: History, title: 'Analysis History', desc: 'Every analysis is saved automatically so you can revisit, compare, or re-export it later.', color: PAGE_ACCENT.history },
];

const STEPS = ['Upload Image', 'AI Analysis', 'Ask Questions', 'Discover Insights'];

const FLOAT_CARDS = [
  { label: 'Vegetation detected', icon: Leaf, color: 'var(--color-vegetation)', pos: 'top-6 -left-6 md:-left-16' },
  { label: 'Water body identified', icon: Droplets, color: 'var(--color-water)', pos: 'top-24 -right-4 md:-right-20' },
  { label: 'Change detected', icon: GitCompareArrows, color: 'var(--color-thermal)', pos: 'bottom-24 -left-8 md:-left-24' },
  { label: 'AI analysis complete', icon: CircleCheck, color: 'var(--accent)', pos: 'bottom-4 -right-2 md:-right-16' },
];

export default function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden">
      <AmbientBackground accent={PAGE_ACCENT.landing} />
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2 font-medium" style={{ fontFamily: 'var(--font-display)' }}>
          <Satellite size={20} style={{ color: 'var(--accent)' }} />
          <span>SatQuery AI</span>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link
            to="/dashboard"
            className="rounded-lg px-4 py-2 text-sm font-medium"
            style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
          >
            Start Analyzing
          </Link>
        </div>
      </header>

      <section className="relative mx-auto max-w-3xl px-6 pt-20 pb-40 text-center">
        <svg
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 mx-auto opacity-[0.07]"
          width="900"
          height="500"
          viewBox="0 0 900 500"
        >
          {[80, 130, 180, 230, 280].map((r, i) => (
            <ellipse key={i} cx="450" cy="200" rx={r * 2.4} ry={r} fill="none" stroke="var(--accent)" strokeWidth="1" />
          ))}
        </svg>

        <motion.span
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 inline-block rounded-full border px-3 py-1 text-xs"
          style={{ borderColor: 'var(--border)', color: 'var(--text-muted)', fontFamily: 'var(--font-data)' }}
        >
          Multimodal Remote Sensing Assistant
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="text-4xl leading-[1.08] font-semibold sm:text-5xl"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Understand Earth. Ask questions. Discover change.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mx-auto mt-5 max-w-xl text-lg"
          style={{ color: 'var(--text-muted)' }}
        >
          An AI-powered multimodal assistant for intelligent satellite image analysis and remote sensing.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mt-8 flex flex-wrap items-center justify-center gap-3"
        >
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-medium"
            style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
          >
            Start Analyzing
            <ArrowRight size={16} />
          </Link>
          <Link
            to="/dashboard/analyze"
            className="inline-flex items-center gap-2 rounded-lg border px-5 py-3 text-sm font-medium"
            style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
          >
            Explore Demo
          </Link>
        </motion.div>

        <div className="relative mx-auto mt-16 max-w-2xl">
          <div className="relative">
            <HeroGlobe />
            <div className="pointer-events-none absolute inset-x-1/2 bottom-2 hidden w-72 -translate-x-1/2 sm:block">
              <div className="flex items-center justify-between rounded-lg border px-3 py-2 text-[10px] uppercase tracking-wider backdrop-blur-md" style={{ borderColor: 'var(--border)', background: 'color-mix(in srgb, var(--surface) 82%, transparent)' }}>
                <span className="flex items-center gap-1.5" style={{ color: 'var(--color-vegetation)' }}><Radio size={11} /> Signal locked</span>
                <span className="flex items-center gap-1.5" style={{ color: 'var(--color-orbit)' }}><Orbit size={11} /> 2 assets</span>
                <span className="flex items-center gap-1.5" style={{ color: 'var(--color-thermal)' }}><Activity size={11} /> Scanning</span>
              </div>
            </div>
          </div>

          {FLOAT_CARDS.map(({ label, icon: Icon, color, pos }, i) => (
            <motion.div
              key={label}
              className={`absolute ${pos} flex items-center gap-2 rounded-lg border px-3 py-2 text-xs shadow-sm`}
              style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 3.5 + i * 0.4, repeat: Infinity, ease: 'easeInOut' }}
            >
              <Icon size={14} style={{ color }} />
              <span>{label}</span>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="border-y py-8" style={{ borderColor: 'var(--border)' }}>
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-center gap-x-8 gap-y-3 px-6">
          {TECH.map((t) => (
            <span key={t} className="text-xs tracking-wide uppercase" style={{ color: 'var(--text-faint)', fontFamily: 'var(--font-data)' }}>
              {t}
            </span>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-24">
        <h2 className="text-center text-2xl font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
          Everything you need to read the Earth
        </h2>
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: 'var(--surface-2)', color }}>
                <Icon size={17} />
              </div>
              <h3 className="text-sm font-medium">{title}</h3>
              <p className="mt-1.5 text-sm" style={{ color: 'var(--text-muted)' }}>
                {desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y py-24" style={{ borderColor: 'var(--border)', background: 'var(--bg-elevated)' }}>
        <div className="mx-auto max-w-4xl px-6">
          <h2 className="text-center text-2xl font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
            How it works
          </h2>
          <div className="mt-12 flex flex-col items-center gap-3 sm:flex-row sm:justify-between">
            {STEPS.map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <div className="flex items-center gap-3 rounded-lg border px-4 py-2.5 text-sm" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
                  <span
                    className="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-medium"
                    style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
                  >
                    {i + 1}
                  </span>
                  {step}
                </div>
                {i < STEPS.length - 1 && <ArrowRight size={16} className="hidden sm:block" style={{ color: 'var(--text-faint)' }} />}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-2xl px-6 py-28 text-center">
        <h2 className="text-3xl font-semibold" style={{ fontFamily: 'var(--font-display)' }}>
          Start Exploring Satellite Intelligence
        </h2>
        <Link
          to="/dashboard"
          className="mt-8 inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-medium"
          style={{ background: 'var(--accent)', color: 'var(--accent-contrast)' }}
        >
          Start Analyzing
          <ArrowRight size={16} />
        </Link>
      </section>

      <footer className="border-t py-8 text-center text-xs" style={{ borderColor: 'var(--border)', color: 'var(--text-faint)' }}>
        SatQuery AI — a multimodal remote sensing assistant.
      </footer>
    </div>
  );
}
