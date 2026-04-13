/**
 * EntityPressureList — entities under stress, ranked by severity.
 *
 * Pressure section. Shows which institutions face the most stress
 * and their classification. Quiet table-like layout.
 */

import type { KnowledgeGraphNode } from "@/types/observatory";

interface EntityPressureListProps {
  entities: KnowledgeGraphNode[];
}

function classificationColor(c: string): string {
  if (c === "CRITICAL") return "text-status-red";
  if (c === "ELEVATED") return "text-status-amber";
  return "text-tx-tertiary";
}

function layerLabel(layer: string): string {
  const MAP: Record<string, string> = {
    geography: "Geography",
    infrastructure: "Infrastructure",
    economy: "Economy",
    finance: "Finance",
    society: "Society",
  };
  return MAP[layer] ?? layer;
}

export function EntityPressureList({ entities }: EntityPressureListProps) {
  const sorted = [...entities]
    .filter((e) => (e.stress ?? 0) > 0)
    .sort((a, b) => (b.stress ?? 0) - (a.stress ?? 0));

  return (
    <section className="py-12 border-t border-border-muted">
      {/* Section label */}
      <p className="text-[0.625rem] font-medium uppercase tracking-[0.12em] text-tx-tertiary mb-3">
        Pressure
      </p>
      <h2 className="text-[1.5rem] font-semibold tracking-[-0.02em] text-charcoal mb-2">
        Entities under stress
      </h2>
      <p className="text-[0.9375rem] leading-[1.6] text-tx-secondary max-w-[520px] mb-10">
        Institutions and infrastructure ranked by stress level.
        Critical entities require immediate attention.
      </p>

      {/* List */}
      <div className="max-w-[720px] divide-y divide-border-muted">
        {sorted.map((entity) => (
          <div
            key={entity.id}
            className="py-4 flex items-center justify-between gap-4"
          >
            {/* Left: name + layer */}
            <div className="min-w-0">
              <p className="text-[0.9375rem] font-medium text-tx-primary truncate">
                {entity.label}
              </p>
              <p className="text-[0.6875rem] text-tx-tertiary uppercase tracking-[0.04em] mt-0.5">
                {layerLabel(entity.layer)} &middot; {entity.type}
              </p>
            </div>

            {/* Right: stress + classification */}
            <div className="flex items-center gap-5 flex-shrink-0">
              <span className="text-[0.9375rem] font-semibold tabular-nums text-charcoal">
                {Math.round((entity.stress ?? 0) * 100)}%
              </span>
              <span
                className={`text-[0.6875rem] font-medium uppercase tracking-[0.06em] ${classificationColor(entity.classification ?? "NOMINAL")}`}
              >
                {entity.classification ?? "NOMINAL"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
