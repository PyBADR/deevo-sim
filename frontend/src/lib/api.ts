import type {
  EventsResponse,
  FlightsResponse,
  VesselsResponse,
  TemplatesResponse,
  ScenarioResult,
  RiskScore,
  DisruptionScore,
  SystemStress,
  InsuranceExposure,
  ClaimsSurge,
  UnderwritingWatch,
  SeverityProjection,
  DecisionOutput,
  ChokepointsResponse,
  PropagationResponse,
  GraphNode,
  GraphEdge,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // ---- Health ----
  health: () => fetchJSON<{ status: string }>("/health"),

  // ---- Events ----
  events: (params?: { limit?: number; severity_min?: number; event_type?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.severity_min) qs.set("severity_min", String(params.severity_min));
    if (params?.event_type) qs.set("event_type", params.event_type);
    return fetchJSON<EventsResponse>(`/events?${qs}`);
  },

  // ---- Flights ----
  flights: (params?: { limit?: number; status?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.status) qs.set("status", params.status);
    return fetchJSON<FlightsResponse>(`/flights?${qs}`);
  },

  // ---- Vessels ----
  vessels: (params?: { limit?: number; vessel_type?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.vessel_type) qs.set("vessel_type", params.vessel_type);
    return fetchJSON<VesselsResponse>(`/vessels?${qs}`);
  },

  // ---- Threat Field ----
  threatField: (lat: number, lng: number) =>
    fetchJSON<{ threat_intensity: number; top_contributors: { id: string; contribution: number }[] }>(
      `/events/threat-field?lat=${lat}&lng=${lng}`
    ),

  // ---- Scoring ----
  riskScore: (body: Record<string, number>) =>
    fetchJSON<RiskScore>("/scores/risk", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  riskScores: (params?: { sector?: string; region?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.sector) qs.set("sector", params.sector);
    if (params?.region) qs.set("region", params.region);
    if (params?.limit) qs.set("limit", String(params.limit));
    return fetchJSON<{ scores: RiskScore[] }>(`/scores/risk?${qs}`);
  },

  disruptionScore: (body: Record<string, number>) =>
    fetchJSON<DisruptionScore>("/scores/disruption", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  confidenceScore: (params: Record<string, number | string>) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    );
    return fetchJSON<{ score: number; factors: { name: string; value: number }[] }>(
      `/scores/confidence?${qs}`
    );
  },

  // ---- System Stress ----
  systemStress: () => fetchJSON<SystemStress>("/system/stress"),

  // ---- Scenarios ----
  scenarioTemplates: () =>
    fetchJSON<TemplatesResponse>("/scenario/templates"),

  scenarioRun: (body: {
    scenario_id?: string;
    severity_override?: number;
    custom_shocks?: { shock_type: string; severity: number; target_entity_id?: string }[];
    horizon_hours?: number;
  }) =>
    fetchJSON<ScenarioResult>("/scenario/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // ---- Graph ----
  graphPropagation: (startNodeId: string, maxHops?: number) => {
    const qs = new URLSearchParams({ start_node_id: startNodeId });
    if (maxHops) qs.set("max_hops", String(maxHops));
    return fetchJSON<PropagationResponse>(`/graph/propagation-path?${qs}`);
  },

  graphChokepoints: () =>
    fetchJSON<ChokepointsResponse>("/graph/chokepoints"),

  graphNodes: (params?: { sector?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.sector) qs.set("sector", params.sector);
    if (params?.limit) qs.set("limit", String(params.limit));
    return fetchJSON<{ nodes: GraphNode[]; edges: GraphEdge[] }>(`/graph/nodes?${qs}`);
  },

  // ---- Insurance ----
  insuranceExposure: (params?: { sector?: string; region?: string }) => {
    const qs = new URLSearchParams();
    if (params?.sector) qs.set("sector", params.sector);
    if (params?.region) qs.set("region", params.region);
    return fetchJSON<{ exposures: InsuranceExposure[] }>(`/insurance/exposure?${qs}`);
  },

  claimsSurge: (scenarioId: string) =>
    fetchJSON<ClaimsSurge>(`/insurance/claims-surge?scenario_id=${scenarioId}`),

  underwritingWatch: (params?: { watch_level?: string }) => {
    const qs = new URLSearchParams();
    if (params?.watch_level) qs.set("watch_level", params.watch_level);
    return fetchJSON<{ watches: UnderwritingWatch[] }>(`/insurance/underwriting?${qs}`);
  },

  severityProjection: (scenarioId: string, horizonHours?: number) => {
    const qs = new URLSearchParams({ scenario_id: scenarioId });
    if (horizonHours) qs.set("horizon_hours", String(horizonHours));
    return fetchJSON<SeverityProjection>(`/insurance/severity-projection?${qs}`);
  },

  // ---- Decision Output ----
  decisionOutput: (scenarioId: string) =>
    fetchJSON<DecisionOutput>(`/decision/output?scenario_id=${scenarioId}`),

  // ---- Entity Detail ----
  entityDetail: (entityId: string) =>
    fetchJSON<{
      id: string;
      name: string;
      name_ar?: string;
      type: string;
      sector: string;
      region: string;
      risk_score: RiskScore;
      disruption_score: DisruptionScore;
      insurance_exposure?: InsuranceExposure;
      connected_entities: { id: string; name: string; edge_type: string; weight: number }[];
    }>(`/entity/${entityId}`),

  // ================================================================
  // Impact Observatory v4 API — v4 §4 envelope: { data, trace_id, generated_at, warnings }
  // ================================================================

  observatory: {
    /** POST /api/v1/runs — Execute pipeline against a scenario/template */
    run: (body: { scenario_id?: string; template_id?: string }) =>
      fetchJSON<{ data: Record<string, unknown> }>("/api/v1/runs", {
        method: "POST",
        body: JSON.stringify(body),
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/status — Poll run status */
    status: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/status`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/financial — Financial impacts + aggregate */
    financial: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/financial`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/banking — Banking stress */
    banking: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/banking`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/insurance — Insurance stress */
    insurance: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/insurance`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/fintech — Fintech stress */
    fintech: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/fintech`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/decision — Decision plan (top-3 actions) */
    decision: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/decision`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/explanation — Explanation pack */
    explanation: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/explanation`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/business-impact — Business impact summary */
    businessImpact: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/business-impact`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/timeline — Timestep-by-timestep simulation */
    timeline: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown>[] }>(`/api/v1/runs/${runId}/timeline`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/regulatory-timeline — Regulatory breach events */
    regulatoryTimeline: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/regulatory-timeline`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),

    /** GET /api/v1/runs/{id}/executive-explanation — Executive narrative */
    executiveExplanation: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/executive-explanation`, {
        headers: { "X-IO-API-Key": "io_master_key_2026" },
      }),
  },
};
