import type { NarrativeLens } from "../types/intelligence";

export const NARRATIVE_LENSES: { id: NarrativeLens; label: string; focus: string }[] = [
  {
    id: "us_financial",
    label: "US Financial Lens",
    focus: "markets, rates, inflation, investor reaction",
  },
  {
    id: "eu_regulatory",
    label: "EU Regulatory Lens",
    focus: "policy, regulation, compliance, sovereign response",
  },
  {
    id: "asia_industrial",
    label: "Asia Industrial Lens",
    focus: "production, logistics, supply chain, throughput",
  },
];
