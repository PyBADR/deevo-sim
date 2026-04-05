"use client";

import { useState, useCallback } from "react";
import { graphClient } from "@/lib/graph-client";
import { api } from "@/lib/api";
import { useRunState } from "@/lib/run-state";
import type {
  ImpactedEntity,
  UnifiedRunResult,
  DecisionActionV2,
  SectorRollup,
  GraphScenarioTemplate,
} from "@/types/observatory";

export interface GlobeState {
  entities: ImpactedEntity[];
  runResult: UnifiedRunResult | null;
  scenarios: GraphScenarioTemplate[];
  loading: boolean;
  scenariosLoading: boolean;
  error: string | null;
}

export function useGlobeEntities() {
  const [state, setState] = useState<GlobeState>({
    entities: [],
    runResult: null,
    scenarios: [],
    loading: false,
    scenariosLoading: false,
    error: null,
  });

  // Load available scenarios
  const loadScenarios = useCallback(async () => {
    setState((s) => ({ ...s, scenariosLoading: true }));
    try {
      const res = await graphClient.scenarios();
      setState((s) => ({ ...s, scenarios: res.scenarios, scenariosLoading: false }));
    } catch (err) {
      setState((s) => ({
        ...s,
        scenariosLoading: false,
        error: err instanceof Error ? err.message : "Failed to load scenarios",
      }));
    }
  }, []);

  // Run unified pipeline via canonical POST /runs → GET /runs/{id}
  const runScenario = useCallback(
    async (templateId: string, severity = 0.7, horizonHours = 168) => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        // 1. POST /runs → 202 Accepted with run_meta
        const runRes = await api.observatory.run({
          template_id: templateId,
          severity,
          horizon_hours: horizonHours,
        });
        const runId = (runRes.data as any).run_id as string;

        // 2. GET /runs/{id} → Full UnifiedRunResult
        const resultRes = await api.observatory.result(runId);
        const result = resultRes.data as unknown as UnifiedRunResult;

        setState((s) => ({
          ...s,
          runResult: result,
          entities: result.map_payload?.impacted_entities ?? [],
          loading: false,
        }));
        // Store in shared state for cross-page sync (Dashboard, etc.)
        useRunState.getState().setUnifiedResult(result);
        return result;
      } catch (err) {
        setState((s) => ({
          ...s,
          loading: false,
          error: err instanceof Error ? err.message : "Pipeline run failed",
        }));
        return null;
      }
    },
    []
  );

  const clearRun = useCallback(() => {
    setState((s) => ({ ...s, entities: [], runResult: null }));
  }, []);

  return { ...state, loadScenarios, runScenario, clearRun };
}
