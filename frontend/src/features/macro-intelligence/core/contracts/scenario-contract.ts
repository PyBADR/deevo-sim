import type { IntelligenceSnapshot } from "../types/intelligence";

export interface ScenarioInput {
  scenarioId: string;
  scenarioLabel: string;
  trigger: string;
  description: string;
  primaryCountries: string[];
  primarySectors: string[];
  severity: number;
  horizonHours: number;
}

export interface ScenarioToSnapshotContract {
  input: ScenarioInput;
  output: IntelligenceSnapshot;
}
