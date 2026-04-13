/**
 * Impact Observatory | مرصد الأثر — CEO Macro Intelligence Strip
 *
 * Persistent top-level strip exposing the intelligence core to executives.
 * Replaces the old SystemStrip with macro-aware data.
 *
 * Shows:
 *   - 3 most stressed GCC countries (sorted by compositeStress)
 *   - 2 most pressured sectors (sorted by stress)
 *   - System posture (monitoring → crisis)
 *
 * HARD RULE: CEO reads this in 3 seconds. No clutter. No decoration.
 * Hidden when idle — the page is just a document.
 */

'use client';

import { useSystemState } from '@/lib/systemState';
import type { SystemStatus } from '@/lib/systemState';
import type { DecisionPosture } from '@/lib/intelligence/decisionEngine';

/* ── Posture display ── */

const postureLabel: Record<DecisionPosture, string> = {
  monitoring: 'Monitoring',
  advisory:  'Advisory',
  active:    'Active',
  immediate: 'Immediate',
  crisis:    'Crisis',
};

const postureColor: Record<DecisionPosture, string> = {
  monitoring: 'text-[var(--io-text-tertiary)]',
  advisory:  'text-[var(--io-text-secondary)]',
  active:    'text-[var(--io-status-olive)]',
  immediate: 'text-[var(--io-status-amber)]',
  crisis:    'text-[var(--io-status-red)]',
};

/* ── Status dot ── */

const statusDot: Record<SystemStatus, string> = {
  idle:       '',
  running:    'bg-[var(--io-status-olive)]',
  escalating: 'bg-[var(--io-status-amber)]',
  resolved:   'bg-[var(--io-text-tertiary)]',
};

/* ── Country code → short name ── */

const countryShort: Record<string, string> = {
  SA: 'Saudi',
  AE: 'UAE',
  KW: 'Kuwait',
  QA: 'Qatar',
  BH: 'Bahrain',
  OM: 'Oman',
};

/* ── Stress intensity → label ── */

function stressLabel(v: number): string {
  if (v >= 0.75) return 'severe';
  if (v >= 0.55) return 'high';
  if (v >= 0.35) return 'elevated';
  return 'moderate';
}

function stressColor(v: number): string {
  if (v >= 0.75) return 'text-[var(--io-status-red)]';
  if (v >= 0.55) return 'text-[var(--io-status-amber)]';
  if (v >= 0.35) return 'text-[var(--io-text-secondary)]';
  return 'text-[var(--io-text-tertiary)]';
}

function formatTime(hours: number): string {
  if (hours < 1) return 'T+0h';
  if (hours < 100) return `T+${Math.round(hours)}h`;
  const days = Math.floor(hours / 24);
  const remaining = Math.round(hours % 24);
  return `T+${days}d ${remaining}h`;
}

export function MacroStrip() {
  const { status, snapshot, intelligence } = useSystemState();

  // Invisible when idle
  if (status === 'idle') return null;

  // Top 3 countries by compositeStress
  const topCountries = [...intelligence.countries]
    .sort((a, b) => b.compositeStress - a.compositeStress)
    .slice(0, 3);

  // Top 2 sectors by stress
  const topSectors = [...intelligence.sectors]
    .sort((a, b) => b.stress - a.stress)
    .slice(0, 2);

  const posture = intelligence.decision.posture;

  return (
    <div className="sticky top-14 z-40 bg-[var(--io-bg)]/90 backdrop-blur-md border-b border-[var(--io-border-muted)]">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12 h-10 flex items-center justify-between gap-4 overflow-x-auto">

        {/* Left: Posture + time */}
        <div className="flex items-center gap-3 shrink-0">
          {/* Status dot */}
          <span className={`w-1.5 h-1.5 rounded-full ${statusDot[status]}`} />

          {/* Posture */}
          <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.05em] ${postureColor[posture]}`}>
            {postureLabel[posture]}
          </span>

          {/* Time */}
          <span className="text-[0.6875rem] tabular-nums text-[var(--io-text-tertiary)]">
            {formatTime(snapshot.elapsedHours)}
            <span className="opacity-40 mx-0.5">/</span>
            {formatTime(snapshot.horizonHours)}
          </span>
        </div>

        {/* Center: Top 3 countries */}
        <div className="flex items-center gap-4 sm:gap-5">
          {topCountries.map((c) => (
            <span key={c.countryCode} className="flex items-baseline gap-1.5">
              <span className="text-[0.6875rem] font-medium text-[var(--io-charcoal)]">
                {countryShort[c.countryCode] ?? c.countryCode}
              </span>
              <span className={`text-[0.625rem] font-semibold tabular-nums ${stressColor(c.compositeStress)}`}>
                {stressLabel(c.compositeStress)}
              </span>
            </span>
          ))}
        </div>

        {/* Right: Top 2 sectors */}
        <div className="flex items-center gap-4 shrink-0">
          {topSectors.map((s) => (
            <span key={s.sector} className="flex items-baseline gap-1.5">
              <span className="text-[0.6875rem] font-medium text-[var(--io-text-secondary)]">
                {s.label}
              </span>
              <span className={`text-[0.625rem] font-semibold tabular-nums ${stressColor(s.stress)}`}>
                {stressLabel(s.stress)}
              </span>
            </span>
          ))}
        </div>

      </div>
    </div>
  );
}
