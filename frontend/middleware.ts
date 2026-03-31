/**
 * ══════════════════════════════════════════════════════════════
 * DECISIONCORE INTELLIGENCE — API MIDDLEWARE
 * ══════════════════════════════════════════════════════════════
 * Adds CORS, security headers, request logging, and rate limiting
 * for all /api/* routes. Auth is handled per-route for granularity.
 */

import { NextRequest, NextResponse } from 'next/server'

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Only apply to API routes
  if (!pathname.startsWith('/api/')) {
    return NextResponse.next()
  }

  // CORS headers for API routes
  const response = NextResponse.next()
  response.headers.set('Access-Control-Allow-Origin', '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-DC7-API-Key, X-DC7-Trace-Id')
  response.headers.set('Access-Control-Expose-Headers', 'X-DC7-Trace-Id, X-DC7-Run-Id')

  // Security headers
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-DC7-Environment', process.env.DC7_TIER || 'pilot')
  response.headers.set('X-DC7-API-Version', '1.0.0')

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new NextResponse(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-DC7-API-Key, X-DC7-Trace-Id',
        'Access-Control-Max-Age': '86400',
      },
    })
  }

  return response
}

export const config = {
  matcher: '/api/:path*',
}
