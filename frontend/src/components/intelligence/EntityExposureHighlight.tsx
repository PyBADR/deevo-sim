/**
 * EntityExposureHighlight — 3 Most Exposed Entities with Dependency Reasoning
 *
 * CEO sees the three institutions most at risk.
 * Each entry explains WHY: dependency chain or sector pressure.
 *
 * Shows:
 *   - Entity name (with institutional context)
 *   - Country · Sector · Response status
 *   - Exposure driver — why this entity is stressed
 *   - Dependencies — what it depends on (from entity registry)
 *
 * Visible when live. Falls back to scenario manifest exposure when static.
 */

'use client';

import { useSystemState } from '@/lib/systemState';
import { getScenario } from '@/lib/scenarios';
import type { ExposureLine } from '@/lib/scenarios';
import { ENTITY_REGISTRY } from '@/lib/intelligence/entityState';

const countryNames: Record<string, string> = {
  SA: 'Saudi Arabia',
  AE: 'UAE',
  KW: 'Kuwait',
  QA: 'Qatar',
  BH: 'Bahrain',
  OM: 'Oman',
};

function exposureColor(level: string): string {
  if (level === 'critical') return 'text-[var(--io-status-red)]';
  if (level === 'high') return 'text-[var(--io-status-amber)]';
  if (level === 'elevated') return 'text-[var(--io-text-secondary)]';
  return 'text-[var(--io-text-tertiary)]';
}

function statusColor(s: string): string {
  if (s === 'overdue') return 'text-[var(--io-status-red)]';
  if (s === 'awaiting') return 'text-[var(--io-status-amber)]';
  if (s === 'active') return 'text-[var(--io-status-olive)]';
  return 'text-[var(--io-text-tertiary)]';
}

interface EntityExposureHighlightProps {
  scenarioId: string;
}

export function EntityExposureHighlight({ scenarioId }: EntityExposureHighlightProps) {
  const { status, intelligence, activeScenarioId } = useSystemState();
  const isLive = status !== 'idle' && activeScenarioId === scenarioId;

  /* ═══════════════════════════════════════════════════════
     LIVE MODE — from intelligence core with dependency reasoning
     ═══════════════════════════════════════════════════════ */
  if (isLive && intelligence.entities.length > 0) {
    const topEntities = [...intelligence.entities]
      .sort((a, b) => b.exposure - a.exposure)
      .slice(0, 3);

    const criticalCount = intelligence.summary.criticalEntityCount;

    return (
      <section className="io-section">
        <p className="io-label mb-4">
          Entity Exposure
          {criticalCount > 0 && (
            <span className="text-[var(--io-status-red)] ml-2">
              {criticalCount} critical
            </span>
          )}
        </p>

        <div className="space-y-8 max-w-3xl io-stagger">
          {topEntities.map((e, i) => {
            // Look up dependencies from entity registry
            const def = ENTITY_REGISTRY.find(d => d.id === e.entityId);
            const deps = def?.dependencies ?? [];

            return (
              <div key={e.entityId}>
                {/* Entity identity */}
                <div className="flex items-baseline gap-3 mb-1.5">
                  <span className="text-[var(--io-text-tertiary)] tabular-nums text-[0.875rem] mr-0.5">
                    {i + 1}.
                  </span>
                  <span className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)]">
                    {e.name}
                  </span>
                  <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.04em] ${exposureColor(e.level)}`}>
                    {e.level}
                  </span>
                </div>

                {/* Context line */}
                <p className="text-[0.75rem] text-[var(--io-text-tertiary)] mb-2 pl-6">
                  {countryNames[e.country] ?? e.country} · {e.sector} · Response:{' '}
                  <span className={statusColor(e.responseStatus)}>{e.responseStatus}</span>
                </p>

                {/* Driver — why this entity is stressed */}
                <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] pl-6 mb-2">
                  {e.driver}
                </p>

                {/* Dependencies — what this entity depends on */}
                {deps.length > 0 && (
                  <p className="text-[0.8125rem] text-[var(--io-text-tertiary)] pl-6">
                    <span className="font-medium text-[var(--io-charcoal)]">Dependencies:</span>{' '}
                    {deps.join(' · ')}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </section>
    );
  }

  /* ═══════════════════════════════════════════════════════
     STATIC MODE — from scenario manifest exposure lines
     ═══════════════════════════════════════════════════════ */
  const scenario = getScenario(scenarioId);
  if (!scenario || scenario.impact.length === 0) return null;

  return (
    <section className="io-section">
      <p className="io-label mb-4">Institutional Exposure</p>
      <p className="io-section-heading">
        {scenario.impactFraming}
      </p>

      <div className="space-y-8 io-stagger">
        {scenario.impact.slice(0, 3).map((line: ExposureLine, i: number) => (
          <div key={i} className="max-w-3xl">
            <div className="flex items-baseline gap-3 mb-2">
              <span className="text-[var(--io-text-tertiary)] tabular-nums text-[0.875rem] mr-0.5">
                {i + 1}.
              </span>
              <span className="text-[1rem] font-semibold text-[var(--io-charcoal)]">
                {line.entity}
              </span>
              <span className={`text-[0.75rem] font-semibold ${exposureColor(line.severity.toLowerCase())}`}>
                {line.severity}
              </span>
            </div>
            <p className="text-[0.75rem] font-medium text-[var(--io-text-tertiary)] mb-2 pl-6">
              {line.sector}
            </p>
            <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] pl-6">
              {line.exposure}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
