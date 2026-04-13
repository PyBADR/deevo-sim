/**
 * PropagationLayer — Explicit Cause → Effect Chain
 *
 * NOT a result summary. This shows CAUSE.
 * Format:
 *   Event → Country pressure → Sector transmission → Entity exposure → Macro effect
 *
 * When live: reads real contagion events from the propagation engine,
 *   enriched with country/sector/entity context from intelligence core.
 * When static: reads scenario manifest propagation chain.
 *
 * Sovereign-grade. Prose chain. No diagrams. No flowcharts.
 */

'use client';

import { useSystemState } from '@/lib/systemState';
import { getIntelligence } from '@/lib/scenarioIntelligence';

interface PropagationLayerProps {
  scenarioId: string;
}

function stressTag(v: number): string {
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

const countryNames: Record<string, string> = {
  SA: 'Saudi Arabia',
  AE: 'UAE',
  KW: 'Kuwait',
  QA: 'Qatar',
  BH: 'Bahrain',
  OM: 'Oman',
};

export function PropagationLayer({ scenarioId }: PropagationLayerProps) {
  const { status, intelligence, activeScenarioId } = useSystemState();
  const isLive = status !== 'idle' && activeScenarioId === scenarioId;

  /* ═══════════════════════════════════════════════════════
     LIVE MODE — real propagation from intelligence core
     Structured as: Country Pressure → Sector Transmission →
     Entity Exposure → Contagion Events
     ═══════════════════════════════════════════════════════ */
  if (isLive) {
    const countries = [...intelligence.countries]
      .sort((a, b) => b.compositeStress - a.compositeStress);
    const sectors = [...intelligence.sectors]
      .sort((a, b) => b.stress - a.stress);
    const events = intelligence.contagionLog.slice(-3);

    return (
      <section className="io-section">
        <p className="io-label mb-6">Propagation Chain</p>

        <div className="max-w-3xl space-y-10">

          {/* ── Step 1: Country Pressure ── */}
          <div>
            <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
              Country Pressure
            </p>
            <div className="space-y-2 io-stagger">
              {countries.slice(0, 3).map((c) => (
                <p key={c.countryCode} className="text-[0.9375rem] leading-[1.7] text-[var(--io-text-secondary)]">
                  <span className="font-semibold text-[var(--io-charcoal)]">{c.name}</span>
                  <span className="mx-2 text-[var(--io-border-accent)]">—</span>
                  <span className={`font-semibold ${stressColor(c.compositeStress)}`}>
                    {stressTag(c.compositeStress)}
                  </span>
                  <span className="text-[var(--io-text-tertiary)]"> stress. </span>
                  {c.gdpPressure.level !== 'low' && (
                    <span>GDP {c.gdpPressure.level}. </span>
                  )}
                  {c.liquidityStress.level !== 'low' && (
                    <span>Liquidity {c.liquidityStress.level}. </span>
                  )}
                  {c.tradeDisruption.level !== 'low' && (
                    <span>Trade {c.tradeDisruption.level}. </span>
                  )}
                </p>
              ))}
            </div>
          </div>

          {/* ── Step 2: Sector Transmission ── */}
          <div>
            <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
              ↓ Sector Transmission
            </p>
            <div className="space-y-2 io-stagger">
              {sectors.slice(0, 3).map((s) => (
                <p key={s.sector} className="text-[0.9375rem] leading-[1.7] text-[var(--io-text-secondary)]">
                  <span className="font-semibold text-[var(--io-charcoal)]">{s.label}</span>
                  <span className="mx-2 text-[var(--io-border-accent)]">—</span>
                  <span className={`font-semibold ${stressColor(s.stress)}`}>
                    {stressTag(s.stress)}
                  </span>
                  <span className="text-[var(--io-text-tertiary)]"> via </span>
                  <span>{s.transmissionSource}</span>
                </p>
              ))}
            </div>
          </div>

          {/* ── Step 3: Entity Exposure ── */}
          {intelligence.entities.length > 0 && (
            <div>
              <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
                ↓ Entity Exposure
              </p>
              <div className="space-y-2 io-stagger">
                {[...intelligence.entities]
                  .sort((a, b) => b.exposure - a.exposure)
                  .slice(0, 3)
                  .map((e) => (
                    <p key={e.entityId} className="text-[0.9375rem] leading-[1.7] text-[var(--io-text-secondary)]">
                      <span className="font-semibold text-[var(--io-charcoal)]">{e.name}</span>
                      <span className="text-[var(--io-text-tertiary)]"> ({countryNames[e.country] ?? e.country} · {e.sector})</span>
                      <span className="mx-2 text-[var(--io-border-accent)]">—</span>
                      <span>{e.driver}</span>
                    </p>
                  ))}
              </div>
            </div>
          )}

          {/* ── Step 4: Contagion Events (cross-cutting cascades) ── */}
          {events.length > 0 && (
            <div>
              <p className="text-[0.75rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-3">
                ↓ Contagion Events
                <span className="font-normal ml-2">
                  {intelligence.contagionLog.length} total
                </span>
              </p>
              <ol className="space-y-3 io-stagger">
                {events.map((event, i) => (
                  <li key={i} className="io-numbered-item">
                    <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
                    <span className="font-semibold text-[var(--io-charcoal)]">
                      {event.source} → {event.target}
                    </span>
                    <span className="mx-2 text-[var(--io-border-accent)]">—</span>
                    <span className="text-[var(--io-text-secondary)]">
                      {event.description}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          )}

        </div>
      </section>
    );
  }

  /* ═══════════════════════════════════════════════════════
     STATIC MODE — scenario manifest propagation chain
     ═══════════════════════════════════════════════════════ */
  const intel = getIntelligence(scenarioId);
  if (!intel || intel.propagation.length === 0) return null;

  return (
    <section className="io-section">
      <p className="io-label mb-4">Propagation Chain</p>
      <p className="io-section-heading">
        Ordered causal sequence from initial trigger to systemic outcome.
        Each node represents a measured point where pressure transforms or amplifies.
      </p>

      <ol className="space-y-5 max-w-3xl io-stagger">
        {intel.propagation.map((step, i) => (
          <li key={i} className="io-numbered-item">
            <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
            <span className="inline-block w-5 text-center mr-2 text-[var(--io-charcoal)] font-medium">
              {step.direction}
            </span>
            <span className="font-semibold text-[var(--io-charcoal)]">{step.node}</span>
            <span className="mx-2 text-[var(--io-border-accent)]">—</span>
            <span>{step.effect}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
