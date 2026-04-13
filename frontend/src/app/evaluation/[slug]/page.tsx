/**
 * Impact Observatory | مرصد الأثر — Evaluation Briefing
 *
 * Institutional accountability document.
 * Read top to bottom like a post-decision review memo.
 *
 *   1. Evaluation Identity     — verdict, scenario, summary
 *   2. Outcome Assessment      — expected vs actual in prose
 *   3. Correctness             — quiet verdict with rationale
 *   4. Signal Traceability     — which signals drove the decision
 *   5. Decision Reasoning Trace — full WHY/HOW/WHAT audit
 *   6. Analyst Commentary      — human-voice review
 *   7. Institutional Learning  — replay summary
 *   8. Rule Performance        — calm audit list
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PageShell, Container } from '@/components/layout';
import { getEvaluation, getAllEvaluations } from '@/lib/evaluations';
import type { Verdict } from '@/lib/evaluations';
import { EvaluationProgression } from '@/components/system/EvaluationProgression';
import { SignalLayer } from '@/components/intelligence/SignalLayer';
import { DecisionIntelligence } from '@/components/intelligence/DecisionIntelligence';
import { PropagationLayer } from '@/components/intelligence/PropagationLayer';
import { MonitoringBlock } from '@/components/intelligence/MonitoringBlock';

export async function generateStaticParams() {
  return getAllEvaluations().map((e) => ({ slug: e.id }));
}

const verdictColor: Record<Verdict, string> = {
  Confirmed:            'text-[var(--io-status-olive)]',
  'Partially Confirmed': 'text-[var(--io-status-amber)]',
  Revised:              'text-[var(--io-status-red)]',
  Inconclusive:         'text-[var(--io-text-tertiary)]',
};

function vColor(verdict: Verdict): string {
  return verdictColor[verdict] ?? 'text-[var(--io-text-tertiary)]';
}

export default async function EvaluationPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const e = getEvaluation(slug);
  if (!e) notFound();

  return (
    <PageShell>
      <Container>

        {/* Back */}
        <div className="pt-8 pb-3">
          <Link
            href="/evaluation"
            className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-200"
          >
            ← All evaluations
          </Link>
        </div>

        {/* ═══════════════════════════════════════════════════════
           EVALUATION PROGRESSION (live data collection when active)
           ═══════════════════════════════════════════════════════ */}
        <EvaluationProgression scenarioId={e.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           EVALUATION IDENTITY
           ═══════════════════════════════════════════════════════ */}
        <header className="pt-4 pb-16 sm:pb-20">
          <div className="io-meta mb-6">
            <span className="io-label">Evaluation</span>
            <span className={`io-status ${vColor(e.verdict)}`}>
              {e.verdict}
            </span>
            <span className="tabular-nums">
              {(e.correctness * 100).toFixed(0)}%
            </span>
          </div>

          <h1 className="io-briefing-title mb-8 max-w-3xl">
            {e.scenarioTitle}
          </h1>

          <p className="io-prose-lg mb-6">
            {e.summary}
          </p>

          <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
            <Link
              href={`/scenario/${e.scenarioRef}`}
              className="text-[0.8125rem] font-medium text-[var(--io-text-tertiary)] hover:text-[var(--io-charcoal)] transition-colors duration-200"
            >
              View scenario →
            </Link>
            <Link
              href={`/decision/${e.scenarioRef}`}
              className="text-[0.8125rem] font-medium text-[var(--io-text-tertiary)] hover:text-[var(--io-charcoal)] transition-colors duration-200"
            >
              View decision brief →
            </Link>
          </div>
        </header>

        <hr className="io-divider-accent" />

        {/* ═══════════════════════════════════════════════════════
           OUTCOME ASSESSMENT — expected vs actual
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <p className="io-label mb-6">Outcome Assessment</p>

          <div className="max-w-3xl space-y-12">
            <div>
              <p className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)] mb-3">
                Expected
              </p>
              <p className="io-prose">
                {e.expectedOutcome}
              </p>
            </div>

            <div>
              <p className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)] mb-3">
                Actual
              </p>
              <p className="io-prose">
                {e.actualOutcome}
              </p>
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════
           CORRECTNESS — verdict with rationale
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <p className="io-label mb-6">Correctness</p>

          <p className="text-[1.125rem] font-bold text-[var(--io-charcoal)] mb-6">
            <span className={vColor(e.verdict)}>{e.verdict}</span>
            <span className="text-[var(--io-text-tertiary)] font-normal mx-2">at</span>
            <span className="tabular-nums">{(e.correctness * 100).toFixed(0)}%</span>
          </p>

          <p className="io-prose">
            {e.correctnessRationale}
          </p>
        </section>

        {/* ═══════════════════════════════════════════════════════
           SIGNAL TRACEABILITY
           ═══════════════════════════════════════════════════════ */}
        <SignalLayer scenarioId={e.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           PROPAGATION — how pressure spread
           ═══════════════════════════════════════════════════════ */}
        <PropagationLayer scenarioId={e.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           DECISION REASONING TRACE
           ═══════════════════════════════════════════════════════ */}
        <DecisionIntelligence scenarioId={e.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           MONITORING — accountability chain (live only)
           ═══════════════════════════════════════════════════════ */}
        <MonitoringBlock scenarioId={e.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           ANALYST COMMENTARY
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <p className="io-label mb-6">Analyst Commentary</p>
          <p className="io-prose">
            {e.analystCommentary}
          </p>
        </section>

        {/* ═══════════════════════════════════════════════════════
           INSTITUTIONAL LEARNING — replay summary
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <p className="io-label mb-6">Replay Summary</p>
          <p className="io-prose">
            {e.replaySummary}
          </p>
        </section>

        {/* ═══════════════════════════════════════════════════════
           RULE PERFORMANCE — institutional audit
           ═══════════════════════════════════════════════════════ */}
        <section className="py-16 sm:py-20">
          <p className="io-label mb-6">Rule Performance</p>

          <ol className="space-y-4 max-w-3xl io-stagger">
            {e.rulePerformance.map((rule, i) => (
              <li
                key={i}
                className="io-numbered-item"
              >
                <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
                {rule}
              </li>
            ))}
          </ol>
        </section>

        {/* ═══════════════════════════════════════════════════════
           BRIEFING FOOTER
           ═══════════════════════════════════════════════════════ */}
        <footer className="py-10 border-t border-[var(--io-border-muted)]">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-y-6 gap-x-8 max-w-3xl">
            <div>
              <p className="io-label mb-1.5">Reference</p>
              <p className="io-footer-text">{e.id}</p>
            </div>
            <div>
              <p className="io-label mb-1.5">Evaluated</p>
              <p className="io-footer-text">
                {new Date(e.evaluatedDate).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                })}
              </p>
            </div>
            <div>
              <p className="io-label mb-1.5">Scenario</p>
              <Link
                href={`/scenario/${e.scenarioRef}`}
                className="io-footer-text hover:text-[var(--io-text-secondary)] transition-colors duration-200"
              >
                View scenario →
              </Link>
            </div>
            <div>
              <p className="io-label mb-1.5">Decision</p>
              <Link
                href={`/decision/${e.scenarioRef}`}
                className="io-footer-text hover:text-[var(--io-text-secondary)] transition-colors duration-200"
              >
                View directive →
              </Link>
            </div>
          </div>
        </footer>

      </Container>
    </PageShell>
  );
}
