/**
 * Impact Observatory — Centralized copy.
 * All user-facing strings for the product narrative.
 * Business language only. No technical jargon.
 */

export const hero = {
  title: "From Macro Signals to Economic Decisions",
  subtitle:
    "Understand how shocks move across GCC economies\u2014and who must act.",
} as const;

export const nav = {
  brand: "Impact Observatory",
  scenarios: "Scenarios",
  decisions: "Decisions",
  evaluation: "Evaluation",
} as const;

export const steps = {
  heading: "How It Works",
  items: [
    {
      number: "01",
      title: "Signal Detection",
      description:
        "A macro event is identified\u2014energy disruption, liquidity stress, regional escalation\u2014and its severity is assessed.",
    },
    {
      number: "02",
      title: "Economic Transmission",
      description:
        "The signal propagates through trade flows, banking channels, and commodity markets across GCC economies.",
    },
    {
      number: "03",
      title: "Sector Exposure",
      description:
        "Each sector\u2019s vulnerability is measured: energy, banking, insurance, real estate, government fiscal position.",
    },
    {
      number: "04",
      title: "Institutional Pressure",
      description:
        "Entities under stress are identified\u2014central banks, sovereign funds, port authorities\u2014with escalation thresholds.",
    },
    {
      number: "05",
      title: "Recommended Action",
      description:
        "Decision owners receive prioritized actions with cost-benefit analysis, deadlines, and escalation triggers.",
    },
    {
      number: "06",
      title: "Expected Outcome",
      description:
        "Each scenario projects loss ranges, recovery timelines, and value preserved through coordinated intervention.",
    },
    {
      number: "07",
      title: "Actual Outcome",
      description:
        "Post-event, actual results are compared against projections to evaluate decision quality and model accuracy.",
    },
    {
      number: "08",
      title: "Decision Evaluation",
      description:
        "Systematic replay: what was recommended, what was executed, what worked, and what to improve.",
    },
  ],
} as const;

export const scenarioGallery = {
  heading: "Scenario Library",
  subtitle:
    "Fifteen macro scenarios across energy, liquidity, trade, and geopolitical dimensions.",
} as const;

export const sectorCoverage = {
  heading: "Sector Coverage",
  subtitle:
    "Seven transmission layers from macro signals to institutional decisions.",
  sectors: [
    { label: "Oil & Gas", key: "energy" },
    { label: "Banking", key: "banking" },
    { label: "Insurance", key: "insurance" },
    { label: "Government", key: "government" },
    { label: "Real Estate", key: "real_estate" },
    { label: "Trade", key: "trade" },
    { label: "Fintech", key: "fintech" },
  ],
} as const;

export const whyItMatters = {
  heading: "Why It Matters",
  points: [
    {
      title: "Decision Speed",
      description:
        "Reduce decision latency from days to hours with pre-computed scenarios and ranked actions.",
    },
    {
      title: "Cross-border Visibility",
      description:
        "See how a shock in one GCC market transmits to others before the contagion materializes.",
    },
    {
      title: "Institutional Accountability",
      description:
        "Every recommendation is traceable\u2014owner, deadline, escalation trigger, expected outcome.",
    },
    {
      title: "Post-Decision Learning",
      description:
        "Compare expected outcomes against actual results to systematically improve future decisions.",
    },
  ],
} as const;

export const evaluation = {
  heading: "Decision Evaluation",
  subtitle:
    "Systematic comparison of expected outcomes against actual results.",
} as const;

/** Format helpers */
export function fmtUsd(n: number): string {
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  return `$${n.toLocaleString()}`;
}

export function fmtPct(n: number): string {
  return `${(n * 100).toFixed(0)}%`;
}

export function fmtDays(n: number): string {
  return `${n} day${n !== 1 ? "s" : ""}`;
}
