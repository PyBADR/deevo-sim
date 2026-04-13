/**
 * Impact Observatory | مرصد الأثر — Evaluation Register
 *
 * Institutional accountability ledger. Post-decision reviews
 * ordered by verdict. Calm authority. Prose-led.
 */

import Link from 'next/link';
import { PageShell, Container } from '@/components/layout';
import { getEvaluationsByVerdict } from '@/lib/evaluations';
import type { Verdict } from '@/lib/evaluations';
import { brand } from '@/lib/copy';

const verdictColor: Record<Verdict, string> = {
  Confirmed:            'text-[var(--io-status-olive)]',
  'Partially Confirmed': 'text-[var(--io-status-amber)]',
  Revised:              'text-[var(--io-status-red)]',
  Inconclusive:         'text-[var(--io-text-tertiary)]',
};

export default function EvaluationRegisterPage() {
  const evaluations = getEvaluationsByVerdict();

  return (
    <PageShell>
      <Container>

        <header className="pt-20 sm:pt-28 pb-16 sm:pb-20">
          <p className="io-label-lg mb-5">Accountability</p>
          <h1 className="io-hero max-w-3xl mb-8" style={{ fontSize: '2.25rem' }}>
            Decision Evaluation
          </h1>
          <p className="io-subhero">
            Post-decision review for each scenario. Expected outcomes compared against
            actual results, with analyst commentary and institutional learning.
          </p>
        </header>

        <hr className="io-divider-accent" />

        <ol className="divide-y divide-[var(--io-border-muted)] io-stagger">
          {evaluations.map((e) => (
            <li key={e.id}>
              <Link
                href={`/evaluation/${e.id}`}
                className="group block py-7 sm:py-8 transition-colors duration-200 hover:bg-[var(--io-warm)]/40 -mx-6 sm:-mx-8 lg:-mx-12 px-6 sm:px-8 lg:px-12"
              >
                <div className="io-meta mb-3">
                  <span className={`io-status ${verdictColor[e.verdict]}`}>
                    {e.verdict}
                  </span>
                  <span className="tabular-nums">
                    {(e.correctness * 100).toFixed(0)}% correctness
                  </span>
                </div>

                <p className="text-[1.0625rem] font-semibold text-[var(--io-charcoal)] group-hover:text-[var(--io-graphite)] transition-colors duration-200 mb-2.5 leading-snug">
                  {e.scenarioTitle}
                </p>

                <p className="text-[0.875rem] leading-[1.75] text-[var(--io-text-secondary)] max-w-3xl">
                  {e.summary}
                </p>
              </Link>
            </li>
          ))}
        </ol>

        <div className="io-footer">
          <span className="io-footer-text">
            {brand.name} · {brand.nameAr}
          </span>
          <span className="io-footer-text">
            {evaluations.length} evaluations
          </span>
        </div>

      </Container>
    </PageShell>
  );
}
