const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Scenario API endpoints
export async function fetchScenarios() {
  const response = await fetch(`${API_BASE_URL}/api/scenarios`);
  if (!response.ok) {
    throw new Error(`Failed to fetch scenarios: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchScenarioById(id: string) {
  const response = await fetch(`${API_BASE_URL}/api/scenarios/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch scenario: ${response.statusText}`);
  }
  return response.json();
}

export async function runScenario(
  scenarioId: string,
  severity: number,
  options?: Record<string, unknown>
) {
  const response = await fetch(`${API_BASE_URL}/api/scenarios/${scenarioId}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      severity,
      ...options,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to run scenario: ${response.statusText}`);
  }
  return response.json();
}

export async function getScenarioResult(runId: string) {
  const response = await fetch(`${API_BASE_URL}/api/scenarios/results/${runId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch scenario result: ${response.statusText}`);
  }
  return response.json();
}

// Entity API endpoints
export async function fetchEntities() {
  const response = await fetch(`${API_BASE_URL}/api/entities`);
  if (!response.ok) {
    throw new Error(`Failed to fetch entities: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEntityById(id: string) {
  const response = await fetch(`${API_BASE_URL}/api/entities/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch entity: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEntitiesByType(type: string) {
  const response = await fetch(`${API_BASE_URL}/api/entities?type=${type}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch entities by type: ${response.statusText}`);
  }
  return response.json();
}

// Risk and Analytics API endpoints
export async function fetchRiskAnalysis() {
  const response = await fetch(`${API_BASE_URL}/api/risk-analysis`);
  if (!response.ok) {
    throw new Error(`Failed to fetch risk analysis: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEntityRiskScore(entityId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/risk-analysis/entity/${entityId}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch entity risk score: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchHeatmapData() {
  const response = await fetch(`${API_BASE_URL}/api/analytics/heatmap`);
  if (!response.ok) {
    throw new Error(`Failed to fetch heatmap data: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchFlowData() {
  const response = await fetch(`${API_BASE_URL}/api/analytics/flows`);
  if (!response.ok) {
    throw new Error(`Failed to fetch flow data: ${response.statusText}`);
  }
  return response.json();
}

// System health and status API endpoints
export async function fetchSystemHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`Failed to fetch system health: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchGCCMetrics() {
  const response = await fetch(`${API_BASE_URL}/api/gcc-metrics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch GCC metrics: ${response.statusText}`);
  }
  return response.json();
}

// Events API endpoints
export async function fetchEvents(filters?: {
  entityId?: string;
  startTime?: string;
  endTime?: string;
  severity?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.entityId) params.append("entity_id", filters.entityId);
  if (filters?.startTime) params.append("start_time", filters.startTime);
  if (filters?.endTime) params.append("end_time", filters.endTime);
  if (filters?.severity) params.append("severity", filters.severity);

  const response = await fetch(`${API_BASE_URL}/api/events?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch events: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEventById(id: string) {
  const response = await fetch(`${API_BASE_URL}/api/events/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch event: ${response.statusText}`);
  }
  return response.json();
}

// Cascade analysis API endpoints
export async function fetchCascadeAnalysis(startEntityId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/cascade-analysis/${startEntityId}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch cascade analysis: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchExplanation(scenarioRunId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/explanations/${scenarioRunId}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch explanation: ${response.statusText}`);
  }
  return response.json();
}

// Timeline API endpoints
export async function fetchTimelineData(
  startTime: string,
  endTime: string,
  entityId?: string
) {
  const params = new URLSearchParams();
  params.append("start_time", startTime);
  params.append("end_time", endTime);
  if (entityId) params.append("entity_id", entityId);

  const response = await fetch(
    `${API_BASE_URL}/api/timeline?${params.toString()}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch timeline data: ${response.statusText}`);
  }
  return response.json();
}

// GCC Layer data API endpoints
export async function fetchGCCLayerData(layer: string) {
  const response = await fetch(`${API_BASE_URL}/api/gcc-layers/${layer}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch GCC layer data: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchGCCLayerById(layer: string, id: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/gcc-layers/${layer}/${id}`
  );
  if (!response.ok) {
    throw new Error(
      `Failed to fetch GCC layer item: ${response.statusText}`
    );
  }
  return response.json();
}

// Data source information
export async function fetchDataSources() {
  const response = await fetch(`${API_BASE_URL}/api/data-sources`);
  if (!response.ok) {
    throw new Error(`Failed to fetch data sources: ${response.statusText}`);
  }
  return response.json();
}

// Abort and cancel utilities
export function createAbortController() {
  return new AbortController();
}

export function getRequestConfig(signal?: AbortSignal) {
  const config: RequestInit = {};
  if (signal) {
    config.signal = signal;
  }
  return config;
}
