import type { IntelligenceSnapshot } from "../types/intelligence";

export const MOCK_INTELLIGENCE_SNAPSHOT: IntelligenceSnapshot = {
  scenarioId: "strait-of-hormuz-partial-blockage",
  scenarioLabel: "Strait of Hormuz Partial Blockage",
  generatedAtIso: new Date().toISOString(),
  topLineStatus: "high",
  summary:
    "Energy transit disruption is transmitting across GCC macro, banking, insurance, and logistics layers with escalation risk if action is delayed.",
  lensReadings: [
    {
      lens: "us_financial",
      headline: "Oil shock and risk repricing dominate",
      interpretation: "Markets read the event through oil, inflation, and capital repricing.",
      whyItMatters: "Funding conditions tighten as uncertainty moves into financial expectations.",
    },
    {
      lens: "eu_regulatory",
      headline: "Coordination and policy posture dominate",
      interpretation: "European reading emphasizes policy coordination, compliance risk, and sovereign signaling.",
      whyItMatters: "Weak regulatory posture amplifies loss through slower institutional response.",
    },
    {
      lens: "asia_industrial",
      headline: "Throughput and supply chain disruption dominate",
      interpretation: "Asian reading focuses on shipping, production continuity, and bottlenecks.",
      whyItMatters: "Industrial disruption can outlast the headline event through delayed throughput recovery.",
    },
  ],
  signals: [],
  graphNodes: [],
  graphEdges: [],
  countryStates: [],
  sectorStates: [],
  propagation: [],
  entityExposure: [],
  decisions: [],
  monitoring: [],
};
