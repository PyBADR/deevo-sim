/**
 * Decision Register — /decisions
 *
 * Cross-scenario view of all required institutional responses.
 * Structured prose, not a dashboard. No cards. No metadata rows.
 *
 * Structure:
 *   Context       — what this page is, why it exists
 *   Active Decisions — grouped by scenario, each action as a prose directive
 *   Accountability  — what happens if deadlines pass
 *
 * Owner, deadline, and sector are woven into each action sentence.
 * They are not rendered as metadata rows.
 *
 * Uses PageShell and Container from @/components/layout.
 * Everything else is native HTML with Tailwind.
 */

import Link from "next/link";
import { PageShell } from "@/components/layout/PageShell";
import { Container } from "@/components/layout/Container";
import {
  scenarios,
  severityWord,
  severityVariant,
  type ScenarioBriefing,
} from "@/lib/scenarios";

// ── Helpers ─────────────────────────────────────────────────────────

/** Sort scenarios by severity descending */
function sortedScenarios(): ScenarioBriefing[] {
  return Object.values(scenarios).sort((a, b) => b.severity - a.severity);
}

function totalActions(): number {
  return Object.values(scenarios).reduce(
    (sum, s) => sum + s.actions.length,
    0
  );
}

function uniqueOwners(): string[] {
  const owners = new Set<string>();
  for (const s of Object.values(scenarios)) {
    for (const a of s.actions) {
      owners.add(a.owner);
    }
  }
  return Array.from(owners);
}

// ── Page ─────────────────────────────────────────────────────────────

export default function DecisionRegisterPage() {
  const ordered = sortedScenarios();
  const count = totalActions();
  const owners = uniqueOwners();

  const badgeStyles: Record<string, string> = {
    red: "bg-status-red/10 text-status-red",
    amber: "bg-status-amber/10 text-status-amber",
    olive: "bg-status-olive/10 text-status-olive",
  };

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
            Decision Register
          </h1>

          <p className="mt-7 text-[1.0625rem] leading-[1.7] text-tx-primary">
            {count} institutional actions across {ordered.length} active
            scenarios, assigned to {owners.length} decision owners.
            Each action below is a directive — a specific intervention
            that a named institution must execute within a stated deadline
            to contain the financial exposure described in its parent scenario.
          </p>

          <p className="mt-5 text-[0.9375rem] leading-[1.7] text-tx-secondary">
            Actions are grouped by scenario and ordered by severity.
            Within each scenario, actions appear in the sequence
            they must execute — earlier actions create the conditions
            for later ones to succeed. Skipping or delaying any action
            in the sequence degrades the effectiveness of all subsequent ones.
          </p>

          {/* ─────────────────────────────────────────────────────────
              ACTIVE DECISIONS — grouped by scenario
             ───────────────────────────────────────────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Active Decisions
            </p>

            <div className="space-y-16">
              {ordered.map((s) => {
                const badge = severityVariant(s.severity);
                return (
                  <div key={s.slug}>
                    {/* Scenario header */}
                    <div className="flex items-center gap-3 flex-wrap mb-3">
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

                    <h2 className="text-[1.25rem] font-semibold tracking-[-0.02em] text-charcoal leading-[1.2]">
                      <Link
                        href={`/scenario/${s.slug}`}
                        className="hover:text-tx-secondary transition-colors"
                      >
                        {s.title}
                      </Link>
                    </h2>

                    <p className="mt-2 text-[0.875rem] leading-[1.65] text-tx-secondary mb-6">
                      {s.decisionFraming}
                    </p>

                    {/* Actions as numbered prose directives */}
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
                  </div>
                );
              })}
            </div>
          </section>

          {/* ─────────────────────────────────────────────────────────
              ACCOUNTABILITY
             ───────────────────────────────────────────────────────── */}
          <section className="mt-20">
            <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
              Accountability
            </p>

            <p className="text-[0.9375rem] leading-[1.7] text-tx-primary">
              Every action in this register carries provenance. The observatory
              records who recommended it, what data supported the recommendation,
              the deadline by which it must execute, and the monitoring criteria
              that will determine whether it succeeded. After the decision window
              closes, actual outcomes are compared against projected outcomes
              to evaluate decision quality and improve future response.
            </p>

            <p className="mt-5 text-[0.9375rem] leading-[1.7] text-tx-secondary">
              Actions that miss their deadlines do not disappear. They are
              reclassified as overdue and escalated to the next level of
              institutional authority. The escalation trigger for each action
              is defined in its parent scenario briefing — the specific
              quantitative threshold that converts a recommendation into
              a mandatory response.
            </p>

            {/* Owner register */}
            <div className="mt-10">
              <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-4">
                Decision Owners
              </p>

              <ul className="space-y-2">
                {owners.map((owner) => {
                  const ownerActions: { scenario: string; action: string; deadline: string }[] = [];
                  for (const s of ordered) {
                    for (const a of s.actions) {
                      if (a.owner === owner) {
                        ownerActions.push({
                          scenario: s.title,
                          action: a.action,
                          deadline: a.deadline,
                        });
                      }
                    }
                  }
                  return (
                    <li
                      key={owner}
                      className="
                        pl-5 border-l-2 border-border-muted
                        text-[0.8125rem] leading-[1.65] text-tx-secondary
                      "
                    >
                      <span className="font-medium text-tx-primary">{owner}</span>
                      {" \u2014 "}
                      {ownerActions.length} action{ownerActions.length !== 1 ? "s" : ""} across {new Set(ownerActions.map((a) => a.scenario)).size} scenario{new Set(ownerActions.map((a) => a.scenario)).size !== 1 ? "s" : ""}
                    </li>
                  );
                })}
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
