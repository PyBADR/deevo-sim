import type { GCCCountry, SectorType, StressLevel } from "@/features/macro-intelligence/core";

export interface OperatingScenario {
  id: string;
  title: string;
  titleAr: string;
  icon: string;
  trigger: string;
  description: string;
  countries: GCCCountry[];
  sectors: SectorType[];
  severity: number;
  stressLevel: StressLevel;
  horizonHours: number;
  status: "ready" | "active" | "archived";
}

export interface ScenarioSelectionState {
  scenarios: OperatingScenario[];
  activeScenarioId: string | null;
}
