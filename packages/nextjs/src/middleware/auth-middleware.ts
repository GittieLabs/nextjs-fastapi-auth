/**
 * Next.js middleware utilities for authentication and subdomain routing
 *
 * Provides middleware factory functions for:
 * - Route protection (authentication required)
 * - Admin route protection
 * - Subdomain parsing and routing
 * - Organization context injection
 *
 * @packageDocumentation
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { createServerClient } from '@supabase/ssr'
import type { AuthConfig } from '../types'

export interface MiddlewareConfig {
  /** Supabase configuration */
  supabase: {
    url: string
    anonKey: string
  }
  /** Main domain for subdomain detection (e.g., 'govreadyai.app') */
  mainDomain?: string
  /** Routes that require authentication */
  protectedRoutes?: string[]
  /** Routes that are publicly accessible */
  publicRoutes?: string[]
  /** Routes that require admin access */
  adminRoutes?: string[]
  /** Marketing routes (only available on main domain) */
  marketingRoutes?: string[]
  /** API subdomain (e.g., 'api') */
  apiSubdomain?: string
  /** Enable debug logging */
  debug?: boolean
  /** Custom auth check function */
  checkAuthMode?: (req: NextRequest) => Promise<boolean>
}

export interface SubdomainInfo {
  /** Extracted subdomain (null if on main domain) */
  subdomain: string | null
  /** Whether request is on main domain */
  isMainDomain: boolean
}

/**
 * Parse subdomain from request host
 *
 * Handles both production domains and localhost development with subdomain.localhost pattern.
 *
 * @param host - Request host header
 * @param mainDomain - Main production domain (e.g., 'govreadyai.app')
 * @returns Subdomain information
 *
 * @example
 * ```typescript
 * parseSubdomain('ktg.localhost:3000', 'govreadyai.app')
 * // => { subdomain: 'ktg', isMainDomain: false }
 *
 * parseSubdomain('govreadyai.app', 'govreadyai.app')
 * // => { subdomain: null, isMainDomain: true }
 *
 * parseSubdomain('ktg.govreadyai.app', 'govreadyai.app')
 * // => { subdomain: 'ktg', isMainDomain: false }
 * ```
 */
export function parseSubdomain(host: string, mainDomain?: string): SubdomainInfo {
  if (!host) return { subdomain: null, isMainDomain: true }

  // Handle localhost development
  if (host.includes('localhost') || host.includes('127.0.0.1')) {
    // Check for subdomain in localhost (e.g., ktg.localhost:3000)
    if (host.includes('.localhost')) {
      const parts = host.split(':')[0].split('.') // Remove port, then split by dots
      if (parts.length >= 2 && parts[parts.length - 1] === 'localhost') {
        const subdomain = parts[0]
        return { subdomain, isMainDomain: false }
      }
    }
    // Plain localhost without subdomain
    return { subdomain: null, isMainDomain: true }
  }

  if (!mainDomain) {
    return { subdomain: null, isMainDomain: true }
  }

  const parts = host.split('.')

  // For production domain, we need at least 3 parts (subdomain.example.com)
  if (parts.length >= 3 && host.endsWith(mainDomain)) {
    const subdomain = parts[0]
    // Treat www as main domain, not a subdomain
    if (subdomain === 'www') {
      return { subdomain: null, isMainDomain: true }
    }
    return { subdomain, isMainDomain: false }
  }

  // If it's exactly the main domain (2 parts), it's the main domain
  if (parts.length === 2 && host === mainDomain) {
    return { subdomain: null, isMainDomain: true }
  }

  return { subdomain: null, isMainDomain: true }
}

/**
 * Create authenticated Supabase client for middleware
 *
 * @param req - Next.js request
 * @param res - Next.js response
 * @param config - Supabase configuration
 * @returns Supabase server client
 */
