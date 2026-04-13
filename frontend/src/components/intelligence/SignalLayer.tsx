/**
 * SignalLayer — Two-Layer Signal Intelligence
 *
 * Layer A (Executive): ONE dominant signal. 3 seconds.
 * Layer B (Traceability): 3–5 supporting signals with type, source, impact.
 *
 * When live: intelligence core drives both layers.
 * When static: scenario manifest provides structured inputs.
 *
 * No tabs. No toggles. Stacked: dominant first, then supporting.
 * Sovereign-grade signal intelligence — not a notification feed.
 */

'use client';

import { useSystemState } from '@/lib/systemState';
import { getIntelligence } from '@/lib/scenarioIntelligence';
import type { SignalType } from '@/lib/scenarioIntelligence';

const typeStyle: Record<SignalType, string> = {
  Economic:     'text-[var(--io-text-tertiary)]',
  Geopolitical: 'text-[var(--io-status-red)]',
  Market:       'text-[var(--io-status-amber)]',
  Operational:  'text-[var(--io-text-tertiary)]',
  Regulatory:   'text-[var(--io-status-olive)]',
};

interface SignalLayerProps {
  scenarioId: string;
}

export function SignalLayer({ scenarioId }: SignalLayerProps) {
  const { status, intelligence, activeScenarioId } = useSystemState();

  const isLive = status !== 'idle' && activeScenarioId === scenarioId;

  /* ═══════════════════════════════════════════════════════
     LIVE MODE — intelligence core drives both layers
     ═══════════════════════════════════════════════════════ */
  if (isLive && intelligence.signals.activeSignals.length > 0) {
    const sorted = [...intelligence.signals.activeSignals]
      .sort((a, b) => b.intensity - a.intensity);
    const dominant = sorted[0];
    const supporting = sorted.slice(1, 5); // up to 4 more
    const activeCount = intelligence.signals.activeCount;

    return (
      <section className="io-section">

        {/* ── LAYER A: Executive — single dominant signal ── */}
        <p className="io-label mb-4">
          Dominant Signal
          {activeCount > 1 && (
            <span className="text-[var(--io-text-tertiary)] font-normal ml-2">
              +{activeCount - 1} active
            </span>
          )}
        </p>

        <div className="max-w-3xl mb-12">
          <p className="text-[1.0625rem] font-semibold text-[var(--io-charcoal)] leading-snug mb-2">
            {dominant.signal.signal}
          </p>
          <div className="flex items-baseline gap-3 mb-3">
            <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.06em] ${typeStyle[dominant.signal.type] ?? 'text-[var(--io-text-tertiary)]'}`}>
              {dominant.signal.type}
            </span>
            <span className="text-[0.6875rem] text-[var(--io-text-tertiary)]">
              {dominant.signal.source}
            </span>
            <span className="text-[0.6875rem] tabular-nums text-[var(--io-text-tertiary)]">
              {dominant.state} · {(dominant.intensity * 100).toFixed(0)}%
            </span>
          </div>
          <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)]">
            {dominant.signal.impact}
          </p>
        </div>

        {/* ── LAYER B: Traceability — supporting signals ── */}
        {supporting.length > 0 && (
          <div className="max-w-3xl">
            <p className="io-label mb-4">Supporting Signals</p>
            <div className="space-y-6 io-stagger">
              {supporting.map((s, i) => (
                <div key={i}>
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-1.5">
                    <span className="text-[var(--io-text-tertiary)] tabular-nums text-[0.875rem] mr-0.5">
                      {i + 2}.
                    </span>
                    <span className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)] leading-snug">
                      {s.signal.signal}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-2 pl-6">
                    <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.06em] ${typeStyle[s.signal.type] ?? 'text-[var(--io-text-tertiary)]'}`}>
                      {s.signal.type}
                    </span>
                    <span className="text-[0.75rem] text-[var(--io-text-tertiary)]">
                      {s.signal.source}
                    </span>
                    <span className="text-[0.6875rem] tabular-nums text-[var(--io-text-tertiary)]">
                      {s.state} · {(s.intensity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-[0.875rem] leading-[1.7] text-[var(--io-text-secondary)] pl-6">
                    {s.signal.impact}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    );
  }

  /* ═══════════════════════════════════════════════════════
     STATIC MODE — scenario manifest
     ═══════════════════════════════════════════════════════ */
  const intel = getIntelligence(scenarioId);
  if (!intel || intel.signals.length === 0) return null;

  const dominant = intel.signals[0];
  const supporting = intel.signals.slice(1, 5);

  return (
    <section className="io-section">

      {/* ── LAYER A: Executive — primary signal ── */}
      <p className="io-label mb-4">
        Primary Signal
        {intel.signals.length > 1 && (
          <span className="text-[var(--io-text-tertiary)] font-normal ml-2">
            +{intel.signals.length - 1} supporting
          </span>
        )}
      </p>

      <div className="max-w-3xl mb-12">
        <p className="text-[1.0625rem] font-semibold text-[var(--io-charcoal)] leading-snug mb-2">
          {dominant.signal}
        </p>
        <div className="flex items-baseline gap-3 mb-3">
          <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.06em] ${typeStyle[dominant.type]}`}>
            {dominant.type}
          </span>
          <span className="text-[0.75rem] text-[var(--io-text-tertiary)]">
            {dominant.source}
          </span>
        </div>
        <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)]">
          {dominant.impact}
        </p>
      </div>

      {/* ── LAYER B: Traceability — supporting signals ── */}
      {supporting.length > 0 && (
        <div className="max-w-3xl">
          <p className="io-label mb-4">Supporting Signals</p>
          <div className="space-y-6 io-stagger">
            {supporting.map((s, i) => (
              <div key={i}>
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-1.5">
                  <span className="text-[var(--io-text-tertiary)] tabular-nums text-[0.875rem] mr-0.5">
                    {i + 2}.
                  </span>
                  <span className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)] leading-snug">
                    {s.signal}
                  </span>
                </div>
                <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-2 pl-6">
                  <span className={`text-[0.6875rem] font-semibold uppercase tracking-[0.06em] ${typeStyle[s.type]}`}>
                    {s.type}
                  </span>
                  <span className="text-[0.75rem] text-[var(--io-text-tertiary)]">
                    {s.source}
                  </span>
                </div>
                <p className="text-[0.875rem] leading-[1.7] text-[var(--io-text-secondary)] pl-6">
                  {s.impact}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
