/**
 * Next.js middleware utilities for authentication and routing
 *
 * @packageDocumentation
 */

export {
  createAuthMiddleware,
  parseSubdomain,
  handleSubdomainRouting,
  handleAuthentication,
  createMiddlewareSupabaseClient,
  matchesRoute,
  defaultMatcher,
  type MiddlewareConfig,
  type SubdomainInfo,
} from './auth-middleware'
