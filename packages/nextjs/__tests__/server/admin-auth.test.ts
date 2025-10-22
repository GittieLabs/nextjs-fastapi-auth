/**
 * Unit tests for admin authentication utilities
 */

import { NextRequest, NextResponse } from 'next/server'
import {
  validateAdminAuth,
  proxyToBackend,
  isAuthenticated,
  isAdminAuthenticated,
} from '../../src/server/admin-auth'

// Mock Next.js server functions
jest.mock('next/headers', () => ({
  cookies: jest.fn(),
}))

jest.mock('@supabase/ssr', () => ({
  createServerClient: jest.fn(),
}))

describe('Admin Authentication Utilities', () => {
  // Helper to create a test JWT token
  const createTestToken = (payload: any): string => {
    const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url')
    const payloadStr = Buffer.from(JSON.stringify(payload)).toString('base64url')
    const signature = 'test-signature'
    return `${header}.${payloadStr}.${signature}`
  }

  // Helper to create mock NextRequest
  const createMockRequest = (headers: Record<string, string> = {}): NextRequest => {
    const url = 'http://localhost:3000/api/test'
    const request = new NextRequest(url, {
      headers: new Headers(headers),
    })
    return request
  }

  describe('validateAdminAuth', () => {
    it('should return error for missing authorization header', async () => {
      const request = createMockRequest()

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('error')
      expect(result.error).toBeInstanceOf(NextResponse)
      if (result.error) {
        const json = await result.error.json()
        expect(json.error).toBe('Authentication required')
      }
    })

    it('should return error for authorization header without Bearer prefix', () => {
      const request = createMockRequest({
        authorization: 'SomeOtherAuth token123',
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('error')
    })

    it('should return error for invalid JWT format (not 3 parts)', async () => {
      const request = createMockRequest({
        authorization: 'Bearer invalid.token',
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('error')
      if (result.error) {
        const json = await result.error.json()
        expect(json.error).toBe('Invalid token format')
      }
    })

    it('should return error for non-admin token', async () => {
      const payload = { sub: '123', email: 'user@example.com', user_metadata: { role: 'member' } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('error')
      if (result.error) {
        const json = await result.error.json()
        expect(json.error).toContain('Admin access required')
      }
    })

    it('should return token for valid admin token (user_metadata role)', () => {
      const payload = { sub: '123', email: 'admin@example.com', user_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('token')
      expect(result.token).toBe(token)
      expect(result).not.toHaveProperty('error')
    })

    it('should return token for valid admin token (owner role)', () => {
      const payload = { sub: '123', email: 'owner@example.com', user_metadata: { role: 'owner' } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('token')
      expect(result.token).toBe(token)
    })

    it('should return token for super admin token', () => {
      const payload = { sub: '123', email: 'super@example.com', user_metadata: { is_super_admin: true } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('token')
      expect(result.token).toBe(token)
    })

    it('should return token for admin token with app_metadata', () => {
      const payload = { sub: '123', email: 'admin@example.com', app_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('token')
      expect(result.token).toBe(token)
    })

    it('should handle authorization header case-insensitively', () => {
      const payload = { sub: '123', email: 'admin@example.com', user_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        Authorization: `Bearer ${token}`, // Capital A
      })

      // Note: Headers.get() is case-insensitive in the fetch API
      const result = validateAdminAuth(request)

      // Should work because Headers API is case-insensitive
      expect(result).toHaveProperty('token')
    })
  })

  describe('proxyToBackend', () => {
    let fetchMock: jest.SpyInstance

    beforeEach(() => {
      fetchMock = jest.spyOn(global, 'fetch').mockResolvedValue(
        new Response(JSON.stringify({ success: true }), { status: 200 })
      )
    })

    afterEach(() => {
      fetchMock.mockRestore()
    })

    it('should make GET request with authorization header', async () => {
      const url = 'http://localhost:8000/api/v1/test'
      const token = 'test-token-123'

      await proxyToBackend(url, 'GET', token)

      expect(fetchMock).toHaveBeenCalledWith(url, expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        }),
      }))
    })

    it('should make POST request with body', async () => {
      const url = 'http://localhost:8000/api/v1/test'
      const token = 'test-token-123'
      const body = JSON.stringify({ data: 'test' })

      await proxyToBackend(url, 'POST', token, body)

      expect(fetchMock).toHaveBeenCalledWith(url, expect.objectContaining({
        method: 'POST',
        body: body,
      }))
    })

    it('should make PUT request with body', async () => {
      const url = 'http://localhost:8000/api/v1/test'
      const token = 'test-token-123'
      const body = JSON.stringify({ data: 'updated' })

      await proxyToBackend(url, 'PUT', token, body)

      expect(fetchMock).toHaveBeenCalledWith(url, expect.objectContaining({
        method: 'PUT',
        body: body,
      }))
    })

    it('should make PATCH request with body', async () => {
      const url = 'http://localhost:8000/api/v1/test'
      const token = 'test-token-123'
      const body = JSON.stringify({ data: 'patched' })

      await proxyToBackend(url, 'PATCH', token, body)

      expect(fetchMock).toHaveBeenCalledWith(url, expect.objectContaining({
        method: 'PATCH',
        body: body,
      }))
    })

    it('should not include body for GET request even if provided', async () => {
      const url = 'http://localhost:8000/api/v1/test'
      const token = 'test-token-123'
      const body = JSON.stringify({ data: 'should-not-be-sent' })

      await proxyToBackend(url, 'GET', token, body)

      expect(fetchMock).toHaveBeenCalledWith(url, expect.objectContaining({
        method: 'GET',
      }))

      const callArgs = fetchMock.mock.calls[0][1]
      expect(callArgs).not.toHaveProperty('body')
    })

    it('should return the response from backend', async () => {
      const mockData = { result: 'success' }
      fetchMock.mockResolvedValue(
        new Response(JSON.stringify(mockData), { status: 200 })
      )

      const response = await proxyToBackend('http://localhost:8000/api/v1/test', 'GET', 'token')
      const data = await response.json()

      expect(data).toEqual(mockData)
    })

    it('should handle error responses', async () => {
      fetchMock.mockResolvedValue(
        new Response(JSON.stringify({ error: 'Not found' }), { status: 404 })
      )

      const response = await proxyToBackend('http://localhost:8000/api/v1/test', 'GET', 'token')

      expect(response.status).toBe(404)
    })
  })

  describe('isAuthenticated', () => {
    it('should return true for valid Bearer token', () => {
      const token = createTestToken({ sub: '123', email: 'test@example.com' })
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      expect(isAuthenticated(request)).toBe(true)
    })

    it('should return false for missing authorization header', () => {
      const request = createMockRequest()

      expect(isAuthenticated(request)).toBe(false)
    })

    it('should return false for invalid token format', () => {
      const request = createMockRequest({
        authorization: 'Bearer invalid.token',
      })

      expect(isAuthenticated(request)).toBe(false)
    })

    it('should return false for non-Bearer authorization', () => {
      const request = createMockRequest({
        authorization: 'Basic dXNlcjpwYXNz',
      })

      expect(isAuthenticated(request)).toBe(false)
    })

    it('should return false for empty Bearer token', () => {
      const request = createMockRequest({
        authorization: 'Bearer ',
      })

      expect(isAuthenticated(request)).toBe(false)
    })
  })

  describe('isAdminAuthenticated', () => {
    it('should return true for admin token', () => {
      const payload = { sub: '123', email: 'admin@example.com', user_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      expect(isAdminAuthenticated(request)).toBe(true)
    })

    it('should return true for super admin token', () => {
      const payload = { sub: '123', email: 'super@example.com', user_metadata: { is_super_admin: true } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      expect(isAdminAuthenticated(request)).toBe(true)
    })

    it('should return false for member token', () => {
      const payload = { sub: '123', email: 'user@example.com', user_metadata: { role: 'member' } }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      expect(isAdminAuthenticated(request)).toBe(false)
    })

    it('should return false for missing authorization', () => {
      const request = createMockRequest()

      expect(isAdminAuthenticated(request)).toBe(false)
    })

    it('should return false for invalid token format', () => {
      const request = createMockRequest({
        authorization: 'Bearer invalid.token',
      })

      expect(isAdminAuthenticated(request)).toBe(false)
    })
  })

  describe('Edge Cases and Security', () => {
    it('should handle very long tokens', () => {
      const payload = {
        sub: '123',
        email: 'test@example.com',
        user_metadata: { role: 'admin', data: 'x'.repeat(10000) }
      }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('token')
      expect(result.token).toBe(token)
    })

    it('should handle tokens with special characters in email', () => {
      const payload = {
        sub: '123',
        email: 'admin+special@example.co.uk',
        user_metadata: { role: 'admin' }
      }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('token')
    })

    it('should not be fooled by malicious payloads claiming admin', () => {
      // Token with admin claim but invalid format (only 2 parts)
      const fakeToken = 'eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYWRtaW4ifQ'
      const request = createMockRequest({
        authorization: `Bearer ${fakeToken}`,
      })

      const result = validateAdminAuth(request)

      expect(result).toHaveProperty('error')
    })

    it('should handle tokens with both user_metadata and app_metadata', () => {
      const payload = {
        sub: '123',
        email: 'hybrid@example.com',
        user_metadata: { role: 'member' },
        app_metadata: { role: 'admin' } // app_metadata takes precedence
      }
      const token = createTestToken(payload)
      const request = createMockRequest({
        authorization: `Bearer ${token}`,
      })

      const result = validateAdminAuth(request)

      // Should accept because app_metadata has admin
      expect(result).toHaveProperty('token')
    })
  })
})
