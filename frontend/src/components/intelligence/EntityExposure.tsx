/**
 * Exposed Entities — Intelligence Component
 *
 * Country-specific entity exposure with transmission reason.
 * Grouped by GCC jurisdiction, not by abstract "layer."
 *
 * Each entity block:
 *   - Names the entity
 *   - States the stress level
 *   - Explains WHY it is exposed (incoming transmission edge)
 *   - Places it in country × sector context
 *
 * Perspective-aware:
 *   executive → institutional name + financial exposure
 *   analyst   → transmission weight + classification detail
 *   regulator → regulatory jurisdiction + supervisory threshold
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
  if (n > 0) return `$${n.toLocaleString()}`;
  return "";
}

function stressColor(v: number): string {
  if (v >= 0.7) return "text-status-red";
  if (v >= 0.4) return "text-status-amber";
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

function layerLabel(layer: string): string {
  const labels: Record<string, string> = {
    geography: "Geography",
    infrastructure: "Infrastructure",
    economy: "Economy",
    finance: "Finance",
    society: "Society",
  };
  return labels[layer] ?? layer.charAt(0).toUpperCase() + layer.slice(1);
}

/**
 * Perspective-specific entity exposure sentence.
 */
function exposureSentence(
  persona: "executive" | "analyst" | "regulator",
  entity: { label: string; stress: number; layer: string; classification: string },
  reason: string | null,
  estimatedLoss: number,
  country: string,
): string {
  const stressPct = Math.round(entity.stress * 100);

  switch (persona) {
    case "executive":
      return (
        `${entity.label} in ${country} at ${stressPct}% stress` +
        (estimatedLoss > 0 ? `, ${formatUsd(estimatedLoss)} estimated exposure` : "") +
        "." +
        (reason ? ` ${reason}.` : "")
      );

    case "analyst":
      return (
        `${entity.label} (${layerLabel(entity.layer)}, ${entity.classification}) at ${stressPct}% stress` +
        (estimatedLoss > 0 ? `. Estimated loss: ${formatUsd(estimatedLoss)}` : "") +
        "." +
        (reason ? ` Transmission: ${reason}.` : "")
      );

    case "regulator":
      return (
        `${entity.label} — ${country} jurisdiction, ${layerLabel(entity.layer)} sector, ${stressPct}% stress` +
        (entity.stress >= 0.65 ? " (exceeds supervisory threshold)" : "") +
        "." +
        (estimatedLoss > 0 ? ` Regulatory exposure: ${formatUsd(estimatedLoss)}.` : "") +
        (reason ? ` Cause: ${reason}.` : "")
      );
  }
}

// ── Component ──────────────────────────────────────────────────────────

export function EntityExposure() {
  const graphNodes = useCommandCenterStore((s) => s.graphNodes);
  const graphEdges = useCommandCenterStore((s) => s.graphEdges);
  const headline = useCommandCenterStore((s) => s.headline);
  const status = useCommandCenterStore((s) => s.status);
  const persona = useAppStore((s) => s.persona);

  if (status !== "ready" || graphNodes.length === 0) return null;

  // Build incoming edge map: target → best incoming edge
  const incomingEdges = new Map<string, { source: string; label: string; transmission: number }>();
  for (const edge of graphEdges) {
    const existing = incomingEdges.get(edge.target);
    if (!existing || (edge.transmission ?? 0) > existing.transmission) {
      incomingEdges.set(edge.target, {
        source: edge.source,
        label: edge.label ?? "",
        transmission: edge.transmission ?? 0,
      });
    }
  }
  const nodeMap = new Map(graphNodes.map((n) => [n.id, n.label]));

  // Sort by stress, take top entities
  const sorted = [...graphNodes].sort((a, b) => (b.stress ?? 0) - (a.stress ?? 0));
  const totalStress = sorted.reduce((s, n) => s + (n.stress ?? 0), 0);

  // Group by country
  const byCountry = new Map<string, typeof sorted>();
  for (const node of sorted) {
    const country = nearestCountry(node.lat ?? 25, node.lng ?? 52);
    if (!byCountry.has(country)) byCountry.set(country, []);
    byCountry.get(country)!.push(node);
  }

  // Sort countries by aggregate stress
  const countryOrder = Array.from(byCountry.entries())
    .map(([country, nodes]) => ({
      country,
      nodes,
      avgStress: nodes.reduce((s, n) => s + (n.stress ?? 0), 0) / nodes.length,
    }))
    .sort((a, b) => b.avgStress - a.avgStress);

  return (
    <section>
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-4">
        Exposed Entities
      </p>

      <p className="text-[0.9375rem] leading-[1.7] text-tx-secondary mb-10">
        {graphNodes.length} entities in the observation network
        across {countryOrder.length} GCC jurisdiction{countryOrder.length !== 1 ? "s" : ""}.
        {headline && headline.criticalCount > 0
          ? ` ${headline.criticalCount} at critical threshold, ${headline.elevatedCount} elevated.`
          : headline && headline.elevatedCount > 0
            ? ` ${headline.elevatedCount} at elevated threshold.`
            : ""}
      </p>

      {/* Country-grouped entities */}
      <div className="space-y-12">
        {countryOrder.map(({ country, nodes: countryNodes }) => {
          // Show top 3 per country
          const topNodes = countryNodes.slice(0, 3);

          return (
            <div key={country}>
              <p className="text-[0.6875rem] font-medium uppercase tracking-[0.08em] text-tx-tertiary mb-4">
                {country}
              </p>

              <div className="border-t border-border-muted">
                {topNodes.map((entity) => {
                  const stress = entity.stress ?? 0;
                  const classification = entity.classification ?? "MODERATE";
                  const incoming = incomingEdges.get(entity.id);
                  const sourceLabel = incoming ? nodeMap.get(incoming.source) ?? incoming.source : null;
                  const reason = incoming
                    ? (sourceLabel ? `${sourceLabel} — ${incoming.label}` : incoming.label)
                    : null;

                  const entityLoss = headline && totalStress > 0
                    ? Math.round(headline.totalLossUsd * (stress / totalStress))
                    : 0;

                  return (
                    <div key={entity.id} className="py-5 border-b border-border-muted">
                      {/* Entity name + stress */}
                      <p className="text-[0.9375rem] font-semibold text-tx-primary leading-[1.3]">
                        {entity.label}
                        <span className={`ml-3 tabular-nums text-[0.8125rem] font-medium ${stressColor(stress)}`}>
                          {Math.round(stress * 100)}%
                        </span>
                      </p>

                      {/* Prose exposure sentence — perspective-aware */}
                      <p className="mt-2 text-[0.875rem] leading-[1.65] text-tx-secondary">
                        {exposureSentence(
                          persona,
                          { label: entity.label, stress, layer: entity.layer, classification },
                          reason,
                          entityLoss,
                          country,
                        )}
                      </p>
                    </div>
                  );
                })}

                {/* Overflow count */}
                {countryNodes.length > 3 && (
                  <p className="py-3 text-[0.75rem] text-tx-tertiary">
                    {countryNodes.length - 3} additional entit{countryNodes.length - 3 === 1 ? "y" : "ies"} under observation in {country}.
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
