"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ============================================================================
// Impact Observatory v4 Hooks — Maps to /api/v1/runs/* endpoints
// ============================================================================

/**
 * Launch a pipeline run against a scenario or template.
 * POST /api/v1/runs → 202
 */
export function useObservatoryRun(
  onSuccess?: (data: Record<string, unknown>) => void,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { scenario_id?: string; template_id?: string }) =>
      api.observatory.run(params),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["observatory"] });
      onSuccess?.(data.data as Record<string, unknown>);
    },
  });
}

/**
 * Poll run status.
 * GET /api/v1/runs/{id}/status
 */
export function useRunStatus(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "status", runId],
    queryFn: () => api.observatory.status(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.data?.status;
      return status === "completed" || status === "failed" ? false : 2000;
    },
  });
}

/**
 * Financial impacts.
 * GET /api/v1/runs/{id}/financial
 */
export function useFinancial(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "financial", runId],
    queryFn: () => api.observatory.financial(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Banking stress.
 * GET /api/v1/runs/{id}/banking
 */
export function useBanking(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "banking", runId],
    queryFn: () => api.observatory.banking(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Insurance stress.
 * GET /api/v1/runs/{id}/insurance
 */
export function useInsurance(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "insurance", runId],
    queryFn: () => api.observatory.insurance(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fintech stress.
 * GET /api/v1/runs/{id}/fintech
 */
export function useFintech(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "fintech", runId],
    queryFn: () => api.observatory.fintech(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Decision plan (top-3 actions).
 * GET /api/v1/runs/{id}/decision
 */
export function useDecision(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "decision", runId],
    queryFn: () => api.observatory.decision(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Explanation pack.
 * GET /api/v1/runs/{id}/explanation
 */
export function useExplanation(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "explanation", runId],
    queryFn: () => api.observatory.explanation(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Business impact summary.
 * GET /api/v1/runs/{id}/business-impact
 */
export function useBusinessImpact(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "business-impact", runId],
    queryFn: () => api.observatory.businessImpact(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Temporal simulation timeline.
 * GET /api/v1/runs/{id}/timeline
 */
export function useTimeline(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "timeline", runId],
    queryFn: () => api.observatory.timeline(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Regulatory breach timeline.
 * GET /api/v1/runs/{id}/regulatory-timeline
 */
export function useRegulatoryTimeline(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "regulatory-timeline", runId],
    queryFn: () => api.observatory.regulatoryTimeline(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Executive narrative explanation.
 * GET /api/v1/runs/{id}/executive-explanation
 */
export function useExecutiveExplanation(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "executive-explanation", runId],
    queryFn: () => api.observatory.executiveExplanation(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}
