/**
 * Client-side authentication utilities
 *
 * @packageDocumentation
 */

export {
  authenticatedFetch,
  authenticatedGet,
  authenticatedPost,
  authenticatedPut,
  authenticatedPatch,
  authenticatedDelete,
  authenticatedRequest,
  getClientApiHeaders,
  getCurrentSubdomain,
  handleAuthenticatedResponse,
  configureAuthenticatedFetch,
  type AuthenticatedFetchConfig,
} from './authenticated-fetch'

export {
  createAuthenticatedWebSocket,
  AuthenticatedWebSocketManager,
  type WebSocketAuthOptions,
} from './websocket'
