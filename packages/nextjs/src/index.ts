/**
 * @gittielabs/nextjs-fastapi-auth
 *
 * Authentication and authorization library for Next.js + FastAPI applications
 *
 * @packageDocumentation
 */

// Re-export types
export type * from './types'

// Re-export JWT utilities
export {
  extractJwtPayload,
  isTokenExpired,
  extractTokenFromHeader,
  isValidTokenFormat,
  isAdminToken,
  isSuperAdminToken,
  getEmailFromToken,
  getUserIdFromToken,
  getRoleFromToken,
} from './jwt/extractor'

// Note: Client, server, middleware, and hooks are exported via package.json subpaths
// import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'
// import { validateAdminAuth } from '@gittielabs/nextjs-fastapi-auth/server'
// import { createAuthMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'
// import { useAuth } from '@gittielabs/nextjs-fastapi-auth/hooks'
