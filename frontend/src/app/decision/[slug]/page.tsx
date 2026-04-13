/**
 * Decision Briefing — /decision/[slug]
 *
 * Per-scenario decision directive. Extracts the Decision and Outcome
 * sections from the scenario briefing into a standalone page.
 * Cross-links to the scenario briefing and the evaluation.
 *
 * Uses PageShell and Container from @/components/layout.
 * Everything else is native HTML with Tailwind.
 */

import { notFound } from "next/navigation";
import Link from "next/link";
import { PageShell } from "@/components/layout/PageShell";
import { Container } from "@/components/layout/Container";
import {
  getScenario,
  getAllSlugs,
  severityWord,
  severityVariant,
} from "@/lib/scenarios";
import { getEvaluation } from "@/lib/evaluations";

// ── Static generation ────────────────���──────────────────────────────

export function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }));
}

// ── Page ───���───────────────────────────────────────────────────────���─

export default async function DecisionBriefingPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const s = getScenario(slug);
  if (!s) notFound();

  const evaluation = getEvaluation(slug);
  const badge = severityVariant(s.severity);
  const badgeStyles: Record<string, string> = {
    red: "bg-status-red/10 text-status-red",
    amber: "bg-status-amber/10 text-status-amber",
    olive: "bg-status-olive/10 text-status-olive",
  };

  return (
    <PageShell>
      <Container>
        <article className="pt-10 pb-24 max-w-[720px]">

          {/* Back */}
          <Link
            href="/decisions"
            className="
              inline-flex items-center gap-1.5 mb-10
              text-[0.8125rem] text-tx-tertiary
              hover:text-tx-primary transition-colors
            "
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M9 3L5 7l4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            All decisions
          </Link>

          {/* ──��──────────────────────────────────────────────────────
              HEADER
             ───────────────────────────────────────────────────────── */}

          {/* Metadata */}
          <div className="flex items-center gap-3 flex-wrap mb-5">
            <span className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary">
              Decision Directive
            </span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-sm text-[0.625rem] font-medium uppercase tracking-wider ${badgeStyles[badge]}`}>
              {severityWord(s.severity)}
            </span>
            <span className="text-[0.6875rem] text-tx-tertiary">
              {s.domain}
            </span>
            <span className="text-[0.6875rem] text-tx-tertiary">&middot;</span>
            <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
              {s.horizon}
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
            {s.title}
          </h1>

          {/* Cross-link to scenario */}
          <div className="mt-5">
            <Link
              href={`/scenario/${s.slug}`}
              className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
            >
              View scenario briefing &rarr;
            </Link>
          </div>

          {/* ─────────────────────────────────────────────────────────
              REQUIRED RESPONSE
             ───────────────────────────────────────────────────────── */}
          <section className="mt-16">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Required Response
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
              {s.decisionFraming}
            </p>

            <ol className="border-t border-border-muted">
              {s.actions.map((a, idx) => (
                <li
                  key={idx}
                  className="py-5 border-b border-border-muted"
                >
                  <p className="text-[0.9375rem] leading-[1.65] text-tx-primary">
                    <span className="font-semibold tabular-nums text-tx-tertiary mr-2">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    {a.action}
                  </p>
                  <p className="mt-2 text-[0.8125rem] leading-[1.6] text-tx-secondary">
                    {a.owner} must execute within {a.deadline}.
                  </p>
                </li>
              ))}
            </ol>
          </section>

          {/* ─────────────────────────────────────────────────────────
              EXPECTED EFFECT
             ──────────────────────────���────────────────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Expected Effect
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
              {s.outcomeNarrative}
            </p>

            {/* Monitoring criteria */}
            <div className="mt-10">
              <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-4">
                Monitoring Criteria
              </p>

              <ul className="space-y-4">
                {s.monitoringCriteria.map((criterion, idx) => (
                  <li
                    key={idx}
                    className="
                      pl-5 border-l-2 border-border-muted
                      text-[0.8125rem] leading-[1.65] text-tx-secondary
                    "
                  >
                    {criterion}
                  </li>
                ))}
              </ul>
            </div>

            {/* Evaluation cross-link */}
            {evaluation && (
              <div className="mt-10">
                <Link
                  href={`/evaluation/${s.slug}`}
                  className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
                >
                  View evaluation &rarr;
                </Link>
              </div>
            )}
          </section>

          {/* ── Footer ��─ */}
          <footer className="mt-24 pt-6 border-t border-border-muted">
            <div className="flex items-center gap-5 flex-wrap mb-4">
              <Link
                href={`/scenario/${s.slug}`}
                className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
              >
                Scenario briefing &rarr;
              </Link>
              {evaluation && (
                <Link
                  href={`/evaluation/${s.slug}`}
                  className="text-[0.8125rem] text-tx-tertiary hover:text-tx-primary transition-colors"
                >
                  Evaluation &rarr;
                </Link>
              )}
            </div>
            <div className="flex items-end justify-between">
              <span className="text-[0.6875rem] text-tx-tertiary tracking-[0.02em]">
                GCC Macro Financial Intelligence
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
