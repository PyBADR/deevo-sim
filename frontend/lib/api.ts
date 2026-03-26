import type { Entity } from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  health: () => apiFetch<{ status: string }>('/api/health'),
  parseScenario: (data: { raw_text: string; title?: string; country?: string; category?: string }) =>
    apiFetch('/api/scenario/parse', { method: 'POST', body: JSON.stringify(data) }),
  buildGraph: (data: { scenario_id: string; entities: Entity[] }) =>
    apiFetch('/api/graph/build', { method: 'POST', body: JSON.stringify(data) }),
  generateAgents: (data: { scenario_id: string }) =>
    apiFetch('/api/agents/generate', { method: 'POST', body: JSON.stringify(data) }),
  runSimulation: (data: { scenario_id: string }) =>
    apiFetch('/api/simulation/run', { method: 'POST', body: JSON.stringify(data) }),
  askChat: (data: { question: string; scenario_id: string }) =>
    apiFetch('/api/chat/ask', { method: 'POST', body: JSON.stringify(data) }),
}
