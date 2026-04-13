/**
 * Impact Observatory | مرصد الأثر — Decision Reaction Layer
 *
 * Client component that overlays live urgency state onto the
 * decision briefing page when a scenario is active.
 *
 * When idle: invisible. Static page reads as normal document.
 * When active: shows evolving urgency language and adjusted posture.
 * When resolved: shows final state assessment.
 *
 * Does NOT replace directive content. Adds a reactive context layer.
 */

'use client';

import { useSystemState } from '@/lib/systemState';

interface Props {
  scenarioId: string;
  classification: string;
}

function urgencyLanguage(
  multiplier: number,
  stressLevel: string,
  impactState: string,
  elapsedHours: number,
): { posture: string; advisory: string } {
  if (multiplier > 2.0) {
    return {
      posture: 'Immediate',
      advisory: `Stress at ${stressLevel}. Impact ${impactState.toLowerCase()}. All directives should be treated as immediate-execution priority. Delay compounds exposure at current rate.`,
    };
  }
  if (multiplier > 1.5) {
    return {
      posture: 'Elevated',
      advisory: `System stress rising. ${impactState} impact detected at T+${Math.round(elapsedHours)}h. Primary directive deadline should be treated as binding.`,
    };
  }
  if (multiplier > 1.2) {
    return {
      posture: 'Active',
      advisory: `Scenario in progress. Stress level: ${stressLevel}. Directives are active and deadlines are operative.`,
    };
  }
  return {
    posture: 'Monitoring',
    advisory: `System returning to baseline. Directives remain in force. Continue monitoring criteria.`,
  };
}

export function DecisionReaction({ scenarioId, classification }: Props) {
  const { activeScenarioId, status, snapshot } = useSystemState();

  // Only show when this scenario is active
  if (status === 'idle') return null;
  if (activeScenarioId !== scenarioId) return null;

  const { posture, advisory } = urgencyLanguage(
    snapshot.urgencyMultiplier,
    snapshot.stressLevel,
    snapshot.impactState,
    snapshot.elapsedHours,
  );

  const postureColor =
    posture === 'Immediate'
      ? 'text-[var(--io-status-red)]'
      : posture === 'Elevated'
        ? 'text-[var(--io-status-amber)]'
        : posture === 'Active'
          ? 'text-[var(--io-status-olive)]'
          : 'text-[var(--io-text-tertiary)]';

  return (
    <section className="py-8 border-b border-[var(--io-border-muted)]">
      <div className="max-w-3xl">
        <div className="flex items-baseline gap-4 mb-3">
          <p className="io-label">Live Posture</p>
          <span className={`text-[0.8125rem] font-semibold ${postureColor}`}>
            {posture}
          </span>
          {status === 'resolved' && (
            <span className="text-[0.75rem] text-[var(--io-text-tertiary)]">
              — Simulation complete
            </span>
          )}
        </div>

        <p className="text-[0.875rem] leading-[1.7] text-[var(--io-text-secondary)]">
          {advisory}
        </p>

        {/* Sector pressure — only during escalation */}
        {snapshot.urgencyMultiplier > 1.5 && snapshot.activeSectors.length > 0 && (
          <p className="text-[0.8125rem] text-[var(--io-text-tertiary)] mt-3">
            Sectors under pressure: {snapshot.activeSectors.join(' · ')}
          </p>
        )}
      </div>
    </section>
  );
}
