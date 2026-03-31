import { NextResponse } from 'next/server'
import { MODEL_VERSION, ENGINE_VERSION, GRAPH_VERSION } from '@/lib/server/execution'
import { getEnvironment } from '@/lib/server/auth'
import { gccNodes, gccEdges, gccScenarios } from '@/lib/gcc-graph'

export const dynamic = 'force-dynamic'

export async function GET() {
  return NextResponse.json({
    service: 'decision-core',
    versions: {
      model: MODEL_VERSION,
      engine: ENGINE_VERSION,
      graph: GRAPH_VERSION,
      api: '1.0.0',
    },
    graph: {
      nodes: gccNodes.length,
      edges: gccEdges.length,
      scenarios: gccScenarios.length,
      layers: ['geography', 'infrastructure', 'economy', 'finance', 'society'],
    },
    capabilities: {
      propagation: true,
      scenarioEngines: true,
      decisionIntelligence: true,
      monteCarlo: true,
      bilingual: true,
      persistence: 'in-memory',
      auth: 'api-key',
      rbac: true,
      auditTrail: true,
    },
    environment: getEnvironment(),
    timestamp: new Date().toISOString(),
  })
}
