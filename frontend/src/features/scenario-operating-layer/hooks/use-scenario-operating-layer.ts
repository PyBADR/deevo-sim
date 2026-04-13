"use client";

import { useMemo, useState } from "react";
import { OPERATING_SCENARIOS } from "../data/scenarios";

export function useScenarioOperatingLayer() {
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(
    OPERATING_SCENARIOS.find((s) => s.status === "active")?.id ?? OPERATING_SCENARIOS[0]?.id ?? null
  );

  const scenarios = useMemo(() => OPERATING_SCENARIOS, []);
  const activeScenario = useMemo(
    () => scenarios.find((s) => s.id === activeScenarioId) ?? scenarios[0] ?? null,
    [scenarios, activeScenarioId]
  );

  return {
    scenarios,
    activeScenario,
    activeScenarioId,
    setActiveScenarioId,
  };
}
