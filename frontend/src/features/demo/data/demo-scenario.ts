/**
 * Impact Observatory | Demo Scenario Data
 *
 * Curated, presentation-grade data for the executive demo.
 * DEMO_MODE flag isolates this from real API pipelines.
 */

export const DEMO_MODE = true;

export interface TransmissionNode {
  id: string;
  label: string;
  description: string;
  delay: number; // seconds before this node activates in animation
}

export interface TransmissionEdge {
  from: string;
  to: string;
  label: string;
}

export interface GCCCountryImpact {
  country: string;
  flag: string;
  sectorStress: number; // 0–1
  estimatedLoss: string;
  impactLevel: "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL";
  topSector: string;
  /** Short explainability note: what causes this country's impact */
  driver: string;
}

export interface SectorImpact {
  name: string;
  icon: string;
  signal: string;
  impact: string;
  riskLevel: "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL";
  explanation: string;
}

export interface DecisionAction {
  title: string;
  owner: string;
  urgency: "IMMEDIATE" | "24H" | "72H";
  expectedEffect: string;
}

export const demoScenario = {
  id: "hormuz_chokepoint_disruption",
  name: "Strait of Hormuz Partial Blockage",
  nameAr: "إغلاق جزئي لمضيق هرمز",
  severity: 0.72,
  severityLabel: "Elevated" as const,
  lossWithoutAction: 4.9e9,
  lossWithAction: 4.3e9,
  lossSaved: 0.6e9,
  confidence: 0.84,
  nodesImpacted: 31,
  timeHorizon: "168 hours",

  // Step 3 — Shock
  shock: {
    headline: "Maritime disruption reduces oil transit by 60%",
    details: [
      {
        label: "Oil Supply Disruption",
        value: "60%",
        description: "Transit volume reduction through the strait",
      },
      {
        label: "Shipping Slowdown",
        value: "12–18 days",
        description: "Average delay on rerouted vessels via Cape of Good Hope",
      },
      {
        label: "Time Horizon",
        value: "72 hours",
        description: "Critical window for first-order economic effects",
      },
    ],
  },

  // Step 4 — Transmission
  transmission: {
    nodes: [
      { id: "oil", label: "Oil & Energy", description: "Crude transit halted", delay: 0 },
      { id: "shipping", label: "Maritime & Shipping", description: "Route rerouting", delay: 0.8 },
      { id: "banking", label: "Banking & Finance", description: "Liquidity stress", delay: 1.6 },
      { id: "insurance", label: "Insurance", description: "Claims surge", delay: 2.4 },
      { id: "government", label: "Government & Fiscal", description: "Fiscal pressure", delay: 3.2 },
    ] as TransmissionNode[],
    edges: [
      { from: "oil", to: "shipping", label: "Price spike" },
      { from: "shipping", to: "banking", label: "Trade finance freeze" },
      { from: "banking", to: "insurance", label: "Liquidity stress" },
      { from: "insurance", to: "government", label: "Claims surge" },
    ] as TransmissionEdge[],
    cascadeLabels: [
      "Crude prices surge 40% within hours",
      "Shipping routes reroute — costs triple",
      "Trade finance lines freeze across GCC banks",
      "Marine & energy insurance claims spike 280%",
      "Fiscal reserves under pressure — stabilization needed",
    ],
  },

  // Step 5 — GCC Impact
  countries: [
    { country: "Saudi Arabia", flag: "SA", sectorStress: 0.68, estimatedLoss: "$1.8B", impactLevel: "ELEVATED", topSector: "Oil & Gas", driver: "Largest crude exporter via Hormuz — direct export volume loss" },
    { country: "UAE", flag: "AE", sectorStress: 0.61, estimatedLoss: "$1.1B", impactLevel: "ELEVATED", topSector: "Banking", driver: "Trade finance hub — letter of credit exposure to in-transit cargo" },
    { country: "Kuwait", flag: "KW", sectorStress: 0.55, estimatedLoss: "$480M", impactLevel: "MODERATE", topSector: "Oil & Gas", driver: "Oil revenue dependence (90%+ fiscal) amplifies price volatility" },
    { country: "Qatar", flag: "QA", sectorStress: 0.49, estimatedLoss: "$420M", impactLevel: "MODERATE", topSector: "LNG Export", driver: "LNG tanker rerouting adds 12-day delay and $8M per cargo" },
    { country: "Bahrain", flag: "BH", sectorStress: 0.42, estimatedLoss: "$210M", impactLevel: "MODERATE", topSector: "Insurance", driver: "Regional reinsurance center — war-risk premium cascade" },
    { country: "Oman", flag: "OM", sectorStress: 0.58, estimatedLoss: "$310M", impactLevel: "MODERATE", topSector: "Port & Shipping", driver: "Salalah/Sohar ports directly on disrupted route corridor" },
  ] as GCCCountryImpact[],

  // Step 6 — Sector Impact
  sectors: [
    {
      name: "Oil & Gas",
      icon: "fuel",
      signal: "Crude transit volume dropped to 40% of baseline",
      impact: "Spot price surge, forward contracts repricing",
      riskLevel: "CRITICAL",
      explanation: "The Strait of Hormuz handles 21% of global oil flow. A 60% disruption triggers immediate repricing across all GCC crude benchmarks.",
    },
    {
      name: "Banking & Finance",
      icon: "landmark",
      signal: "Interbank liquidity tightening detected",
      impact: "Credit lines frozen on trade finance",
      riskLevel: "ELEVATED",
      explanation: "Trade finance exposure to maritime routes creates cascading liquidity pressure. Letters of credit for in-transit cargo become distressed assets.",
    },
    {
      name: "Insurance",
      icon: "shield",
      signal: "Marine hull and cargo claims surging 280%",
      impact: "Reinsurance capacity under pressure",
      riskLevel: "ELEVATED",
      explanation: "War-risk premiums activate across all GCC maritime policies. Reinsurers invoke force majeure clauses, creating coverage gaps.",
    },
    {
      name: "Fintech & Payments",
      icon: "smartphone",
      signal: "Cross-border payment latency increasing",
      impact: "Settlement delays on trade corridors",
      riskLevel: "MODERATE",
      explanation: "Payment rails linked to trade settlement slow as underlying transactions enter dispute. Digital wallet top-ups from trade income decline.",
    },
    {
      name: "Real Estate",
      icon: "building",
      signal: "Foreign investment inflows pausing",
      impact: "Project financing uncertainty",
      riskLevel: "LOW",
      explanation: "Second-order effect as investor confidence shifts. Active mega-projects in UAE/Saudi face construction material supply delays via maritime routes.",
    },
    {
      name: "Government & Fiscal",
      icon: "university",
      signal: "Oil revenue projections revised downward",
      impact: "Strategic reserve activation likely",
      riskLevel: "ELEVATED",
      explanation: "Fiscal breakeven prices shift as export volumes drop. Sovereign wealth funds may need to inject liquidity to stabilize domestic markets.",
    },
  ] as SectorImpact[],

  // Step 7 — Decisions
  decisions: [
    {
      title: "Activate strategic petroleum reserves",
      owner: "Ministry of Energy",
      urgency: "IMMEDIATE",
      expectedEffect: "Stabilize crude supply for 14 days, prevent price spiral above $130/bbl",
    },
    {
      title: "Inject emergency liquidity into interbank market",
      owner: "Central Bank",
      urgency: "IMMEDIATE",
      expectedEffect: "Unfreeze trade finance lines, restore letter of credit processing",
    },
    {
      title: "Reroute maritime traffic via alternative corridors",
      owner: "Port Authority",
      urgency: "24H",
      expectedEffect: "Reduce delivery delays from 18 days to 8 days via Suez/Red Sea routes",
    },
    {
      title: "Adjust credit exposure limits on energy sector",
      owner: "Banking Regulator (SAMA / CBUAE)",
      urgency: "24H",
      expectedEffect: "Prevent cascading defaults in energy-linked loan portfolios",
    },
    {
      title: "Stabilize digital payment rails and settlement systems",
      owner: "Payment Infrastructure Authority",
      urgency: "72H",
      expectedEffect: "Maintain cross-border payment SLA below 4-hour settlement window",
    },
  ] as DecisionAction[],

  // Step 8 — Outcome (THE MONEY SHOT)
  outcome: {
    withoutAction: {
      totalLoss: "$4.9B",
      lossRaw: 4.9e9,
      recoveryTimeline: "21–30 days",
      riskEscalation: "+45%",
      description: "Without intervention, supply disruption compounds through banking and insurance channels. Trade finance freeze extends to 3 weeks. Insurance coverage gaps trigger secondary defaults.",
      why: "Cascading transmission across 5 sectors amplifies the initial maritime shock into a region-wide financial event.",
    },
    withAction: {
      totalLoss: "$4.3B",
      lossRaw: 4.3e9,
      recoveryTimeline: "5–7 days",
      riskReduction: "62%",
      description: "Coordinated response across energy, banking, and fiscal authorities contains the shock within 72 hours. Maritime rerouting reduces supply gap. Liquidity injection prevents credit freeze cascade.",
      why: "Early intervention breaks the transmission chain between banking and insurance, preventing secondary cascade.",
    },
    saved: {
      amount: "$600M",
      amountRaw: 0.6e9,
      explanation: "Net savings from coordinated central bank liquidity injection, strategic reserve activation, and maritime corridor rerouting within the 24–72h decision window.",
    },
  },

  // Step 9 — Trust
  trust: {
    confidence: 0.84,
    dataFreshness: "<10 minutes",
    validationMethod: "Multi-signal validated",
    dataSources: [
      "AIS Maritime Traffic (simulated)",
      "Central Bank Interbank Rates (modeled)",
      "ACLED Geopolitical Events (reference)",
      "GCC Exchange Market Data (synthetic)",
      "Insurance Claims Registry (projected)",
    ],
    assumptions: [
      "60% transit volume reduction sustained for 168 hours",
      "No military escalation beyond maritime disruption",
      "Central bank reserves sufficient for 14-day intervention",
      "Reinsurance contracts honor force majeure within 48 hours",
    ],
    modelVersion: "IO Simulation Engine v2.4",
    lastCalibration: "2026-03-15",
    footerPipeline: "Signal \u2192 Transmission \u2192 Decision \u2192 Outcome \u2192 Audit",
  },
};
