/**
 * NarrativeLayer — Multi-Narrative Intelligence
 *
 * Three institutional vantage points on the SAME event.
 * Each lens reinterprets pressure differently:
 *
 *   US Financial  — markets, rates, inflation, capital response
 *   EU Regulatory — policy, compliance, institutional mandates
 *   Asia Industrial — production, logistics, supply chain
 *
 * Full stacked prose. Not one-liners. Not summaries.
 * Read top to bottom like competing analyst briefs.
 * No tabs. No toggles. No cards.
 */

'use client';

import { getIntelligence } from '@/lib/scenarioIntelligence';
import type { RegionalNarrative } from '@/lib/scenarioIntelligence';

const regionMeta: Record<RegionalNarrative['region'], { label: string; lens: string }> = {
  'US Financial':    { label: 'US Financial Perspective',    lens: 'Markets · Rates · Inflation · Capital' },
  'EU Regulatory':   { label: 'EU Regulatory Perspective',   lens: 'Policy · Compliance · Institutional Mandate' },
  'Asia Industrial': { label: 'Asia Industrial Perspective', lens: 'Production · Logistics · Supply Chain' },
};

interface NarrativeLayerProps {
  scenarioId: string;
}

export function NarrativeLayer({ scenarioId }: NarrativeLayerProps) {
  const intel = getIntelligence(scenarioId);
  if (!intel || intel.narratives.length === 0) return null;

  return (
    <section className="io-section">
      <p className="io-label mb-4">Three-Lens Reading</p>
      <p className="io-section-heading">
        Three institutional vantage points on the same event — how pressure is read
        differently across financial, regulatory, and industrial frameworks.
      </p>

      <div className="space-y-12 max-w-3xl io-stagger">
        {intel.narratives.map((n, i) => {
          const meta = regionMeta[n.region];
          return (
            <div key={i}>
              <p className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)] mb-1">
                {meta.label}
              </p>
              <p className="text-[0.6875rem] font-medium uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-4">
                {meta.lens}
              </p>
              <p className="text-[0.9375rem] leading-[1.85] text-[var(--io-text-secondary)]">
                {n.perspective}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
