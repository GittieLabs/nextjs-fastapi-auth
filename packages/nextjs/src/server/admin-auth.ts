/**
 * Server-side admin authentication utilities for Next.js API routes
 *
 * Provides utilities for validating admin access in API routes and
 * proxying requests to the backend with authentication.
 */

import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { extractJwtPayload, isAdminToken } from '../jwt/extractor'

export interface AdminAuthResult {
  token: string
  error?: never
}

export interface AdminAuthError {
  token?: never
  error: NextResponse
}

export type AdminAuthValidation = AdminAuthResult | AdminAuthError

/**
 * Validate that request has valid admin authorization
 *
 * Checks for Bearer token and validates admin role in JWT payload.
 * Note: This is frontend validation only - backend must also validate.
 *
 * @param request - Next.js request object
 * @returns Token if valid, or NextResponse error
 *
 * @example
 * ```typescript
 * export async function GET(request: NextRequest) {
 *   const auth = validateAdminAuth(request)
 *   if (auth.error) return auth.error
 *
 *   // Use auth.token to proxy to backend
 *   const response = await proxyToBackend(url, 'GET', auth.token)
 *   return NextResponse.json(await response.json())
 * }
 * ```
 */
export function validateAdminAuth(request: NextRequest): AdminAuthValidation {
  const authorization = request.headers.get('authorization')

  // Check if authorization header exists
  if (!authorization || !authorization.startsWith('Bearer ')) {
    console.log('[Admin Auth] No authorization header found')
    return {
      error: NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }
  }

  // Extract token
  const token = authorization.substring(7)

  // Check if token is a valid JWT (3 parts separated by dots)
  const parts = token.split('.')
  if (parts.length !== 3) {
    console.log('[Admin Auth] Invalid JWT format')
    return {
      error: NextResponse.json(
        { error: 'Invalid token format' },
        { status: 401 }
      )
    }
  }

  // Check if token claims admin role (basic frontend check)
  // Note: Backend will do full validation including signature verification
  if (!isAdminToken(token)) {
    console.log('[Admin Auth] Token does not have admin role')
    return {
      error: NextResponse.json(
        { error: 'Admin access required. You do not have permission to access this resource.' },
        { status: 403 }
      )
    }
  }

  console.log('[Admin Auth] Authorization validated, forwarding to backend')
  return { token }
}

/**
 * Proxy request to backend API with authentication
 *
 * @param url - Backend API URL
 * @param method - HTTP method
 * @param authorization - JWT token (without "Bearer " prefix)
 * @param body - Optional request body
 * @returns Backend response
 *
 * @example
 * ```typescript
 * const response = await proxyToBackend(
 *   'http://localhost:8000/api/v1/admin/users',
 *   'GET',
 *   token
 * )
 * ```
 */
export async function proxyToBackend(
  url: string,
  method: string,
  authorization: string,
  body?: string
): Promise<Response> {
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authorization}`,
  }

  const options: RequestInit = {
    method,
    headers,
  }

  if (body && ['POST', 'PUT', 'PATCH'].includes(method)) {
    options.body = body
  }

  return fetch(url, options)
}

/**
 * Get backend JWT token from Supabase token
 *
 * Exchanges a Supabase JWT for a backend JWT token.
 *
 * @param supabaseToken - Supabase JWT token
 * @param backendUrl - Backend API base URL
 * @returns Backend JWT token or null
 */
export async function getBackendJwtToken(
  supabaseToken: string,
  backendUrl: string
): Promise<string | null> {
  try {
    const response = await fetch(`${backendUrl}/api/v1/auth/jwt-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseToken}`,
      },
      body: JSON.stringify({
        supabase_jwt: supabaseToken,
        expiry_minutes: 60
      }),
    })

    if (response.ok) {
      const data = await response.json()
      return data.token
    }

    console.error('[Admin Auth] Failed to get backend JWT:', response.status)
    return null
  } catch (error) {
    console.error('[Admin Auth] Error getting backend JWT:', error)
    return null
  }
}

/**
 * Get Supabase session from server-side
 *
 * @param supabaseUrl - Supabase project URL
 * @param supabaseKey - Supabase anon key
 * @returns Supabase session or null
 */
export async function getSupabaseSession(
  supabaseUrl: string,
  supabaseKey: string
) {
  const cookieStore = await cookies()

  const supabase = createServerClient(
    supabaseUrl,
    supabaseKey,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    }
  )

  try {
    const { data: { session }, error } = await supabase.auth.getSession()
    if (error) {
      console.error('[Admin Auth] Error getting session:', error)
      return null
    }
    return session
  } catch (error) {
    console.error('[Admin Auth] Failed to get session:', error)
    return null
  }
}

/**
 * Get admin backend JWT from current session
 *
 * @param config - Configuration with Supabase and backend URLs
 * @returns Backend JWT token or null
 */
export async function getAdminBackendJwt(config: {
  supabaseUrl: string
  supabaseKey: string
  backendUrl: string
}): Promise<string | null> {
  const session = await getSupabaseSession(config.supabaseUrl, config.supabaseKey)
  if (!session?.access_token) {
    console.log('[Admin Auth] No Supabase session found')
    return null
  }

  console.log('[Admin Auth] Found Supabase session, getting backend JWT')
  return await getBackendJwtToken(session.access_token, config.backendUrl)
}

/**
 * Create authenticated headers for server-side API calls
 *
 * @param request - Next.js request object
 * @param includeSubdomain - Whether to include subdomain header
 * @returns Headers with authentication
 */
export function createAuthenticatedHeaders(
  request: NextRequest,
  includeSubdomain: boolean = true
): HeadersInit {
  const headers: HeadersInit = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  }

  // Add subdomain header for organization context
  if (includeSubdomain) {
    const host = request.headers.get('host') || ''
    if (host.includes('.localhost') || host.includes('.govreadyai.app')) {
      const subdomain = host.split('.')[0]
      if (subdomain && subdomain !== 'www' && subdomain !== 'localhost') {
        headers['x-organization-subdomain'] = subdomain
        console.log('[API Auth] Including subdomain header:', subdomain)
      }
    }
  }

  // Get authorization from request
  const authorization = request.headers.get('authorization')
  if (authorization) {
    headers['Authorization'] = authorization
    console.log('[API Auth] Using Authorization header from request')
  }

  return headers
}

/**
 * Check if request is from authenticated user
 *
 * @param request - Next.js request object
 * @returns True if request has valid authorization header
 */
export function isAuthenticated(request: NextRequest): boolean {
  const authorization = request.headers.get('authorization')
  if (!authorization || !authorization.startsWith('Bearer ')) {
    return false
  }

  const token = authorization.substring(7)
  const parts = token.split('.')
  return parts.length === 3
}

/**
 * Check if request is from admin user
 *
 * @param request - Next.js request object
 * @returns True if request has valid admin authorization
 */
export function isAdminAuthenticated(request: NextRequest): boolean {
  if (!isAuthenticated(request)) {
    return false
  }

  const authorization = request.headers.get('authorization')!
  const token = authorization.substring(7)

  return isAdminToken(token)
}
