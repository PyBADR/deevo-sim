import { NextRequest, NextResponse } from 'next/server'
import { authenticateRequest } from '@/lib/server/auth'
import { enforcePermission } from '@/lib/server/rbac'
import { runStore } from '@/lib/server/store'

export const dynamic = 'force-dynamic'

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
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

  const run = runStore.get(params.id)

  if (!run) {
    return NextResponse.json(
      { error: `Run not found: ${params.id}`, code: 'NOT_FOUND' },
      { status: 404 }
    )
  }

  // Tenant isolation: users can only see their tenant's runs
  if (auth.role !== 'admin' && run.tenantId !== auth.tenantId) {
    return NextResponse.json(
      { error: 'Run not found', code: 'NOT_FOUND' },
      { status: 404 }
    )
  }

  return NextResponse.json({
    run,
    _links: {
      self: `/api/runs/${run.runId}`,
      audit: `/api/audit/${run.auditId}`,
    },
  })
}
