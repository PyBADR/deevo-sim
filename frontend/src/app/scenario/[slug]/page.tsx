/**
 * Impact Observatory | مرصد الأثر — Scenario Intelligence Briefing
 *
 * Unified sovereign-grade CEO Command Surface.
 * Three layers integrated into one page:
 *   Intelligence Core + Multi-Narrative + Executive Clarity
 *
 * Section Hierarchy:
 *   1. Macro Context       — headline, severity, context, significance
 *   2. System Activation   — run / stop / reset with live posture
 *   3. Three-Lens Reading  — US Financial, EU Regulatory, Asia Industrial
 *   4. Signal Intelligence — Layer A (dominant) + Layer B (supporting)
 *   5. Propagation Chain   — country → sector → entity → contagion
 *   6. Entity Exposure     — top 3 with dependency reasoning
 *   7. Decision Block      — WHY / HOW / WHAT with posture
 *   8. Monitoring          — execution / monitoring / escalation / review
 *   9. Outcome             — what confirms the path
 *
 * HARD RULE: CEO understands the system in 10 seconds.
 * The page answers:
 *   What is happening?
 *   Why does it matter economically?
 *   How is it spreading?
 *   Who is exposed?
 *   What is the decision?
 *   What confirms success?
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PageShell, Container } from '@/components/layout';
import { getScenario, getAllScenarios } from '@/lib/scenarios';
import { ScenarioActivation } from '@/components/system/ScenarioActivation';
import { NarrativeLayer } from '@/components/intelligence/NarrativeLayer';
import { SignalLayer } from '@/components/intelligence/SignalLayer';
import { PropagationLayer } from '@/components/intelligence/PropagationLayer';
import { DecisionIntelligence } from '@/components/intelligence/DecisionIntelligence';
import { EntityExposureHighlight } from '@/components/intelligence/EntityExposureHighlight';
import { MonitoringBlock } from '@/components/intelligence/MonitoringBlock';

export async function generateStaticParams() {
  return getAllScenarios().map((s) => ({ slug: s.id }));
}

const severityColor: Record<string, string> = {
  Severe:   'text-[var(--io-status-red)]',
  Critical: 'text-[var(--io-status-red)]',
  High:     'text-[var(--io-status-red)]',
  Elevated: 'text-[var(--io-status-amber)]',
  Guarded:  'text-[var(--io-text-tertiary)]',
};

function sColor(level: string): string {
  return severityColor[level] ?? 'text-[var(--io-text-tertiary)]';
}

export default async function ScenarioPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const b = getScenario(slug);
  if (!b) notFound();

  return (
    <PageShell>
      <Container>

        {/* Back */}
        <div className="pt-8 pb-3">
          <Link
            href="/"
            className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-200"
          >
            ← All scenarios
          </Link>
        </div>

        {/* ═══════════════════════════════════════════════════════
           1. MACRO CONTEXT — what is happening?
           CEO reads headline + severity + context in 5 seconds.
           ═══════════════════════════════════════════════════════ */}
        <header className="pt-4 pb-16 sm:pb-20">
          <div className="io-meta mb-6">
            <span className={`io-status ${sColor(b.severity)}`}>
              {b.severity}
            </span>
            <span>{b.domain}</span>
            <span className="tabular-nums">{b.horizonHours}h horizon</span>
          </div>

          <h1 className="io-briefing-title mb-8 max-w-3xl">
            {b.title}
          </h1>

          <p className="io-prose-lg mb-6">
            {b.context}
          </p>

          <p className="io-prose text-[var(--io-text-tertiary)]">
            {b.significance}
          </p>
        </header>

        {/* ═══════════════════════════════════════════════════════
           2. SYSTEM ACTIVATION — run scenario with live posture
           ═══════════════════════════════════════════════════════ */}
        <ScenarioActivation
          scenarioId={b.id}
          scenarioName={b.title}
          horizonHours={b.horizonHours}
          severity={b.severity}
        />

        <hr className="io-divider-accent" />

        {/* ═══════════════════════════════════════════════════════
           3. THREE-LENS READING — why it matters differently
           across financial, regulatory, industrial frameworks.
           Full stacked prose. Not one-liners.
           ═══════════════════════════════════════════════════════ */}
        <NarrativeLayer scenarioId={b.id} />

        {/* ═══════════════════════════════════════════════════════
           4. SIGNAL INTELLIGENCE
           Layer A: ONE dominant signal (3 seconds)
           Layer B: 3–5 supporting signals (traceability)
           ═══════════════════════════════════════════════════════ */}
        <SignalLayer scenarioId={b.id} />

        {/* ═══════════════════════════════════════════════════════
           5. PROPAGATION CHAIN — how is it spreading?
           Event → Country pressure → Sector transmission →
           Entity exposure → Contagion events
           ═══════════════════════════════════════════════════════ */}
        <PropagationLayer scenarioId={b.id} />

        {/* ═══════════════════════════════════════════════════════
           6. ENTITY EXPOSURE — who is exposed?
           Top 3 entities with dependency reasoning.
           Live: from intelligence core.
           Static: from scenario manifest.
           ═══════════════════════════════════════════════════════ */}
        <EntityExposureHighlight scenarioId={b.id} />

        {/* ═══════════════════════════════════════════════════════
           7. DECISION BLOCK — what is the decision?
           WHY / HOW / WHAT with posture integration.
           ═══════════════════════════════════════════════════════ */}
        <DecisionIntelligence scenarioId={b.id} />

        {/* ═══════════════════════════════════════════════════════
           8. MONITORING — who executes, who watches, who escalates
           Institutional accountability chain.
           Live only — invisible when static.
           ═══════════════════════════════════════════════════════ */}
        <MonitoringBlock scenarioId={b.id} />

        {/* ═══════════════════════════════════════════════════════
           9. OUTCOME — what confirms success?
           ═══════════════════════════════════════════════════════ */}
        <section className="py-16 sm:py-20">
          <p className="io-label mb-4">Expected Outcome</p>
          <p className="io-prose-lg mt-6">
            {b.outcome}
          </p>

          <div className="mt-12">
            <p className="io-label mb-4">What Confirms the Path</p>
            <ol className="space-y-3 max-w-3xl io-stagger">
              {b.monitoringCriteria.map((criterion, i) => (
                <li key={i} className="io-numbered-item">
                  <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
                  {criterion}
                </li>
              ))}
            </ol>
          </div>

          <div className="mt-12">
            <Link
              href={`/decision/${b.id}`}
              className="text-[0.8125rem] font-medium text-[var(--io-text-tertiary)] hover:text-[var(--io-charcoal)] transition-colors duration-200"
            >
              View full decision brief →
            </Link>
          </div>
        </section>

        {/* Footer */}
        <div className="io-footer">
          <span className="io-footer-text">
            Impact Observatory · مرصد الأثر
          </span>
          <span className="io-footer-text">
            {b.id}
          </span>
        </div>

      </Container>
    </PageShell>
  );
}
