import { NextRequest, NextResponse } from 'next/server'
import { authenticateRequest, getEnvironment } from '@/lib/server/auth'
import { enforcePermission } from '@/lib/server/rbac'
import { createAuditEntry } from '@/lib/server/audit'
import { generateTraceId } from '@/lib/server/trace'
import { executeScenario } from '@/lib/server/execution'

export const dynamic = 'force-dynamic'

/**
 * POST /api/run-decision
 * Runs full scenario + decision pipeline, returns decision-focused output.
 * Same execution as /run-scenario but response shape optimized for decision consumers.
 */
export async function POST(req: NextRequest) {
  const startTime = Date.now()
  const auth = authenticateRequest(req)

  if (!auth.authenticated) {
    return NextResponse.json(
      { error: 'Authentication required', code: 'AUTH_REQUIRED' },
      { status: 401 }
    )
  }

  const denied = enforcePermission(auth.role, 'run_decisions')
  if (denied) {
    createAuditEntry({
      traceId: generateTraceId(),
      runId: '',
      tenantId: auth.tenantId,
      userId: auth.userId,
      action: 'run_decision_denied',
      endpoint: '/api/run-decision',
      method: 'POST',
      inputs: {},
      status: 'forbidden',
      statusCode: 403,
      durationMs: Date.now() - startTime,
    })
    return NextResponse.json({ error: denied, code: 'FORBIDDEN' }, { status: 403 })
  }

  let body: { scenarioId?: string; severity?: number }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body', code: 'INVALID_INPUT' }, { status: 400 })
  }

  if (!body.scenarioId) {
    return NextResponse.json({ error: 'scenarioId is required', code: 'INVALID_INPUT' }, { status: 400 })
  }

  const severity = typeof body.severity === 'number' ? Math.min(1, Math.max(0, body.severity)) : 0.5

  try {
    const result = executeScenario(
      { scenarioId: body.scenarioId, severity },
      auth,
      getEnvironment(),
    )

    // Return decision-focused shape
    return NextResponse.json({
      runId: result.runId,
      traceId: result.traceId,
      auditId: result.auditId,
      scenarioId: result.scenarioId,
      scenarioLabel: result.scenarioLabel,
      severity,
      decision: result.decision,
      metrics: result.metrics,
      model: result.model,
      timestamp: result.timestamp,
      durationMs: result.durationMs,
    })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message, code: 'EXECUTION_ERROR' }, { status: 500 })
  }
}
