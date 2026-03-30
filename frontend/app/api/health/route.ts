import { NextResponse } from 'next/server'
import { getEnvironment } from '@/lib/server/auth'
import { getAuditLogSize, verifyAuditChain } from '@/lib/server/audit'
import { runStore } from '@/lib/server/store'

export const dynamic = 'force-dynamic'

export async function GET() {
  const env = getEnvironment()
  const chainIntegrity = verifyAuditChain()

  return NextResponse.json({
    status: 'healthy',
    service: 'dvo7-sim',
    environment: env,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    store: {
      runsCount: runStore.count(),
      auditEntriesCount: getAuditLogSize(),
      auditChainValid: chainIntegrity.valid,
    },
    runtime: {
      platform: 'vercel-serverless',
      nodeVersion: process.version,
      persistence: 'in-memory (pilot)',
      persistenceNote: 'Ephemeral across cold starts. Production: Vercel Postgres.',
    },
  })
}
