import { NextRequest, NextResponse } from 'next/server'
import { authenticateRequest } from '@/lib/server/auth'
import { enforcePermission } from '@/lib/server/rbac'
import { runStore } from '@/lib/server/store'

export const dynamic = 'force-dynamic'

/** GET /api/runs — list runs for authenticated tenant */
export async function GET(req: NextRequest) {
  const auth = authenticateRequest(req)

  if (!auth.authenticated) {
    return NextResponse.json(
      { error: 'Authentication required', code: 'AUTH_REQUIRED' },
      { status: 401 }
    )
  }

  const denied = enforcePermission(auth.role, 'read_runs')
  if (denied) {
    return NextResponse.json({ error: denied, code: 'FORBIDDEN' }, { status: 403 })
  }

  const limit = parseInt(req.nextUrl.searchParams.get('limit') || '50', 10)
  const runs = auth.role === 'admin'
    ? runStore.getByTenant(auth.tenantId, limit)
    : runStore.getByTenant(auth.tenantId, limit)

  // Return summary, not full runs
  const summaries = runs.map(r => ({
    runId: r.runId,
    traceId: r.traceId,
    scenarioId: r.scenarioId,
    scenarioLabel: r.scenarioLabel,
    severity: r.severity,
    totalLoss: r.totalLoss,
    totalExposure: r.totalExposure,
    urgencyLevel: r.urgencyLevel,
    decisionConfidence: r.decisionConfidence,
    status: r.status,
    timestamp: r.timestamp,
    durationMs: r.durationMs,
    _links: {
      detail: `/api/runs/${r.runId}`,
      audit: `/api/audit/${r.auditId}`,
    },
  }))

  return NextResponse.json({
    runs: summaries,
    total: summaries.length,
    tenantId: auth.tenantId,
    timestamp: new Date().toISOString(),
  })
}
