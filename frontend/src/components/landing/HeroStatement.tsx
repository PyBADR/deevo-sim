/**
 * HeroStatement — primary landing statement.
 *
 * Full-width, large typography, warm neutral palette.
 * One headline, one supporting line, one CTA, one anchor link.
 * No imagery. No icons. No blue.
 */

import { Container } from "@/components/layout/Container";
import { hero } from "@/lib/copy";

export function HeroStatement() {
  return (
    <section className="relative pt-20 pb-18 sm:pt-30 sm:pb-22 overflow-hidden">
      {/* Subtle radial gradient — warm, not cool */}
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 20% 40%, rgba(27,27,25,0.025) 0%, transparent 100%)",
        }}
      />

      <Container>
        <div className="relative max-w-[740px]">
          {/* Eyebrow */}
          <p
            className="
              text-[0.6875rem] font-medium uppercase tracking-[0.12em]
              text-tx-tertiary mb-6
            "
          >
            GCC Macro Financial Intelligence
          </p>

          {/* Headline */}
          <h1
            className="
              text-[clamp(2.75rem,6vw,4.5rem)] font-semibold leading-[1.04]
              tracking-[-0.035em] text-charcoal text-balance
            "
          >
            {hero.title}
          </h1>

          {/* Supporting line */}
          <p
            className="
              mt-7 text-[1.25rem] sm:text-[1.375rem] leading-[1.55]
              tracking-[-0.01em] text-tx-secondary
              max-w-[480px] text-balance
            "
          >
            {hero.subtitle}
          </p>

          {/* Actions */}
          <div className="mt-12 flex items-center gap-6 flex-wrap">
            {/* Primary CTA */}
            <a
              href="/command-center"
              className="
                inline-flex items-center gap-2.5 px-7 py-3.5
                bg-charcoal text-white
                text-[0.8125rem] font-medium leading-none
                rounded-[10px]
                transition-all duration-200 ease-out
                hover:bg-graphite hover:shadow-card
                active:scale-[0.98]
              "
            >
              Explore Scenarios
              <svg
                width="15"
                height="15"
                viewBox="0 0 15 15"
                fill="none"
                className="opacity-50"
                aria-hidden="true"
              >
                <path
                  d="M5.5 3L10.5 7.5L5.5 12"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>

            {/* Secondary anchor */}
            <a
              href="#how-it-works"
              className="
                text-[0.8125rem] font-medium text-tx-tertiary
                underline underline-offset-4 decoration-border-soft
                transition-colors duration-150
                hover:text-tx-primary hover:decoration-tx-tertiary
              "
            >
              How it works
            </a>
          </div>

          {/* Summary stats — quiet, factual */}
          <div
            className="
              mt-16 flex items-center gap-8 sm:gap-12
              pt-8 border-t border-border-muted
            "
          >
            <StatLine label="Scenarios" value="15" />
            <StatLine label="GCC Economies" value="6" />
            <StatLine label="Transmission Layers" value="9" />
            <StatLine label="Sectors Covered" value="7" />
          </div>
        </div>
      </Container>
    </section>
  );
}

function StatLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span
        className="
          text-[1.375rem] font-semibold tabular-nums leading-none
          text-charcoal tracking-[-0.02em]
        "
      >
        {value}
      </span>
      <span
        className="
          mt-1.5 text-[0.6875rem] font-medium uppercase tracking-[0.06em]
          text-tx-tertiary
        "
      >
        {label}
      </span>
    </div>
  );
}