export function createMiddlewareSupabaseClient(
  req: NextRequest,
  res: NextResponse,
  config: { url: string; anonKey: string }
) {
  return createServerClient(config.url, config.anonKey, {
    cookies: {
      get(name: string) {
        return req.cookies.get(name)?.value
      },
      set(name: string, value: string, options: any) {
        res.cookies.set({
          name,
          value,
          ...options,
        })
      },
      remove(name: string, options: any) {
        res.cookies.set({
          name,
          value: '',
          ...options,
        })
      },
    },
  })
}

/**
 * Check if route matches any pattern
 *
 * @param pathname - Request pathname
 * @param patterns - Array of route patterns
 * @returns True if pathname starts with any pattern
 */
export function matchesRoute(pathname: string, patterns: string[]): boolean {
  return patterns.some(pattern => pathname.startsWith(pattern))
}

/**
 * Handle subdomain routing logic
 *
 * Rewrites requests to subdomain-specific routes and adds organization headers.
 *
 * @param req - Next.js request
 * @param subdomain - Detected subdomain
 * @param config - Middleware configuration
 * @returns NextResponse with subdomain routing
 */
export function handleSubdomainRouting(
  req: NextRequest,
  subdomain: string,
  config: MiddlewareConfig
): NextResponse | null {
  const pathname = req.nextUrl.pathname

  if (config.debug) {
    console.log('[Middleware] Detected subdomain:', subdomain, 'for path:', pathname)
  }

  // Don't rewrite API routes - pass subdomain via header
  if (pathname.startsWith('/api/')) {
    const url = req.nextUrl.clone()
    url.searchParams.set('_subdomain', subdomain)

    const response = NextResponse.rewrite(url)
    response.headers.set('x-organization-subdomain', subdomain)
    return response
  }

  // Don't rewrite public routes (except root) - they should work globally
  const publicRoutes = config.publicRoutes || []
  const nonRootPublicRoutes = publicRoutes.filter(route => route !== '/')
  if (matchesRoute(pathname, nonRootPublicRoutes)) {
    const response = NextResponse.next()
    response.headers.set('x-organization-subdomain', subdomain)
    return response
  }

  // Rewrite subdomain requests to [subdomain] dynamic route
  if (pathname === '/') {
    if (config.debug) {
      console.log(`[Middleware] Rewriting ${subdomain} root to /${subdomain}`)
    }
    const url = req.nextUrl.clone()
    url.pathname = `/${subdomain}`
    const response = NextResponse.rewrite(url)
    response.headers.set('x-organization-subdomain', subdomain)
    return response
  } else {
    // For other paths, rewrite to subdomain/path
    if (config.debug) {
      console.log(`[Middleware] Rewriting ${subdomain}${pathname} to /${subdomain}${pathname}`)
    }
    const url = req.nextUrl.clone()
    url.pathname = `/${subdomain}${pathname}`
    const response = NextResponse.rewrite(url)
    response.headers.set('x-organization-subdomain', subdomain)
    return response
  }
}

/**
 * Handle authentication and authorization logic
 *
 * @param req - Next.js request
 * @param response - NextResponse to modify
 * @param config - Middleware configuration
 * @returns Modified NextResponse or redirect
 */
export async function handleAuthentication(
  req: NextRequest,
  response: NextResponse,
  config: MiddlewareConfig
): Promise<NextResponse> {
  const pathname = req.nextUrl.pathname

  // Always allow public routes
  const publicRoutes = config.publicRoutes || []
  if (matchesRoute(pathname, publicRoutes)) {
    return response
  }

  // Check if authentication is required
  let authRequired = true
  if (config.checkAuthMode) {
    authRequired = await config.checkAuthMode(req)
  }

  // If authentication is not required, allow all routes
  if (!authRequired) {
    return response
  }

  try {
    // Create Supabase client
    const supabase = createMiddlewareSupabaseClient(req, response, config.supabase)

    // Refresh session if expired
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession()

    // Check if route requires authentication
    const protectedRoutes = config.protectedRoutes || []
    const isProtectedRoute = matchesRoute(pathname, protectedRoutes)

    if (isProtectedRoute && (!session || error)) {
      // Redirect to login if trying to access protected route without auth
      const redirectUrl = new URL('/auth/login', req.url)
      redirectUrl.searchParams.set('redirectTo', pathname)
      return NextResponse.redirect(redirectUrl)
    }

    // Check admin routes
    const adminRoutes = config.adminRoutes || []
    const isAdminRoute = matchesRoute(pathname, adminRoutes)
    if (isAdminRoute && session) {
      // TODO: Add proper role checking from JWT payload
      // For now, allow all authenticated users
      return response
    }

    return response
  } catch (error) {
    console.error('[Middleware] Authentication error:', error)
    // On error, allow the request to continue
    return response
  }
}

