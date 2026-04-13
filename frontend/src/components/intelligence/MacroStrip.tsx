/**
 * Macro Context — Intelligence Component
 *
 * System posture statement for the active scenario.
 * Perspective-aware: adjusts framing for executive / analyst / regulator.
 * Includes temporal horizon, counterfactual baseline, and confidence basis.
 *
 * Reads from: useCommandCenterStore, useAppStore (persona).
 */

"use client";

import { useCommandCenterStore } from "@/features/command-center/lib/command-store";
import { useAppStore } from "@/store/app-store";

// ── Helpers ────────────────────────────────────────────────────────────

function formatUsd(n: number): string {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(0)}M`;
  return `$${n.toLocaleString()}`;
}

function postureWord(avg: number): string {
  if (avg >= 0.8) return "SEVERE";
  if (avg >= 0.65) return "HIGH";
  if (avg >= 0.5) return "ELEVATED";
  if (avg >= 0.35) return "GUARDED";
  if (avg >= 0.2) return "LOW";
  return "NOMINAL";
}

function postureColor(avg: number): string {
  if (avg >= 0.65) return "text-status-red";
  if (avg >= 0.35) return "text-status-amber";
  return "text-status-olive";
}

const GCC_CENTERS = [
  { code: "KSA", name: "Saudi Arabia", lat: 24.7, lng: 46.7 },
  { code: "UAE", name: "United Arab Emirates", lat: 25.0, lng: 55.2 },
  { code: "KWT", name: "Kuwait", lat: 29.3, lng: 47.9 },
  { code: "QAT", name: "Qatar", lat: 25.3, lng: 51.5 },
  { code: "BHR", name: "Bahrain", lat: 26.0, lng: 50.5 },
  { code: "OMN", name: "Oman", lat: 23.6, lng: 58.5 },
] as const;

function nearestCountry(lat: number, lng: number): string {
  let best: string = GCC_CENTERS[0].name;
  let d2 = Infinity;
  for (const c of GCC_CENTERS) {
    const v = (lat - c.lat) ** 2 + (lng - c.lng) ** 2;
    if (v < d2) { d2 = v; best = c.name; }
  }
  return best;
}

/** Map country → sectors active in that country (from graph nodes). */
function countrySectorMap(
  nodes: { label: string; layer: string; stress?: number; lat?: number; lng?: number }[],
) {
  const map = new Map<string, Map<string, { totalStress: number; count: number; topEntity: string; topStress: number }>>();
  for (const n of nodes) {
    const country = nearestCountry(n.lat ?? 25, n.lng ?? 52);
    const s = n.stress ?? 0;
    if (!map.has(country)) map.set(country, new Map());
    const sectors = map.get(country)!;
    const existing = sectors.get(n.layer);
    if (existing) {
      existing.totalStress += s;
      existing.count++;
      if (s > existing.topStress) { existing.topStress = s; existing.topEntity = n.label; }
    } else {
      sectors.set(n.layer, { totalStress: s, count: 1, topEntity: n.label, topStress: s });
    }
  }
  return map;
}

// ── Perspective framing ────────────────────────────────────────────────

function perspectiveFrame(
  persona: "executive" | "analyst" | "regulator",
  headline: { totalLossUsd: number; criticalCount: number; elevatedCount: number; peakDay: number; maxRecoveryDays: number; averageStress: number },
  scenario: { domain: string; horizonHours: number } | null,
): string {
  const loss = formatUsd(headline.totalLossUsd);
  const horizon = scenario ? `${scenario.horizonHours}h` : "active";

  switch (persona) {
    case "executive":
      return `The GCC financial system faces ${loss} in projected exposure over a ${horizon} horizon. ` +
        `${headline.criticalCount} entities have reached critical stress thresholds and require institutional response before day ${headline.peakDay}. ` +
        `Without intervention, recovery extends to ${headline.maxRecoveryDays} days.`;

    case "analyst":
      return `System-wide average stress at ${Math.round(headline.averageStress * 100)}% across the observation window. ` +
        `${headline.criticalCount} critical, ${headline.elevatedCount} elevated entities. ` +
        `Total projected loss ${loss} with ${headline.peakDay}-day peak and ${headline.maxRecoveryDays}-day recovery baseline. ` +
        `${scenario?.domain ?? "Multi-domain"} scenario, ${horizon} horizon.`;

    case "regulator":
      return `Supervisory alert: ${headline.criticalCount} regulated entities exceed stress thresholds requiring mandatory review. ` +
        `Aggregate exposure ${loss} across ${horizon} horizon. ` +
        `Escalation deadline day ${headline.peakDay}. ` +
        `Full recovery timeline ${headline.maxRecoveryDays} days under current trajectory.`;
  }
}

// ── Component ──────────────────────────────────────────────────────────

export function MacroStrip() {
  const headline = useCommandCenterStore((s) => s.headline);
  const graphNodes = useCommandCenterStore((s) => s.graphNodes);
  const scenario = useCommandCenterStore((s) => s.scenario);
  const counterfactual = useCommandCenterStore((s) => s.counterfactual);
  const confidence = useCommandCenterStore((s) => s.confidence);
  const trust = useCommandCenterStore((s) => s.trust);
  const macroContext = useCommandCenterStore((s) => s.macroContext);
  const status = useCommandCenterStore((s) => s.status);
  const persona = useAppStore((s) => s.persona);

  if (status !== "ready" || !headline) return null;

  const posture = postureWord(headline.averageStress);
  const pColor = postureColor(headline.averageStress);

  // Country × sector breakdown
  const csMap = countrySectorMap(graphNodes);
  const sortedCountries = Array.from(csMap.entries())
    .map(([country, sectors]) => {
      let totalStress = 0;
      let totalCount = 0;
      for (const s of sectors.values()) { totalStress += s.totalStress; totalCount += s.count; }
      return { country, avgStress: totalStress / totalCount, sectors };
    })
    .sort((a, b) => b.avgStress - a.avgStress);

  // Counterfactual baseline
  const baselineLoss = counterfactual?.baseline?.projected_loss_usd ?? 0;
  const recommendedLoss = counterfactual?.recommended?.projected_loss_usd ?? 0;
  const hasCounterfactual = baselineLoss > 0 && recommendedLoss > 0;

  // Confidence basis
  const stagesCount = trust?.stagesCompleted?.length ?? 0;
  const sourcesCount = trust?.dataSources?.length ?? 0;
  const confidencePct = Math.round((confidence || trust?.confidence || 0) * 100);

  return (
    <section>
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
        Macro Context
      </p>

      {/* Posture line */}
      <p className="text-[1.125rem] font-semibold leading-[1.3]">
        <span className={pColor}>{posture}</span>
        <span className="text-tx-tertiary font-normal mx-3">&mdash;</span>
        <span className="text-tx-primary">
          {formatUsd(headline.totalLossUsd)} exposure,{" "}
          {headline.nodesImpacted} entities,{" "}
          {scenario ? `${scenario.horizonHours}h horizon` : "active"}
        </span>
      </p>

      {/* Perspective-aware framing */}
      <p className="mt-4 text-[0.9375rem] leading-[1.7] text-tx-primary">
        {perspectiveFrame(persona, headline, scenario)}
      </p>

      {/* Temporal horizon */}
      <p className="mt-3 text-[0.9375rem] leading-[1.7] text-tx-secondary">
        Peak stress expected day {headline.peakDay}.
        {headline.maxRecoveryDays > 0 && ` Full recovery baseline: ${headline.maxRecoveryDays} days.`}
        {macroContext?.trigger_summary_en && ` ${macroContext.trigger_summary_en}`}
      </p>

      {/* Counterfactual baseline sentence */}
      {hasCounterfactual && (
        <p className="mt-3 text-[0.9375rem] leading-[1.7] text-tx-secondary">
          Without intervention, projected losses reach {formatUsd(baselineLoss)} over
          {counterfactual!.baseline.recovery_days > 0
            ? ` ${counterfactual!.baseline.recovery_days} days`
            : " the scenario horizon"}.
          Coordinated response reduces this to {formatUsd(recommendedLoss)}
          {counterfactual!.delta.loss_reduction_pct > 0
            ? ` — a ${Math.round(counterfactual!.delta.loss_reduction_pct)}% reduction`
            : ""}.
        </p>
      )}

      {/* Confidence basis sentence */}
      {confidencePct > 0 && (
        <p className="mt-3 text-[0.9375rem] leading-[1.7] text-tx-secondary">
          Analysis confidence at {confidencePct}%
          {stagesCount > 0 || sourcesCount > 0
            ? `, derived from ${stagesCount > 0 ? `${stagesCount} analytical stages` : ""}${stagesCount > 0 && sourcesCount > 0 ? " and " : ""}${sourcesCount > 0 ? `${sourcesCount} verified data sources` : ""}`
            : ""}
          .
          {trust?.warnings && trust.warnings.length > 0
            ? ` ${trust.warnings.length} analytical caveat${trust.warnings.length > 1 ? "s" : ""} noted.`
            : ""}
        </p>
      )}

      {/* Country-specific sector narratives */}
      {sortedCountries.length > 0 && (
        <div className="mt-10">
          <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-4">
            Jurisdiction Exposure
          </p>

          <div className="border-t border-border-muted">
            {sortedCountries.slice(0, 4).map(({ country, avgStress, sectors }) => {
              const sectorEntries = Array.from(sectors.entries())
                .map(([k, v]) => ({ name: k, avg: v.totalStress / v.count, top: v.topEntity, topStress: v.topStress }))
                .sort((a, b) => b.avg - a.avg);

              return (
                <div key={country} className="py-5 border-b border-border-muted">
                  <p className="text-[0.9375rem] font-semibold text-tx-primary leading-[1.3]">
                    {country}
                    <span className={`ml-3 tabular-nums text-[0.8125rem] font-medium ${postureColor(avgStress)}`}>
                      {Math.round(avgStress * 100)}%
                    </span>
                  </p>

                  {/* Country-specific sector narrative — prose, not list */}
                  <p className="mt-2 text-[0.8125rem] leading-[1.65] text-tx-secondary">
                    {sectorEntries.length === 1
                      ? `In ${country}, the ${sectorEntries[0].name} sector carries the concentration. ${sectorEntries[0].top} at ${Math.round(sectorEntries[0].topStress * 100)}% stress.`
                      : `In ${country}, ${sectorEntries[0].name} leads at ${Math.round(sectorEntries[0].avg * 100)}% average stress (${sectorEntries[0].top} at ${Math.round(sectorEntries[0].topStress * 100)}%). ` +
                        `${sectorEntries.length > 1 ? `${sectorEntries[1].name.charAt(0).toUpperCase() + sectorEntries[1].name.slice(1)} follows at ${Math.round(sectorEntries[1].avg * 100)}%.` : ""}` +
                        `${sectorEntries.length > 2 ? ` ${sectorEntries.slice(2).length} additional sector${sectorEntries.slice(2).length > 1 ? "s" : ""} under observation.` : ""}`
                    }
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
