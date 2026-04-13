/**
 * MonitoringBlock — Institutional Accountability Chain
 *
 * Every decision has:
 *   - Execution Owner   — who executes
 *   - Monitoring Owner  — who watches
 *   - Escalation Authority — who intervenes if deadline passes
 *   - Review Cycle      — how often status is re-evaluated
 *
 * When live: reads monitoring assignments from intelligence core.
 *   Shows phase (active monitoring → escalation → review → closed),
 *   status of each assignment, and hours until next review.
 * When static: shows decision actions with sector ownership.
 *
 * Sovereign-grade accountability. Not a Jira board.
 */

'use client';

import { useSystemState } from '@/lib/systemState';
import type { MonitoringAssignment } from '@/lib/intelligence/monitoringEngine';

interface MonitoringBlockProps {
  scenarioId: string;
}

const phaseLabel: Record<string, string> = {
  pre_activation:   'Pre-Activation',
  active_monitoring: 'Active Monitoring',
  escalation:       'Escalation',
  review:           'Review',
  closed:           'Closed',
};

const phaseColor: Record<string, string> = {
  pre_activation:   'text-[var(--io-text-tertiary)]',
  active_monitoring: 'text-[var(--io-status-olive)]',
  escalation:       'text-[var(--io-status-red)]',
  review:           'text-[var(--io-status-amber)]',
  closed:           'text-[var(--io-text-tertiary)]',
};

const statusColor: Record<MonitoringAssignment['status'], string> = {
  pending:    'text-[var(--io-text-tertiary)]',
  active:     'text-[var(--io-text-secondary)]',
  on_track:   'text-[var(--io-status-olive)]',
  at_risk:    'text-[var(--io-status-amber)]',
  escalated:  'text-[var(--io-status-red)]',
  completed:  'text-[var(--io-text-tertiary)]',
};

const statusLabel: Record<MonitoringAssignment['status'], string> = {
  pending:    'Pending',
  active:     'Active',
  on_track:   'On Track',
  at_risk:    'At Risk',
  escalated:  'Escalated',
  completed:  'Completed',
};

export function MonitoringBlock({ scenarioId }: MonitoringBlockProps) {
  const { status, intelligence, activeScenarioId } = useSystemState();
  const isLive = status !== 'idle' && activeScenarioId === scenarioId;

  // Only render when scenario is running
  if (!isLive) return null;

  const mon = intelligence.monitoring;
  if (mon.assignments.length === 0) return null;

  return (
    <section className="io-section">
      {/* Phase + next review */}
      <div className="flex items-baseline gap-3 mb-4">
        <p className="io-label">Monitoring</p>
        <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.06em] ${phaseColor[mon.phase] ?? 'text-[var(--io-text-tertiary)]'}`}>
          {phaseLabel[mon.phase] ?? mon.phase}
        </span>
        {mon.hoursUntilReview > 0 && mon.phase !== 'closed' && (
          <span className="text-[0.6875rem] tabular-nums text-[var(--io-text-tertiary)]">
            Next review in {Math.round(mon.hoursUntilReview)}h
          </span>
        )}
      </div>

      {/* Status summary */}
      <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl mb-8">
        {mon.statusSummary}
      </p>

      {/* Assignment chain — who executes, who monitors, who escalates */}
      <div className="space-y-8 max-w-3xl io-stagger">
        {mon.assignments.map((a, i) => (
          <div key={i}>
            {/* Action + status */}
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-2">
              <span className="text-[var(--io-text-tertiary)] tabular-nums text-[0.875rem] mr-0.5">
                {i + 1}.
              </span>
              <span className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)] leading-snug">
                {a.action}
              </span>
              <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.04em] ${statusColor[a.status]}`}>
                {statusLabel[a.status]}
              </span>
            </div>

            {/* Ownership chain */}
            <div className="pl-6 space-y-1.5">
              <p className="text-[0.8125rem] text-[var(--io-text-secondary)]">
                <span className="font-medium text-[var(--io-charcoal)]">Executes:</span>{' '}
                {a.ownership.executionOwner}
              </p>
              <p className="text-[0.8125rem] text-[var(--io-text-secondary)]">
                <span className="font-medium text-[var(--io-charcoal)]">Monitors:</span>{' '}
                {a.ownership.monitoringOwner}
              </p>
              <p className="text-[0.8125rem] text-[var(--io-text-secondary)]">
                <span className="font-medium text-[var(--io-charcoal)]">Escalation:</span>{' '}
                {a.ownership.escalationAuthority}
              </p>
              <p className="text-[0.75rem] text-[var(--io-text-tertiary)]">
                {a.sector} · Deadline: {a.deadline} ·{' '}
                {a.hoursRemaining > 0
                  ? `${Math.round(a.hoursRemaining)}h remaining`
                  : 'Past deadline'
                }
                {' '}· Review every {a.ownership.reviewCycleHours}h
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