/**
 * Create authentication middleware
 *
 * Factory function that creates a Next.js middleware with authentication,
 * subdomain routing, and organization context.
 *
 * @param config - Middleware configuration
 * @returns Next.js middleware function
 *
 * @example
 * ```typescript
 * // middleware.ts
 * import { createAuthMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'
 *
 * export default createAuthMiddleware({
 *   supabase: {
 *     url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
 *     anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
 *   },
 *   mainDomain: 'govreadyai.app',
 *   protectedRoutes: ['/admin', '/dashboard'],
 *   publicRoutes: ['/', '/auth/login', '/auth/signup'],
 *   adminRoutes: ['/admin'],
 *   debug: process.env.NODE_ENV === 'development',
 * })
 *
 * export const config = {
 *   matcher: [
 *     '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
 *   ],
 * }
 * ```
 */
export function createAuthMiddleware(config: MiddlewareConfig) {
  return async function middleware(req: NextRequest) {
    const pathname = req.nextUrl.pathname
    const host = req.headers.get('host') || ''

    const mainDomain = config.mainDomain || ''
    const apiSubdomain = config.apiSubdomain || 'api'

    // Redirect www to non-www domain
    if (host.startsWith('www.') && mainDomain && host.includes(mainDomain)) {
      const redirectUrl = new URL(req.url)
      redirectUrl.hostname = mainDomain
      return NextResponse.redirect(redirectUrl, 301)
    }

    // Parse subdomain information
    const { subdomain, isMainDomain } = parseSubdomain(host, mainDomain)

    // Handle API subdomain
    if (subdomain === apiSubdomain) {
      return NextResponse.json({ error: 'API endpoint not found' }, { status: 404 })
    }

    // Handle marketing routes - only allowed on main domain
    const marketingRoutes = config.marketingRoutes || []
    if (matchesRoute(pathname, marketingRoutes)) {
      if (!isMainDomain && subdomain && mainDomain) {
        // Redirect marketing routes from subdomains to main domain
        const redirectUrl = new URL(req.url)
        redirectUrl.hostname = mainDomain
        return NextResponse.redirect(redirectUrl)
      }
      return NextResponse.next()
    }

    // Handle client application routes on subdomains
    if (subdomain && !isMainDomain && subdomain !== apiSubdomain) {
      const response = handleSubdomainRouting(req, subdomain, config)
      if (response) {
        return handleAuthentication(req, response, config)
      }
    }

    // Handle main domain routes
    if (isMainDomain) {
      const publicRoutes = config.publicRoutes || []
      // Allow marketing routes and public routes on main domain
      if (matchesRoute(pathname, [...publicRoutes, ...marketingRoutes])) {
        return NextResponse.next()
      }

      // Handle protected routes
      const protectedRoutes = config.protectedRoutes || []
      if (matchesRoute(pathname, protectedRoutes)) {
        return handleAuthentication(req, NextResponse.next(), config)
      }

      // For any other routes on main domain, just allow them
      return NextResponse.next()
    }

    // Always allow Next.js internal API routes
    if (pathname.startsWith('/api/') && !pathname.startsWith('/api/v1/')) {
      return NextResponse.next()
    }

    // Apply authentication to all other routes
    return handleAuthentication(req, NextResponse.next(), config)
  }
}

/**
 * Default middleware matcher configuration
 *
 * Excludes Next.js internal routes and static files.
 */
export const defaultMatcher = [
  '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
]
