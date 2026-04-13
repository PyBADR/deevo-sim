/**
 * Evaluation Briefing — /evaluation/[slug]
 *
 * Post-decision institutional accountability document.
 * Six vertical sections rendered as structured prose:
 *
 *   Header              — verdict, correctness, title, summary, cross-links
 *   Outcome Assessment  — expected vs actual (stacked, not side-by-side)
 *   Correctness         — verdict line + rationale paragraph
 *   Analyst Commentary  — human-voice institutional feedback
 *   Institutional Learning — replay summary, lessons, precedent value
 *   Rule Performance    — numbered audit list of rules and outcomes
 *
 * Uses PageShell and Container from @/components/layout.
 * Everything else is native HTML with Tailwind.
 */

import { notFound } from "next/navigation";
import Link from "next/link";
import { PageShell } from "@/components/layout/PageShell";
import { Container } from "@/components/layout/Container";
import {
  getEvaluation,
  getAllEvaluationSlugs,
  verdictBadgeStyle,
  verdictColor,
} from "@/lib/evaluations";

// ── Static generation ───────────────────────────────────────────────

export function generateStaticParams() {
  return getAllEvaluationSlugs().map((slug) => ({ slug }));
}

// ── Page ─────────────────────────────��───────────────────────────────

export default async function EvaluationBriefingPage({
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
        <article className="pt-10 pb-24 max-w-[720px]">

          {/* ────────────────���────────────────────────────────────────
              HEADER — Evaluation Identity
             ────────���──────────────────────────────────────────────── */}

          {/* Back */}
          <Link
            href="/evaluation"
            className="
              inline-flex items-center gap-1.5 mb-10
              text-[0.8125rem] text-tx-tertiary
              hover:text-tx-primary transition-colors
            "
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M9 3L5 7l4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            All evaluations
          </Link>

          {/* Verdict + correctness */}
          <div className="flex items-center gap-3 flex-wrap mb-5">
            <span className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary">
              Evaluation
            </span>
            <span
              className={`
                inline-flex items-center px-2.5 py-0.5 rounded-sm
                text-[0.625rem] font-medium uppercase tracking-wider
                ${verdictBadgeStyle(e.verdict)}
              `}
            >
              {e.verdict}
            </span>
            <span className={`text-[1.125rem] font-semibold tabular-nums ${verdictColor(e.verdict)}`}>
              {Math.round(e.correctness * 100)}%
            </span>
          </div>

          {/* Title */}
          <h1
            className="
              text-[clamp(1.75rem,4vw,2.75rem)] font-semibold
              leading-[1.08] tracking-[-0.03em]
              text-charcoal text-balance
            "
          >
            {e.scenarioTitle}
          </h1>

          {/* Summary */}
          <p className="mt-7 text-[1.0625rem] leading-[1.7] text-tx-primary">
            {e.evaluationSummary}
          </p>

          {/* Cross-links */}
          <div className="mt-5 flex items-center gap-5 flex-wrap">
            <Link
              href={`/scenario/${e.slug}`}
              className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
            >
              View scenario &rarr;
            </Link>
            <Link
              href={`/decisions`}
              className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
            >
              View decisions &rarr;
            </Link>
          </div>

          {/* ───────────��─────────────────────────────────────────────
              SECTION 1 — Outcome Assessment
             ─────────────��───────────────────────────────���─────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-6">
              Outcome Assessment
            </p>

            {/* Expected */}
            <div className="mb-8">
              <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-2">
                Expected
              </p>
              <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary">
                {e.expected}
              </p>
            </div>

            {/* Actual */}
            <div>
              <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-2">
                Actual
              </p>
              <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
                {e.actual}
              </p>
            </div>
          </section>

          {/* ────────��────────────────────────────────────────────────
              SECTION 2 — Correctness
             ────────────────���───────────────────────────────��──────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Correctness
            </p>

            {/* Verdict line */}
            <p className={`text-[1.125rem] font-semibold leading-[1.3] ${verdictColor(e.verdict)}`}>
              {e.verdict} at {Math.round(e.correctness * 100)}%
            </p>

            {/* Rationale */}
            <p className="mt-4 text-[0.9375rem] leading-[1.7] text-tx-secondary">
              {e.correctnessRationale}
            </p>
          </section>

          {/* ────────��─────────────────────────────��──────────────────
              SECTION 3 — Analyst Commentary
             ─────────────────────��───────────────────────────���─────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Analyst Commentary
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
              {e.analystCommentary}
            </p>
          </section>

          {/* ─────────────────────────��─────────────────────────────���─
              SECTION 4 — Institutional Learning
             ─────────────���─────────────────────���───────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Replay Summary
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
              {e.replaySummary}
            </p>
          </section>

          {/* ─────────────────────────────────────────────────────��───
              SECTION 5 — Rule Performance
             ────────────���────────────────────────────────────��─────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-6">
              Rule Performance
            </p>

            <ol className="border-t border-border-muted">
              {e.rulePerformance.map((r, idx) => (
                <li
                  key={idx}
                  className="py-5 border-b border-border-muted"
                >
                  <p className="text-[0.9375rem] leading-[1.5] text-tx-primary">
                    <span className="font-semibold tabular-nums text-tx-tertiary mr-2">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    {r.rule}
                  </p>
                  <p className="mt-2 text-[0.8125rem] leading-[1.65] text-tx-secondary">
                    {r.outcome}
                  </p>
                </li>
              ))}
            </ol>
          </section>

          {/* ── Footer ── */}
          <footer className="mt-24 pt-6 border-t border-border-muted">
            <div className="flex items-center gap-5 flex-wrap mb-4">
              <Link
                href={`/scenario/${e.slug}`}
                className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
              >
                Scenario briefing &rarr;
              </Link>
              <Link
                href="/decisions"
                className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
              >
                Decision register &rarr;
              </Link>
            </div>
            <div className="flex items-end justify-between">
              <span className="text-[0.6875rem] text-tx-tertiary tracking-[0.02em]">
                Evaluated {e.evaluatedDate}
              </span>
              <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
                2026
              </span>
            </div>
          </footer>
        </article>
      </Container>
    </PageShell>
  );
}
