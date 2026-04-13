/**
 * Impact Observatory | مرصد الأثر — System Strip
 *
 * A minimal persistent strip below the TopNav.
 * Shows global system state when a scenario is active.
 * Hidden when idle — the page is just a document.
 *
 * Design:
 *   - 36px height, same frosted glass as TopNav
 *   - Calm monospace numerics (tabular-nums)
 *   - Five data points: Scenario · Status · Time · Confidence · Impact
 *   - No bright colors, no dashboard feel
 *   - Apple-like quiet information density
 */

'use client';

import { useSystemState } from '@/lib/systemState';
import type { SystemStatus, ImpactState } from '@/lib/systemState';

const statusLabel: Record<SystemStatus, string> = {
  idle: 'Idle',
  running: 'Running',
  escalating: 'Escalating',
  resolved: 'Resolved',
};

const statusColor: Record<SystemStatus, string> = {
  idle: 'text-[var(--io-text-tertiary)]',
  running: 'text-[var(--io-status-olive)]',
  escalating: 'text-[var(--io-status-amber)]',
  resolved: 'text-[var(--io-text-tertiary)]',
};

const impactColor: Record<ImpactState, string> = {
  Contained: 'text-[var(--io-text-tertiary)]',
  Expanding: 'text-[var(--io-status-amber)]',
  Cascading: 'text-[var(--io-status-red)]',
  Stabilising: 'text-[var(--io-status-olive)]',
  Resolved: 'text-[var(--io-text-tertiary)]',
};

function formatTime(hours: number): string {
  if (hours < 1) return 'T+0h';
  if (hours < 100) return `T+${Math.round(hours)}h`;
  const days = Math.floor(hours / 24);
  const remaining = Math.round(hours % 24);
  return `T+${days}d ${remaining}h`;
}

export function SystemStrip() {
  const { activeScenarioId, activeScenarioName, status, snapshot } =
    useSystemState();

  // Invisible when idle — strip occupies zero space
  if (status === 'idle') return null;

  return (
    <div className="sticky top-14 z-40 bg-[var(--io-bg)]/90 backdrop-blur-md border-b border-[var(--io-border-muted)]">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12 h-9 flex items-center justify-between gap-6 overflow-x-auto">

        {/* Scenario name — truncated */}
        <span
          className="text-[0.6875rem] font-medium text-[var(--io-charcoal)] truncate max-w-[180px] sm:max-w-[260px]"
          title={activeScenarioName}
        >
          {activeScenarioName}
        </span>

        {/* Data points */}
        <div className="flex items-center gap-5 sm:gap-7 shrink-0">

          {/* Status */}
          <span className={`text-[0.6875rem] font-semibold tabular-nums ${statusColor[status]}`}>
            {statusLabel[status]}
          </span>

          {/* Time */}
          <span className="text-[0.6875rem] font-medium tabular-nums text-[var(--io-text-tertiary)]">
            {formatTime(snapshot.elapsedHours)}
            <span className="text-[var(--io-text-tertiary)]/50 mx-0.5">/</span>
            {formatTime(snapshot.horizonHours)}
          </span>

          {/* Confidence */}
          <span className="text-[0.6875rem] font-medium tabular-nums text-[var(--io-text-tertiary)] hidden sm:inline">
            {(snapshot.confidence * 100).toFixed(0)}% conf.
          </span>

          {/* Impact state */}
          <span className={`text-[0.6875rem] font-semibold ${impactColor[snapshot.impactState]}`}>
            {snapshot.impactState}
          </span>

        </div>
      </div>
    </div>
  );
}
