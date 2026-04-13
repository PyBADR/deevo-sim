/**
 * DecisionIntelligence — WHY / HOW / WHAT with Posture Integration
 *
 * The decision block answers:
 *   WHY — signal-driven rationale
 *   HOW — institutional mechanism
 *   WHAT — specific action
 *
 * When live: intelligence core drives posture + advisory + WHY/HOW/WHAT
 *   from the decision engine. Full traceability to signals and propagation.
 * When static: scenario manifest's reasoning (WHY/HOW/WHAT + signal basis).
 *
 * Executive layer (WHAT) always comes first.
 * Traceability (WHY → HOW) follows.
 * Posture badge on live. Signal basis anchors credibility.
 */

'use client';

import { useSystemState } from '@/lib/systemState';
import { getIntelligence } from '@/lib/scenarioIntelligence';
import type { DecisionPosture } from '@/lib/intelligence/decisionEngine';

const postureStyle: Record<DecisionPosture, { label: string; color: string }> = {
  monitoring: { label: 'MONITORING',  color: 'text-[var(--io-text-tertiary)]' },
  advisory:  { label: 'ADVISORY',   color: 'text-[var(--io-text-secondary)]' },
  active:    { label: 'ACTIVE',     color: 'text-[var(--io-status-olive)]' },
  immediate: { label: 'IMMEDIATE',  color: 'text-[var(--io-status-amber)]' },
  crisis:    { label: 'CRISIS',     color: 'text-[var(--io-status-red)]' },
};

interface DecisionIntelligenceProps {
  scenarioId: string;
}

export function DecisionIntelligence({ scenarioId }: DecisionIntelligenceProps) {
  const { status, intelligence, activeScenarioId } = useSystemState();
  const isLive = status !== 'idle' && activeScenarioId === scenarioId;

  /* ═══════════════════════════════════════════════════════
     LIVE MODE — intelligence core drives decision output
     ═══════════════════════════════════════════════════════ */
  if (isLive) {
    const d = intelligence.decision;
    const ps = postureStyle[d.posture];

    return (
      <section className="io-section">
        {/* Posture badge */}
        <div className="flex items-baseline gap-3 mb-4">
          <p className="io-label">Decision Posture</p>
          <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.06em] ${ps.color}`}>
            {ps.label}
          </span>
        </div>

        <div className="max-w-3xl space-y-10">

          {/* WHAT — the dominant directive (executive layer, first) */}
          <div>
            <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
              What Must Happen
            </p>
            <p className="text-[1.0625rem] font-semibold text-[var(--io-charcoal)] leading-snug mb-3">
              {d.systemSeverity}
            </p>
            {d.escalationActions.length > 0 && (
              <div className="space-y-2 io-stagger">
                {d.escalationActions.map((action, i) => (
                  <p key={i} className="io-numbered-item">
                    <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
                    <span className="text-[var(--io-text-secondary)]">{action}</span>
                  </p>
                ))}
              </div>
            )}
          </div>

          {/* WHY — signal-driven rationale */}
          <div>
            <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
              Why This Decision Is Required
            </p>
            <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)]">
              {d.advisory}
            </p>
          </div>

          {/* HOW — institutional mechanism */}
          <div>
            <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
              How It Should Execute
            </p>
            {/* Priority countries + sectors form the institutional mechanism */}
            {d.priorityCountries.length > 0 && (
              <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)] mb-3">
                Priority response required in {d.priorityCountries.join(', ')}.
                {d.criticalSectors.length > 0 && (
                  <> {d.criticalSectors.join(' and ')} sectors require coordinated institutional action.</>
                )}
              </p>
            )}
            {d.overdueEntities.length > 0 && (
              <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)]">
                Overdue entities requiring escalation: {d.overdueEntities.join(', ')}.
              </p>
            )}
            {d.priorityCountries.length === 0 && d.overdueEntities.length === 0 && (
              <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)]">
                Through existing institutional authority chains. Decision owners execute within established frameworks.
              </p>
            )}
          </div>
        </div>
      </section>
    );
  }

  /* ═══════════════════════════════════════════════════════
     STATIC MODE — scenario manifest WHY / HOW / WHAT
     ═══════════════════════════════════════════════════════ */
  const intel = getIntelligence(scenarioId);
  if (!intel) return null;

  const r = intel.reasoning;

  return (
    <section className="io-section">
      <p className="io-label mb-4">Decision Intelligence</p>
      <p className="io-section-heading">
        Structured reasoning connecting observed signals to required action.
        Each decision is traceable from intelligence input through causal chain
        to institutional response.
      </p>

      <div className="max-w-3xl space-y-10 io-stagger">
        {/* WHAT — action required */}
        <div>
          <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
            What Must Happen
          </p>
          <p className="text-[1.0625rem] font-semibold text-[var(--io-charcoal)] leading-snug">
            {r.what}
          </p>
        </div>

        {/* WHY — rationale */}
        <div>
          <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
            Why This Decision Is Required
          </p>
          <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)]">
            {r.why}
          </p>
        </div>

        {/* HOW — institutional mechanism */}
        <div>
          <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
            How It Should Execute
          </p>
          <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)]">
            {r.how}
          </p>
        </div>

        {/* Signal basis — traceability anchor */}
        <div>
          <p className="io-label mb-3">Signal Basis</p>
          <ol className="space-y-2">
            {r.signalBasis.map((basis, i) => (
              <li key={i} className="io-numbered-item">
                <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
                {basis}
              </li>
            ))}
          </ol>
        </div>

        {/* Propagation link */}
        <div>
          <p className="io-label mb-3">Propagation Link</p>
          <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)]">
            {r.propagationLink}
          </p>
        </div>
      </div>
    </section>
  );
}
