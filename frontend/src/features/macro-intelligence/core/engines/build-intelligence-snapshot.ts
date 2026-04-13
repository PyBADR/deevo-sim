import type { ScenarioInput } from "../contracts/scenario-contract";
import type { IntelligenceSnapshot } from "../types/intelligence";
import { MOCK_INTELLIGENCE_SNAPSHOT } from "../mock/mock-snapshot";

export function buildIntelligenceSnapshot(input: ScenarioInput): IntelligenceSnapshot {
  return {
    ...MOCK_INTELLIGENCE_SNAPSHOT,
    scenarioId: input.scenarioId,
    scenarioLabel: input.scenarioLabel,
    generatedAtIso: new Date().toISOString(),
    summary: `${input.scenarioLabel} is being interpreted through macro, regulatory, industrial, and transmission layers for GCC decision support.`,
  };
}
