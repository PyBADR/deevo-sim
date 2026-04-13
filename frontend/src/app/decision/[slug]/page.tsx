/**
 * Impact Observatory | مرصد الأثر — Decision Briefing
 *
 * A sovereign-grade directive document.
 * Read top to bottom like a board-level decision memo.
 *
 *   1. Directive Identity  — classification, imperative title, summary
 *   2. Primary Directive   — the single dominant action, with rationale
 *   3. Decision Intelligence — WHY / HOW / WHAT reasoning trace
 *   4. Supporting Actions   — subordinate measures in numbered prose
 *   5. Expected Effect      — aggregate outcome and monitoring criteria
 *   6. Briefing Footer      — reference, issued, origin, distribution
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PageShell, Container } from '@/components/layout';
import { getDecision, getAllDecisions } from '@/lib/decisions';
import { DecisionReaction } from '@/components/system/DecisionReaction';
import { DecisionIntelligence } from '@/components/intelligence/DecisionIntelligence';
import { SignalLayer } from '@/components/intelligence/SignalLayer';
import { MonitoringBlock } from '@/components/intelligence/MonitoringBlock';
import { EntityExposureHighlight } from '@/components/intelligence/EntityExposureHighlight';

export async function generateStaticParams() {
  return getAllDecisions().map((d) => ({ slug: d.id }));
}

const classificationColor: Record<string, string> = {
  Severe:   'text-[var(--io-status-red)]',
  High:     'text-[var(--io-status-red)]',
  Elevated: 'text-[var(--io-status-amber)]',
  Guarded:  'text-[var(--io-text-tertiary)]',
};

function cColor(level: string): string {
  return classificationColor[level] ?? 'text-[var(--io-text-tertiary)]';
}

export default async function DecisionPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const b = getDecision(slug);
  if (!b) notFound();

  const pd = b.primaryDirective;

  return (
    <PageShell>
      <Container>

        {/* Back */}
        <div className="pt-8 pb-3">
          <Link
            href="/decision"
            className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-200"
          >
            ← All directives
          </Link>
        </div>

        {/* ═══════════════════════════════════════════════════════
           DECISION REACTION (live posture when scenario active)
           ═══════════════════════════════════════════════════════ */}
        <DecisionReaction
          scenarioId={b.scenarioRef}
          classification={b.classification}
        />

        {/* ═══════════════════════════════════════════════════════
           DIRECTIVE IDENTITY
           ═══════════════════════════════════════════════════════ */}
        <header className="pt-4 pb-16 sm:pb-20">
          <div className="io-meta mb-6">
            <span className="io-label">Directive</span>
            <span className={`io-status ${cColor(b.classification)}`}>
              {b.classification}
            </span>
          </div>

          <h1 className="io-briefing-title mb-8 max-w-3xl">
            {b.directiveTitle}
          </h1>

          <p className="io-prose-lg mb-6">
            {b.summary}
          </p>

          <Link
            href={`/scenario/${b.scenarioRef}`}
            className="text-[0.8125rem] font-medium text-[var(--io-text-tertiary)] hover:text-[var(--io-charcoal)] transition-colors duration-200"
          >
            View scenario analysis →
          </Link>
        </header>

        <hr className="io-divider-accent" />

        {/* ═══════════════════════════════════════════════════════
           PRIMARY DIRECTIVE — the dominant action
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <p className="io-label mb-6">Primary Directive</p>

          <p className="text-[1.125rem] sm:text-[1.25rem] font-bold leading-[1.45] text-[var(--io-charcoal)] max-w-3xl mb-4">
            {pd.action}
          </p>

          <p className="io-prose mb-12">
            {pd.owner} must execute within {pd.deadline}. Sector: {pd.sector}.
          </p>

          <div className="max-w-3xl space-y-10">
            <div>
              <p className="io-label mb-3">Rationale</p>
              <p className="io-prose">
                {pd.rationale}
              </p>
            </div>

            <div>
              <p className="io-label mb-3">If Not Executed</p>
              <p className="io-prose">
                {pd.consequenceOfInaction}
              </p>
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════
           SIGNAL CONTEXT — dominant signal driving this decision
           ═══════════════════════════════════════════════════════ */}
        <SignalLayer scenarioId={b.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           DECISION INTELLIGENCE (posture + advisory when live)
           ═══════════════════════════════════════════════════════ */}
        <DecisionIntelligence scenarioId={b.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           SUPPORTING ACTIONS
           ═══════════════════════════════════════════════════════ */}
        {b.supportingActions.length > 0 && (
          <section className="io-section">
            <p className="io-label mb-6">Supporting Actions</p>

            <div className="space-y-6 io-stagger">
              {b.supportingActions.map((a, i) => (
                <div key={i} className="max-w-3xl">
                  <p className="io-numbered-item">
                    <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
                    <span className="font-semibold text-[var(--io-charcoal)]">{a.action}</span>
                  </p>
                  <p className="text-[0.8125rem] text-[var(--io-text-tertiary)] mt-1.5 pl-6">
                    {a.owner} · {a.deadline} · {a.sector}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ═══════════════════════════════════════════════════════
           ENTITY EXPOSURE — who is at risk (live only)
           ═══════════════════════════════════════════════════════ */}
        <EntityExposureHighlight scenarioId={b.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           MONITORING — execution / monitoring / escalation (live)
           ═══════════════════════════════════════════════════════ */}
        <MonitoringBlock scenarioId={b.scenarioRef} />

        {/* ═══════════════════════════════════════════════════════
           EXPECTED EFFECT & MONITORING
           ═══════════════════════════════════════════════════════ */}
        <section className="py-16 sm:py-20">
          <p className="io-label mb-4">Expected Effect</p>
          <p className="io-prose-lg mt-6">
            {b.expectedEffect}
          </p>

          <div className="mt-16">
            <p className="io-label mb-6">What Confirms the Path</p>
            <ol className="space-y-4 max-w-3xl io-stagger">
              {b.monitoringCriteria.map((criterion, i) => (
                <li
                  key={i}
                  className="io-numbered-item"
                >
                  <span className="text-[var(--io-text-tertiary)] tabular-nums mr-2.5">{i + 1}.</span>
                  {criterion}
                </li>
              ))}
            </ol>
          </div>

          <div className="mt-12">
            <Link
              href={`/evaluation/${b.id}`}
              className="text-[0.8125rem] font-medium text-[var(--io-text-tertiary)] hover:text-[var(--io-charcoal)] transition-colors duration-200"
            >
              View evaluation →
            </Link>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════
           BRIEFING FOOTER
           ═══════════════════════════════════════════════════════ */}
        <footer className="py-10 border-t border-[var(--io-border-muted)]">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-y-6 gap-x-8 max-w-3xl">
            <div>
              <p className="io-label mb-1.5">Reference</p>
              <p className="io-footer-text">{b.id}</p>
            </div>
            <div>
              <p className="io-label mb-1.5">Issued</p>
              <p className="io-footer-text">
                {new Date(b.issued).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                })}
              </p>
            </div>
            <div>
              <p className="io-label mb-1.5">Origin</p>
              <Link
                href={`/scenario/${b.scenarioRef}`}
                className="io-footer-text hover:text-[var(--io-text-secondary)] transition-colors duration-200"
              >
                Scenario briefing →
              </Link>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <p className="io-label mb-1.5">Distribution</p>
              <p className="io-footer-text leading-relaxed">
                {b.distribution.join(' · ')}
              </p>
            </div>
          </div>
        </footer>

      </Container>
    </PageShell>
  );
}
