/**
 * Client-side authenticated fetch utilities
 *
 * Provides utilities for making authenticated requests from the browser
 * with automatic Supabase token injection.
 */

'use client'

import type { SupabaseClient } from '@supabase/supabase-js'

/**
 * Configuration for authenticated fetch
 */
export interface AuthenticatedFetchConfig {
  supabase?: SupabaseClient
  subdomain?: string | null
  backendUrl?: string
  includeSubdomainHeader?: boolean
  debug?: boolean
}

let globalConfig: AuthenticatedFetchConfig = {
  includeSubdomainHeader: true,
  debug: false
}

/**
 * Configure authenticated fetch globally
 *
 * @param config - Configuration options
 */
export function configureAuthenticatedFetch(config: AuthenticatedFetchConfig) {
  globalConfig = { ...globalConfig, ...config }
}

/**
 * Get current subdomain from window.location
 *
 * @returns Subdomain or null
 */
export function getCurrentSubdomain(): string | null {
  if (typeof window === 'undefined') return null

  const host = window.location.hostname

  // Handle localhost development (e.g., ktg.localhost:3000)
  if (host.includes('.localhost')) {
    const parts = host.split('.')
    if (parts.length >= 2 && parts[parts.length - 1] === 'localhost') {
      return parts[0]
    }
  }

  // Handle production domains (e.g., ktg.govreadyai.app)
  const parts = host.split('.')
  if (parts.length >= 3) {
    const subdomain = parts[0]
    // Exclude www as a subdomain
    if (subdomain !== 'www') {
      return subdomain
    }
  }

  return null
}

/**
 * Get headers for authenticated API calls from the client side
 *
 * @param supabase - Supabase client instance
 * @param customHeaders - Additional headers to include
 * @returns Headers with authentication and organization context
 */
export async function getClientApiHeaders(
  supabase?: SupabaseClient,
  customHeaders?: HeadersInit
): Promise<HeadersInit> {
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  }

  // Add custom headers
  if (customHeaders) {
    Object.assign(headers, customHeaders)
  }

  // Use global config if not provided
  const supabaseClient = supabase || globalConfig.supabase
  const includeSubdomain = globalConfig.includeSubdomainHeader !== false
  const debug = globalConfig.debug

  // Add subdomain header for organization context
  if (includeSubdomain) {
    const subdomain = globalConfig.subdomain || getCurrentSubdomain()
    if (subdomain) {
      headers['x-organization-subdomain'] = subdomain
      if (debug) {
        console.log('[Client API] Including subdomain header:', subdomain)
      }
    }
  }

  // Try to get the current Supabase session
  if (supabaseClient) {
    try {
      if (debug) {
        console.log('[Client API] 🔍 Getting Supabase session...')
      }

      const { data: { session }, error } = await supabaseClient.auth.getSession()

      if (debug) {
        console.log('[Client API] 📊 Session check:', {
          hasSession: !!session,
          hasAccessToken: !!session?.access_token,
          userId: session?.user?.id,
          email: session?.user?.email,
          tokenLength: session?.access_token?.length,
          error: error?.message
        })
      }

      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
        if (debug) {
          console.log('[Client API] ✅ Including Supabase token in request')
          console.log('[Client API] 🔑 Token preview:', session.access_token.substring(0, 30) + '...')
        }
      } else {
        if (debug) {
          console.log('[Client API] ❌ No Supabase session found')
        }
      }
    } catch (error) {
      console.warn('[Client API] 💥 Failed to get Supabase session:', error)
    }
  } else {
    if (debug) {
      console.log('[Client API] ❌ No Supabase client available')
    }
  }

  return headers
}

/**
 * Make an authenticated API request to an internal API route
 *
 * Automatically includes Supabase JWT token and organization context.
 *
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @param supabase - Optional Supabase client (uses global if not provided)
 * @returns Fetch response
 *
 * @example
 * ```typescript
 * const response = await authenticatedFetch('/api/v1/jobs')
 * const jobs = await response.json()
 * ```
 *
 * @example
 * ```typescript
 * const response = await authenticatedFetch('/api/v1/jobs', {
 *   method: 'POST',
 *   body: JSON.stringify({ name: 'New Job' })
 * })
 * ```
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {},
  supabase?: SupabaseClient
): Promise<Response> {
  const debug = globalConfig.debug

  if (debug) {
    console.log(`[authenticatedFetch] 🚀 Making request to: ${url}`)
  }

  const headers = await getClientApiHeaders(supabase, options.headers)

  if (debug) {
    console.log(`[authenticatedFetch] 🔑 Headers prepared:`, {
      hasAuth: !!(headers as any)['Authorization'],
      hasSubdomain: !!(headers as any)['x-organization-subdomain'],
      contentType: (headers as any)['Content-Type']
    })
  }

  return fetch(url, {
    ...options,
    headers,
  })
}

/**
 * Make authenticated GET request
 *
 * @param url - API endpoint URL
 * @param supabase - Optional Supabase client
 * @returns Fetch response
 */
export async function authenticatedGet(
  url: string,
  supabase?: SupabaseClient
): Promise<Response> {
  return authenticatedFetch(url, { method: 'GET' }, supabase)
}

/**
 * Make authenticated POST request
 *
 * @param url - API endpoint URL
 * @param data - Request body data
 * @param supabase - Optional Supabase client
 * @returns Fetch response
 */
export async function authenticatedPost(
  url: string,
  data: any,
  supabase?: SupabaseClient
): Promise<Response> {
  return authenticatedFetch(
    url,
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    supabase
  )
}

/**
 * Make authenticated PUT request
 *
 * @param url - API endpoint URL
 * @param data - Request body data
 * @param supabase - Optional Supabase client
 * @returns Fetch response
 */
export async function authenticatedPut(
  url: string,
  data: any,
  supabase?: SupabaseClient
): Promise<Response> {
  return authenticatedFetch(
    url,
    {
      method: 'PUT',
      body: JSON.stringify(data),
    },
    supabase
  )
}

/**
 * Make authenticated PATCH request
 *
 * @param url - API endpoint URL
 * @param data - Request body data
 * @param supabase - Optional Supabase client
 * @returns Fetch response
 */
export async function authenticatedPatch(
  url: string,
  data: any,
  supabase?: SupabaseClient
): Promise<Response> {
  return authenticatedFetch(
    url,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
    supabase
  )
}

/**
 * Make authenticated DELETE request
 *
 * @param url - API endpoint URL
 * @param supabase - Optional Supabase client
 * @returns Fetch response
 */
export async function authenticatedDelete(
  url: string,
  supabase?: SupabaseClient
): Promise<Response> {
  return authenticatedFetch(url, { method: 'DELETE' }, supabase)
}

/**
 * Helper to check if response is successful and return JSON
 *
 * @param response - Fetch response
 * @returns Parsed JSON data
 * @throws Error if response is not ok
 */
export async function handleAuthenticatedResponse<T = any>(
  response: Response
): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      error: response.statusText
    }))

    throw new Error(errorData.error || errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Make authenticated request and return parsed JSON
 *
 * Combines authenticatedFetch with response handling
 *
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @param supabase - Optional Supabase client
 * @returns Parsed JSON data
 *
 * @example
 * ```typescript
 * const jobs = await authenticatedRequest<Job[]>('/api/v1/jobs')
 * ```
 */
export async function authenticatedRequest<T = any>(
  url: string,
  options: RequestInit = {},
  supabase?: SupabaseClient
): Promise<T> {
  const response = await authenticatedFetch(url, options, supabase)
  return handleAuthenticatedResponse<T>(response)
}
