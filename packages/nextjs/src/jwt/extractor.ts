/**
 * JWT Token Extraction and Validation Utilities
 *
 * Provides utilities for extracting and basic validation of JWT tokens.
 * Note: Full cryptographic validation happens on the backend.
 */

import type { JWTPayload } from '../types'

/**
 * Extract JWT payload without signature verification
 *
 * This is used for forwarding to backend where full validation occurs.
 * Do not use this for security-critical decisions on the frontend.
 *
 * @param token - JWT token string
 * @returns Decoded payload or null if invalid format
 */
export function extractJwtPayload(token: string): JWTPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      console.warn('[JWT] Invalid token format - expected 3 parts')
      return null
    }

    const payload = parts[1]
    const decoded = Buffer.from(payload, 'base64url').toString('utf8')
    return JSON.parse(decoded) as JWTPayload
  } catch (error) {
    console.error('[JWT] Failed to decode token:', error)
    return null
  }
}

/**
 * Check if token is expired based on the exp claim
 *
 * @param payload - Decoded JWT payload
 * @returns True if token is expired
 */
export function isTokenExpired(payload: JWTPayload): boolean {
  if (!payload.exp) return true

  const now = Math.floor(Date.now() / 1000)
  return payload.exp < now
}

/**
 * Extract token from Authorization header
 *
 * @param authHeader - Authorization header value
 * @returns Extracted token or null
 */
export function extractTokenFromHeader(authHeader: string | null): string | null {
  if (!authHeader) return null

  if (authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7)
  }

  return null
}

/**
 * Validate JWT token format (basic check)
 *
 * @param token - Token to validate
 * @returns True if token has valid format
 */
export function isValidTokenFormat(token: string): boolean {
  const parts = token.split('.')
  return parts.length === 3
}

/**
 * Check if user has admin role in JWT payload
 *
 * This provides basic frontend protection before hitting the backend.
 * Backend must still validate cryptographically.
 *
 * @param token - JWT token string
 * @returns True if token claims admin role
 */
export function isAdminToken(token: string): boolean {
  const payload = extractJwtPayload(token)
  if (!payload) return false

  const userMetadata = payload.user_metadata || {}
  const appMetadata = payload.app_metadata || {}

  return (
    userMetadata.role === 'admin' ||
    userMetadata.role === 'owner' ||
    userMetadata.is_super_admin === true ||
    appMetadata.role === 'admin' ||
    appMetadata.role === 'owner' ||
    appMetadata.is_super_admin === true
  )
}

/**
 * Check if user is super admin based on JWT payload
 *
 * @param token - JWT token string
 * @returns True if token claims super admin status
 */
export function isSuperAdminToken(token: string): boolean {
  const payload = extractJwtPayload(token)
  if (!payload) return false

  const userMetadata = payload.user_metadata || {}
  const appMetadata = payload.app_metadata || {}

  return (
    userMetadata.is_super_admin === true ||
    appMetadata.is_super_admin === true
  )
}

/**
 * Get user email from JWT token
 *
 * @param token - JWT token string
 * @returns User email or null
 */
export function getEmailFromToken(token: string): string | null {
  const payload = extractJwtPayload(token)
  return payload?.email || null
}

/**
 * Get user ID from JWT token
 *
 * @param token - JWT token string
 * @returns User ID (sub claim) or null
 */
export function getUserIdFromToken(token: string): string | null {
  const payload = extractJwtPayload(token)
  return payload?.sub || null
}

/**
 * Get user role from JWT token
 *
 * @param token - JWT token string
 * @returns User role or null
 */
export function getRoleFromToken(token: string): string | null {
  const payload = extractJwtPayload(token)
  if (!payload) return null

  const userMetadata = payload.user_metadata || {}
  const appMetadata = payload.app_metadata || {}

  return userMetadata.role || appMetadata.role || null
}
