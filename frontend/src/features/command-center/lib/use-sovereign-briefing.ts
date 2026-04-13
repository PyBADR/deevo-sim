"use client";

/**
 * useSovereignBriefing — Bridge Hook
 *
 * Generates a SovereignBriefing for the command center page.
 * Two data paths:
 *
 *   Path A (preferred): useSystemState has an active scenario with intelligence
 *     → use that IntelligenceSnapshot directly
 *
 *   Path B (fallback): Command center has data from API/mock but no active
 *     system scenario → run the intelligence loop with command center params
 *
 * This hook is the SOLE data supplier for the canonical intelligence surface.
 * It replaces the deleted reading-sequence-store.
 */

import { useMemo } from "react";
import { useSystemState } from "@/lib/systemState";
import { useCommandCenterStore } from "./command-store";
import {
  generateSovereignBriefing,
  type SovereignBriefing,
} from "@/lib/intelligence/sovereignBriefingEngine";
import { runIntelligenceLoop } from "@/lib/intelligence/systemLoop";
import type { IntelligencePerspective } from "@/lib/intelligence/perspectiveEngine";

export function useSovereignBriefing(
  activePerspective: IntelligencePerspective = "gcc_sovereign",
): SovereignBriefing | null {
  const systemState = useSystemState();
  const ccStore = useCommandCenterStore();

  return useMemo(() => {
    // ── Path A: Live intelligence from system state ──
    if (
      systemState.status !== "idle" &&
      systemState.activeScenarioId &&
      systemState.intelligence.scenarioId !== ""
    ) {
      return generateSovereignBriefing(
        systemState.intelligence,
        activePerspective,
      );
    }

    // ── Path B: Bridge from command center data ──
    if (ccStore.status === "ready" && ccStore.scenario) {
      const scenarioId = ccStore.scenario.templateId;
      const horizonHours = ccStore.scenario.horizonHours || 168;
      const severity = ccStore.scenario.severity || 0.72;

      // Derive elapsed hours: use propagation depth as proxy for simulation progress
      // At severity 0.72 and depth 5, we're roughly at t=0.4 (cascading phase)
      const depth = ccStore.headline?.propagationDepth ?? 3;
      const t = Math.min(0.95, severity * 0.4 + depth * 0.08);
      const elapsedHours = Math.round(t * horizonHours);

      // Build decisions from command center decision actions
      const decisions = ccStore.decisionActions.map((a) => ({
        action: a.action,
        owner: a.owner ?? "Unassigned",
        deadline: `${(a as unknown as Record<string, unknown>).time_to_act_hours ?? 24}h`,
        sector: a.sector ?? "cross-sector",
      }));

      const snapshot = runIntelligenceLoop(
        scenarioId,
        elapsedHours,
        horizonHours,
        severity,
        decisions,
      );

      return generateSovereignBriefing(snapshot, activePerspective);
    }

    return null;
  }, [
    systemState.status,
    systemState.activeScenarioId,
    systemState.intelligence,
    ccStore.status,
    ccStore.scenario,
    ccStore.headline,
    ccStore.decisionActions,
    activePerspective,
  ]);
}
