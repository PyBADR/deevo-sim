import type { ScenarioInput } from "../contracts/scenario-contract";
import type { IntelligenceSnapshot } from "../types/intelligence";
import { MOCK_INTELLIGENCE_SNAPSHOT } from "../mock/mock-snapshot";
import { GCC_BASELINE_NODES, GCC_BASELINE_EDGES, GCC_BASELINE_COUNTRY_STATES, GCC_BASELINE_SECTOR_STATES } from "../constants/gcc-baseline";
import { generatePropagation } from "./generate-propagation";
import { generateDecisionDirectives } from "./generate-decisions";
import { generateMonitoringStatuses } from "./generate-monitoring";

export function buildIntelligenceSnapshot(input: ScenarioInput): IntelligenceSnapshot {
  return {
    ...MOCK_INTELLIGENCE_SNAPSHOT,
    scenarioId: input.scenarioId,
    scenarioLabel: input.scenarioLabel,
    generatedAtIso: new Date().toISOString(),
    summary: `${input.scenarioLabel} is being interpreted through macro, regulatory, industrial, and transmission layers for GCC decision support.`,
    graphNodes: GCC_BASELINE_NODES,
    graphEdges: GCC_BASELINE_EDGES,
    countryStates: GCC_BASELINE_COUNTRY_STATES,
    sectorStates: GCC_BASELINE_SECTOR_STATES,
    propagation: generatePropagation(),
    decisions: generateDecisionDirectives(),
    monitoring: generateMonitoringStatuses(),
  };
}
