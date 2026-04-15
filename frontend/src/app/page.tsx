/**
 * Impact Observatory — Landing Page V2
 *
 * Institutional. Not a product page. Not SaaS.
 * This is the entry point to a macro intelligence system
 * used by GCC decision-makers: central bank governors,
 * sovereign wealth fund CIOs, ministry officials.
 *
 * Structure:
 *   Opening statement (hero)
 *   Scope (what it covers, briefly)
 *   Entry (single quiet link)
 *
 * That's it.
 */

import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-main flex flex-col">
      {/* ── Wordmark ── */}
      <header className="px-8 pt-8">
        <span className="text-[0.8125rem] font-medium tracking-[0.04em] text-tx-tertiary">
          Impact Observatory
        </span>
      </header>

      {/* ── Opening ── */}
      <main className="flex-1 flex items-center">
        <div className="w-full max-w-[900px] px-8 sm:px-12 py-20 sm:py-0">
          <h1
            className="
              text-[clamp(2.5rem,6vw,4.5rem)] font-semibold
              leading-[1.06] tracking-[-0.035em]
              text-charcoal text-balance
            "
          >
            GCC Decision
            <br />
            Intelligence Platform
          </h1>

          <p
            className="
              mt-6 text-[1.1875rem] sm:text-[1.3125rem]
              leading-[1.6] text-tx-secondary
              max-w-[500px]
            "
          >
            for Macro, Financial & Strategic Systems
          </p>

          <p
            className="
              mt-3 text-[1rem] sm:text-[1.125rem]
              leading-[1.6] text-tx-tertiary
              max-w-[500px]
            "
            dir="rtl"
          >
            للأنظمة الاقتصادية والمالية والاستراتيجية
          </p>

          {/* ── Value line ── */}
          <p className="mt-8 text-[0.9375rem] sm:text-[1rem] font-medium text-charcoal/80 tracking-[-0.01em] max-w-[500px]">
            Understand Impact. Control Transmission. Execute Decisions.
          </p>
          <p className="mt-2 text-[0.875rem] sm:text-[0.9375rem] text-tx-tertiary max-w-[500px]" dir="rtl">
            استشراف الأثر. فهم انتقاله. توجيه القرار.
          </p>

          {/* ── Trust strip ── */}
          <div className="mt-12 flex items-center gap-3 flex-wrap text-[0.6875rem] font-medium text-tx-tertiary uppercase tracking-[0.06em]">
            <span>Institutional Reference Dataset</span>
            <span className="w-1 h-1 rounded-full bg-tx-tertiary/40" />
            <span>17-Stage Simulation Engine</span>
            <span className="w-1 h-1 rounded-full bg-tx-tertiary/40" />
            <span>GCC Coverage</span>
          </div>

          {/* ── Entry ── */}
          <div className="mt-12">
            <Link
              href="/command-center?demo=true"
              className="
                inline-flex items-center gap-3
                text-[0.9375rem] font-medium text-charcoal
                border-b border-charcoal/30 pb-1
                transition-all duration-200
                hover:border-charcoal hover:gap-4
              "
            >
              Enter Executive Briefing
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M3 8h10M9 4l4 4-4 4"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </Link>
          </div>
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="px-8 pb-8 flex items-end justify-between">
        <span className="text-[0.6875rem] text-tx-tertiary tracking-[0.02em]">
          GCC Decision Intelligence Platform
        </span>
        <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
          2026
        </span>
      </footer>
    </div>
  );
}

