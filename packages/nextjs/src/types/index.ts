/**
 * Type definitions for @gittielabs/nextjs-fastapi-auth
 */

export interface JWTPayload {
  sub: string
  email: string
  aud: string
  exp: number
  iat: number
  iss: string
  user_metadata?: {
    role?: string
    is_super_admin?: boolean
    first_name?: string
    last_name?: string
    avatar_url?: string
    [key: string]: any
  }
  app_metadata?: {
    role?: string
    is_super_admin?: boolean
    [key: string]: any
  }
  [key: string]: any
}

export interface AuthUser {
  id: string
  email: string
  role: 'admin' | 'owner' | 'member' | 'billing'
  organization_id?: string
  is_super_admin?: boolean
  is_authenticated: boolean
  first_name?: string
  last_name?: string
  avatar_url?: string
  organizations?: Array<{
    id: string
    name: string
    subdomain: string
    role: string
    is_active?: boolean | string
  }>
  session_id?: string | null
  expires_at?: number | null
}

export interface AuthConfig {
  supabase?: {
    url?: string
    anonKey?: string
  }
  routes?: {
    protected?: string[]
    public?: string[]
    admin?: string[]
  }
  subdomain?: {
    enabled?: boolean
    mainDomain?: string
  }
  backend?: {
    url?: string
  }
}

export interface AuthResult {
  user?: AuthUser
  token?: string
  error?: string
}

export interface AdminAuthResult {
  user?: AuthUser
  token: string
  error?: {
    message: string
    status: number
  }
}

export type AuthMiddlewareConfig = {
  protectedRoutes?: string[]
  publicRoutes?: string[]
  adminRoutes?: string[]
  marketingRoutes?: string[]
  subdomainAuth?: boolean
  mainDomain?: string
  apiSubdomain?: string
}
