/**
 * Evaluation Register — /evaluation
 *
 * Index of all evaluated scenarios.
 * Same institutional register pattern as the landing and decision pages.
 * No dashboard. No analytics console. Structured prose.
 *
 * Uses PageShell and Container from @/components/layout.
 * Everything else is native HTML with Tailwind.
 */

import Link from "next/link";
import { PageShell } from "@/components/layout/PageShell";
import { Container } from "@/components/layout/Container";
import {
  getEvaluationsByVerdict,
  verdictBadgeStyle,
} from "@/lib/evaluations";

// ── Page ─────────────────────────────────────────────────────────────

export default function EvaluationRegisterPage() {
  const ordered = getEvaluationsByVerdict();

  const confirmed = ordered.filter((e) => e.verdict === "Confirmed").length;
  const partial = ordered.filter((e) => e.verdict === "Partially Confirmed").length;
  const revised = ordered.filter((e) => e.verdict === "Revised").length;
  const inconclusive = ordered.filter((e) => e.verdict === "Inconclusive").length;

  return (
    <PageShell>
      <Container>
        <article className="pt-10 pb-24 max-w-[720px]">

          {/* ─────────────────────────────────────────────────────────
              CONTEXT
             ───────────────────────────────────────────────────────── */}

          <h1
            className="
              text-[clamp(1.75rem,4vw,2.75rem)] font-semibold
              leading-[1.08] tracking-[-0.03em]
              text-charcoal text-balance
            "
          >
            Decision Evaluation
          </h1>

          <p className="mt-7 text-[1.0625rem] leading-[1.7] text-tx-primary">
            Systematic comparison of expected outcomes against actual results
            across {ordered.length} evaluated scenarios. Each evaluation
            answers three questions: did the recommended decisions execute,
            did the projected outcomes materialize, and what should
            the institution change for next time.
          </p>

          <p className="mt-5 text-[0.9375rem] leading-[1.7] text-tx-secondary">
            {confirmed} confirmed, {partial} partially confirmed,
            {revised > 0 ? ` ${revised} revised,` : ""}
            {inconclusive > 0 ? ` ${inconclusive} inconclusive.` : ""}
            {" "}Evaluations are ordered by verdict — scenarios
            requiring the most attention appear first.
          </p>

          {/* ─────────────────────────────────────────────────────────
              EVALUATION REGISTER
             ───────────────────────────────────────────────────────── */}
          <section className="mt-16">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Evaluated Scenarios
            </p>

            <div className="border-t border-border-muted">
              {ordered.map((e) => (
                <Link
                  key={e.slug}
                  href={`/evaluation/${e.slug}`}
                  className="
                    block py-5 border-b border-border-muted
                    transition-colors hover:bg-bg-muted/40
                  "
                >
                  {/* Top line: verdict + correctness */}
                  <div className="flex items-center gap-3 mb-2">
                    <span
                      className={`
                        inline-flex items-center px-2.5 py-0.5 rounded-sm
                        text-[0.625rem] font-medium uppercase tracking-wider
                        ${verdictBadgeStyle(e.verdict)}
                      `}
                    >
                      {e.verdict}
                    </span>
                    <span className="text-[0.75rem] font-semibold tabular-nums text-tx-secondary">
                      {Math.round(e.correctness * 100)}%
                    </span>
                  </div>

                  {/* Scenario title */}
                  <h2 className="text-[1.0625rem] font-semibold tracking-[-0.01em] text-charcoal leading-[1.3]">
                    {e.scenarioTitle}
                  </h2>

                  {/* Summary */}
                  <p className="mt-1.5 text-[0.8125rem] leading-[1.6] text-tx-secondary">
                    {e.evaluationSummary}
                  </p>
                </Link>
              ))}
            </div>
          </section>

          {/* ── Footer ── */}
          <footer className="mt-24 pt-6 border-t border-border-muted flex items-end justify-between">
            <span className="text-[0.6875rem] text-tx-tertiary tracking-[0.02em]">
              GCC Macro Financial Intelligence
            </span>
            <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
              2026
            </span>
          </footer>
        </article>
      </Container>
    </PageShell>
  );
}
