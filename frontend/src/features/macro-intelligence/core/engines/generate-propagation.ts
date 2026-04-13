import type { PropagationStep } from "../types/intelligence";
import { GCC_BASELINE_NODES } from "../constants/gcc-baseline";

function node(id: string) {
  const found = GCC_BASELINE_NODES.find((n) => n.id === id);
  if (!found) {
    throw new Error(`Missing node: ${id}`);
  }
  return found;
}

export function generatePropagation(): PropagationStep[] {
  return [
    {
      step: 1,
      triggerNode: node("ras_tanura"),
      targetNode: node("aramco"),
      mechanism: "physical_constraint",
      effectSummary: "Export terminal throughput drops, reducing energy outflow and triggering revenue compression.",
      timeLagHours: 2,
      stressDelta: 0.18,
      lossDeltaUsd: 890_000_000,
    },
    {
      step: 2,
      triggerNode: node("aramco"),
      targetNode: node("brent"),
      mechanism: "price_transmission",
      effectSummary: "Oil benchmark reprices upward as disruption fear enters global expectations.",
      timeLagHours: 6,
      stressDelta: 0.14,
      lossDeltaUsd: 1_200_000_000,
    },
    {
      step: 3,
      triggerNode: node("ras_tanura"),
      targetNode: node("jebel_ali"),
      mechanism: "regional_rerouting",
      effectSummary: "Container backlog and rerouting pressure spill into UAE logistics capacity.",
      timeLagHours: 12,
      stressDelta: 0.11,
      lossDeltaUsd: 670_000_000,
    },
    {
      step: 4,
      triggerNode: node("sama"),
      targetNode: node("cbb"),
      mechanism: "confidence_signaling",
      effectSummary: "Financial stress transmits into Bahrain through regional liquidity and macro confidence channels.",
      timeLagHours: 24,
      stressDelta: 0.09,
      lossDeltaUsd: 410_000_000,
    },
  ];
}
