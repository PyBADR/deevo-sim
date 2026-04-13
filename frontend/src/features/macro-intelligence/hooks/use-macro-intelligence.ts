"use client";

import { useMemo } from "react";
import { buildIntelligenceSnapshot } from "../core";
import type { ScenarioInput } from "../core";

export function useMacroIntelligence() {
  const snapshot = useMemo(() => {
    const input: ScenarioInput = {
      scenarioId: "strait-of-hormuz-partial-blockage",
      scenarioLabel: "Strait of Hormuz Partial Blockage",
      trigger: "Partial maritime disruption across the Strait of Hormuz",
      description:
        "A macro-intelligence test scenario used to simulate GCC transmission across energy, logistics, banking, and insurance.",
      primaryCountries: ["saudi_arabia", "uae", "kuwait", "qatar", "bahrain", "oman"],
      primarySectors: ["oil_and_gas", "logistics", "banking", "insurance"],
      severity: 0.82,
      horizonHours: 72,
    };

    return buildIntelligenceSnapshot(input);
  }, []);

  return { snapshot };
}
