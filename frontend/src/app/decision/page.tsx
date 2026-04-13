/**
 * Impact Observatory | مرصد الأثر — Decision Register
 *
 * Institutional ledger of sovereign-grade directives.
 * Ordered by classification severity. Prose-led. Calm authority.
 */

import Link from 'next/link';
import { PageShell, Container } from '@/components/layout';
import { getDecisionsByClassification } from '@/lib/decisions';
import { brand } from '@/lib/copy';

const classificationColor: Record<string, string> = {
  Severe:   'text-[var(--io-status-red)]',
  High:     'text-[var(--io-status-red)]',
  Elevated: 'text-[var(--io-status-amber)]',
  Guarded:  'text-[var(--io-text-tertiary)]',
};

function cColor(level: string): string {
  return classificationColor[level] ?? 'text-[var(--io-text-tertiary)]';
}

export default function DecisionRegisterPage() {
  const decisions = getDecisionsByClassification();

  return (
    <PageShell>
      <Container>

        <header className="pt-20 sm:pt-28 pb-16 sm:pb-20">
          <p className="io-label-lg mb-5">Directives</p>
          <h1 className="io-hero max-w-3xl mb-8" style={{ fontSize: '2.25rem' }}>
            Decision Briefings
          </h1>
          <p className="io-subhero">
            Sovereign-grade directives issued for each active scenario. Primary actions,
            institutional owners, response deadlines, and expected effects — ordered by
            classification severity.
          </p>
        </header>

        <hr className="io-divider-accent" />

        <ol className="divide-y divide-[var(--io-border-muted)] io-stagger">
          {decisions.map((d) => (
            <li key={d.id}>
              <Link
                href={`/decision/${d.id}`}
                className="group block py-7 sm:py-8 transition-colors duration-200 hover:bg-[var(--io-warm)]/40 -mx-6 sm:-mx-8 lg:-mx-12 px-6 sm:px-8 lg:px-12"
              >
                <div className="io-meta mb-3">
                  <span className={`io-status ${cColor(d.classification)}`}>
                    {d.classification}
                  </span>
                  <span>{d.primaryDirective.owner}</span>
                  <span className="tabular-nums">{d.primaryDirective.deadline}</span>
                </div>

                <p className="text-[1.0625rem] font-semibold text-[var(--io-charcoal)] group-hover:text-[var(--io-graphite)] transition-colors duration-200 mb-2.5 leading-snug">
                  {d.directiveTitle}
                </p>

                <p className="text-[0.875rem] leading-[1.75] text-[var(--io-text-secondary)] max-w-3xl">
                  {d.summary}
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
            {decisions.length} directives
          </span>
        </div>

      </Container>
    </PageShell>
  );
}
