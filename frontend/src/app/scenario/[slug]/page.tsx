/**
 * Scenario Briefing — /scenario/[slug]
 *
 * Five narrative sections rendered as structured prose.
 * No components. No dashboard patterns. No cards.
 *
 *   Context     — severity · domain · horizon · title · summary · significance
 *   Transmission — framing sentence → vertical causal chain
 *   Impact      — framing sentence → flat exposure register
 *   Decision    — framing sentence → ordered action directives
 *   Outcome     — prose paragraph → monitoring criteria
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

// ── Static generation ───────────────────────────────────────────────

export function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }));
}

// ── Page ─────────────────────────────────────────────────────────────

export default async function ScenarioBriefingPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const s = getScenario(slug);
  if (!s) notFound();

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
            href="/"
            className="
              inline-flex items-center gap-1.5 mb-10
              text-[0.8125rem] text-tx-tertiary
              hover:text-tx-primary transition-colors
            "
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M9 3L5 7l4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Back
          </Link>

          {/* ─────────────────────────────────────────────────────────
              CONTEXT
             ───────────────────────────────────────────────────────── */}

          {/* Metadata line */}
          <div className="flex items-center gap-3 flex-wrap mb-5">
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
            <span className="text-[0.6875rem] text-tx-tertiary">&middot;</span>
            <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
              {s.sectors} sectors
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

          {/* Summary */}
          <p className="mt-7 text-[1.0625rem] leading-[1.7] text-tx-primary">
            {s.summary}
          </p>

          {/* Significance */}
          <p className="mt-5 text-[0.9375rem] leading-[1.7] text-tx-secondary">
            {s.significance}
          </p>

          {/* ─────────────────────────────────────────────────────────
              TRANSMISSION
             ───────────────────────────────────────────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              How Pressure Transmits
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
              {s.transmissionFraming}
            </p>

            {/* Chain */}
            <ol className="space-y-0">
              {s.transmissionChain.map((step, idx) => (
                <li key={idx} className="relative flex gap-5">
                  {/* Left rail: dot + connector */}
                  <div className="flex flex-col items-center flex-shrink-0 w-5 pt-[7px]">
                    <div className="w-[7px] h-[7px] rounded-full bg-charcoal flex-shrink-0" />
                    {idx < s.transmissionChain.length - 1 && (
                      <div className="w-px flex-1 bg-border-muted mt-1" aria-hidden="true" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="pb-10 min-w-0">
                    {/* Origin → Destination */}
                    <p className="text-[0.9375rem] font-semibold text-tx-primary leading-[1.3]">
                      {step.origin}
                      <span className="text-tx-tertiary font-normal mx-2">&rarr;</span>
                      {step.destination}
                    </p>

                    {/* Mechanism */}
                    <p className="mt-2 text-[0.875rem] leading-[1.65] text-tx-secondary">
                      {step.mechanism}
                    </p>

                    {/* Delay */}
                    <p className="mt-2 text-[0.75rem] text-tx-tertiary tabular-nums">
                      {step.delay}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          {/* ─────────────────────────────────────────────────────────
              IMPACT
             ───────────────────────────────────────────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Institutional Exposure
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
              {s.impactFraming}
            </p>

            {/* Register */}
            <div className="border-t border-border-muted">
              {s.exposureRegister.map((entry, idx) => {
                const sevColor: Record<string, string> = {
                  Critical: "text-status-red",
                  Elevated: "text-status-amber",
                  Moderate: "text-tx-secondary",
                  Low: "text-tx-tertiary",
                };
                return (
                  <div
                    key={idx}
                    className="
                      grid grid-cols-[1fr_auto] sm:grid-cols-[140px_minmax(0,1.4fr)_72px]
                      gap-x-5 gap-y-1 py-5 border-b border-border-muted
                      items-baseline
                    "
                  >
                    {/* Entity + sector */}
                    <div className="sm:pr-2">
                      <p className="text-[0.875rem] font-medium text-tx-primary leading-[1.3]">
                        {entry.entity}
                      </p>
                      <p className="text-[0.6875rem] text-tx-tertiary mt-0.5">
                        {entry.sector}
                      </p>
                    </div>

                    {/* Exposure */}
                    <p className="text-[0.8125rem] leading-[1.6] text-tx-secondary col-span-1 sm:col-span-1">
                      {entry.exposure}
                    </p>

                    {/* Severity */}
                    <span
                      className={`
                        text-[0.6875rem] font-medium uppercase tracking-[0.04em]
                        ${sevColor[entry.severity]}
                        text-right sm:text-right
                      `}
                    >
                      {entry.severity}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ─────────────────────────────────────────────────────────
              DECISION
             ───────────────────────────────────────────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Required Response
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
              {s.decisionFraming}
            </p>

            {/* Actions */}
            <ol className="space-y-8">
              {s.actions.map((a, idx) => (
                <li key={idx}>
                  {/* Action sentence */}
                  <p className="text-[0.9375rem] leading-[1.6] text-tx-primary">
                    <span className="font-semibold tabular-nums text-tx-tertiary mr-2">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    {a.action}
                  </p>

                  {/* Metadata line */}
                  <p className="mt-1.5 text-[0.75rem] text-tx-tertiary">
                    {a.owner}
                    <span className="mx-2">&middot;</span>
                    <span className="tabular-nums">{a.deadline}</span>
                    <span className="mx-2">&middot;</span>
                    {a.sector}
                  </p>
                </li>
              ))}
            </ol>
          </section>

          {/* ─────────────────────────────────────────────────────────
              OUTCOME
             ───────────────────────────────────────────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Expected Outcome
            </p>

            {/* Prose */}
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
