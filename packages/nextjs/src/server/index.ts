/**
 * Server-side authentication utilities for Next.js API routes
 *
 * @packageDocumentation
 */

export {
  validateAdminAuth,
  proxyToBackend,
  getBackendJwtToken,
  getSupabaseSession,
  getAdminBackendJwt,
  createAuthenticatedHeaders,
  isAuthenticated,
  isAdminAuthenticated,
  type AdminAuthResult,
  type AdminAuthError,
  type AdminAuthValidation,
} from './admin-auth'
