/**
 * Impact Observatory | مرصد الأثر — Executive Landing
 *
 * The entry point to a sovereign macroeconomic intelligence surface.
 * Not a dashboard. Not a report. An institutional reading environment.
 *
 * Structure:
 *   1. Hero — one dominant message, one supporting line
 *   2. Methodology — three-phase intelligence pipeline (text, not diagram)
 *   3. Scenario Register — active scenarios by severity
 *   4. Sector Coverage — which domains are under observation
 *   5. Geographic Scope — GCC institutional identity
 */

import Link from 'next/link';
import { PageShell, Container } from '@/components/layout';
import { getScenariosBySeverity } from '@/lib/scenarios';
import { brand, landing } from '@/lib/copy';

const severityColor: Record<string, string> = {
  Severe:   'text-[var(--io-status-red)]',
  High:     'text-[var(--io-status-red)]',
  Elevated: 'text-[var(--io-status-amber)]',
  Guarded:  'text-[var(--io-text-tertiary)]',
};

export default function LandingPage() {
  const scenarios = getScenariosBySeverity();

  const severeCount = scenarios.filter(s => s.severity === 'Severe').length;
  const highCount = scenarios.filter(s => s.severity === 'High').length;
  const elevatedCount = scenarios.filter(s => s.severity === 'Elevated').length;

  return (
    <PageShell>
      <Container>

        {/* ═══════════════════════════════════════════════════════
           HERO — one message, one line, one surface
           ═══════════════════════════════════════════════════════ */}
        <header className="pt-20 sm:pt-28 pb-20 sm:pb-24">
          <p className="io-label-lg mb-5">GCC Macroeconomic Intelligence</p>
          <h1 className="io-hero max-w-3xl mb-8">
            {brand.tagline}
          </h1>
          <p className="io-subhero mb-12">
            {brand.description}
          </p>

          {/* Severity summary — three quiet numbers */}
          <div className="flex items-baseline gap-8 sm:gap-12">
            {severeCount > 0 && (
              <div>
                <span className="text-[1.5rem] font-bold tabular-nums text-[var(--io-status-red)]">{severeCount}</span>
                <span className="text-[0.8125rem] text-[var(--io-text-tertiary)] ml-2">Severe</span>
              </div>
            )}
            {highCount > 0 && (
              <div>
                <span className="text-[1.5rem] font-bold tabular-nums text-[var(--io-status-red)]/70">{highCount}</span>
                <span className="text-[0.8125rem] text-[var(--io-text-tertiary)] ml-2">High</span>
              </div>
            )}
            {elevatedCount > 0 && (
              <div>
                <span className="text-[1.5rem] font-bold tabular-nums text-[var(--io-status-amber)]">{elevatedCount}</span>
                <span className="text-[0.8125rem] text-[var(--io-text-tertiary)] ml-2">Elevated</span>
              </div>
            )}
            <div>
              <span className="text-[1.5rem] font-bold tabular-nums text-[var(--io-charcoal)]">{scenarios.length}</span>
              <span className="text-[0.8125rem] text-[var(--io-text-tertiary)] ml-2">Active</span>
            </div>
          </div>
        </header>

        <hr className="io-divider-accent" />

        {/* ═══════════════════════════════════════════════════════
           METHODOLOGY — three phases, prose-led
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <p className="io-label mb-4">How This Works</p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-10 sm:gap-14 mt-10 io-stagger">
            {landing.steps.map((step) => (
              <div key={step.number}>
                <p className="text-[0.75rem] font-semibold text-[var(--io-text-tertiary)] mb-3 tabular-nums tracking-wider">
                  {step.number}
                </p>
                <p className="text-[1rem] font-semibold text-[var(--io-charcoal)] mb-3 leading-snug">
                  {step.title}
                </p>
                <p className="text-[0.875rem] leading-[1.75] text-[var(--io-text-secondary)]">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════
           SCENARIO REGISTER — active scenarios by severity
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <div className="flex flex-wrap items-baseline justify-between gap-4 mb-12">
            <div>
              <p className="io-label mb-3">{landing.scenariosHeading}</p>
              <p className="text-[0.9375rem] leading-relaxed text-[var(--io-text-secondary)] max-w-2xl">
                {landing.scenariosSubheading}
              </p>
            </div>
          </div>

          <ol className="divide-y divide-[var(--io-border-muted)] io-stagger">
            {scenarios.map((s) => (
              <li key={s.id}>
                <Link
                  href={`/scenario/${s.id}`}
                  className="group block py-7 sm:py-8 transition-colors duration-200 hover:bg-[var(--io-warm)]/40 -mx-6 sm:-mx-8 lg:-mx-12 px-6 sm:px-8 lg:px-12"
                >
                  {/* Metadata */}
                  <div className="io-meta mb-3">
                    <span className={`io-status ${severityColor[s.severity] || 'text-[var(--io-text-tertiary)]'}`}>
                      {s.severity}
                    </span>
                    <span>{s.domain}</span>
                    <span className="tabular-nums">{s.horizonHours}h horizon</span>
                  </div>

                  {/* Title */}
                  <p className="text-[1.0625rem] font-semibold text-[var(--io-charcoal)] group-hover:text-[var(--io-graphite)] transition-colors duration-200 mb-2.5 leading-snug">
                    {s.title}
                  </p>

                  {/* Significance */}
                  <p className="text-[0.875rem] leading-[1.75] text-[var(--io-text-secondary)] max-w-3xl mb-3">
                    {s.significance}
                  </p>

                  {/* Sector exposure */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1">
                    {s.sectors.map((sector) => (
                      <span
                        key={sector}
                        className="text-[0.75rem] text-[var(--io-text-tertiary)]"
                      >
                        {sector}
                      </span>
                    ))}
                  </div>
                </Link>
              </li>
            ))}
          </ol>
        </section>

        {/* ═══════════════════════════════════════════════════════
           SECTOR COVERAGE — what domains are under observation
           ═══════════════════════════════════════════════════════ */}
        <section className="io-section">
          <p className="io-label mb-4">{landing.sectorsHeading}</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 sm:gap-10 mt-10 max-w-4xl io-stagger">
            {landing.sectors.map((sector) => (
              <div key={sector.name}>
                <p className="text-[0.9375rem] font-semibold text-[var(--io-charcoal)] mb-1.5">
                  {sector.name}
                </p>
                <p className="text-[0.8125rem] leading-[1.7] text-[var(--io-text-tertiary)]">
                  {sector.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════
           WHY THIS MATTERS — institutional purpose
           ═══════════════════════════════════════════════════════ */}
        <section className="py-16 sm:py-20">
          <p className="io-label mb-4">{landing.whyHeading}</p>
          <p className="io-prose-lg mt-6 max-w-3xl">
            {landing.whyBody}
          </p>
        </section>

        {/* ═══════════════════════════════════════════════════════
           FOOTER
           ═══════════════════════════════════════════════════════ */}
        <div className="io-footer">
          <span className="io-footer-text">
            {brand.name} · {brand.nameAr}
          </span>
          <span className="io-footer-text">
            {scenarios.length} scenarios · GCC · {new Date().getFullYear()}
          </span>
        </div>

      </Container>
    </PageShell>
  );
}
