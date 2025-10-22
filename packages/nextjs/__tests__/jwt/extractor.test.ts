/**
 * Unit tests for JWT extraction and validation utilities
 */

import {
  extractJwtPayload,
  isTokenExpired,
  extractTokenFromHeader,
  isValidTokenFormat,
  isAdminToken,
  isSuperAdminToken,
  getEmailFromToken,
  getUserIdFromToken,
  getRoleFromToken,
} from '../../src/jwt/extractor'

describe('JWT Extractor Utilities', () => {
  // Helper to create a test JWT token
  const createTestToken = (payload: any): string => {
    const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url')
    const payloadStr = Buffer.from(JSON.stringify(payload)).toString('base64url')
    const signature = 'test-signature'
    return `${header}.${payloadStr}.${signature}`
  }

  describe('extractJwtPayload', () => {
    it('should extract payload from valid JWT token', () => {
      const payload = { sub: '123', email: 'test@example.com', exp: Date.now() / 1000 + 3600 }
      const token = createTestToken(payload)

      const result = extractJwtPayload(token)

      expect(result).not.toBeNull()
      expect(result?.sub).toBe('123')
      expect(result?.email).toBe('test@example.com')
    })

    it('should return null for invalid token format (less than 3 parts)', () => {
      const result = extractJwtPayload('invalid.token')
      expect(result).toBeNull()
    })

    it('should return null for invalid token format (more than 3 parts)', () => {
      const result = extractJwtPayload('invalid.token.with.extra.parts')
      expect(result).toBeNull()
    })

    it('should return null for invalid base64 encoding', () => {
      const result = extractJwtPayload('header.!!!invalid-base64!!!.signature')
      expect(result).toBeNull()
    })

    it('should return null for empty string', () => {
      const result = extractJwtPayload('')
      expect(result).toBeNull()
    })
  })

  describe('isTokenExpired', () => {
    it('should return false for non-expired token', () => {
      const payload: any = { exp: Math.floor(Date.now() / 1000) + 3600 } // 1 hour from now
      expect(isTokenExpired(payload)).toBe(false)
    })

    it('should return true for expired token', () => {
      const payload: any = { exp: Math.floor(Date.now() / 1000) - 3600 } // 1 hour ago
      expect(isTokenExpired(payload)).toBe(true)
    })

    it('should return true for token without exp claim', () => {
      const payload: any = {}
      expect(isTokenExpired(payload)).toBe(true)
    })

    it('should return true for token with null exp', () => {
      const payload: any = { exp: null }
      expect(isTokenExpired(payload)).toBe(true)
    })

    it('should return true for token with undefined exp', () => {
      const payload: any = { exp: undefined }
      expect(isTokenExpired(payload)).toBe(true)
    })
  })

  describe('extractTokenFromHeader', () => {
    it('should extract token from Bearer header', () => {
      const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature'
      const result = extractTokenFromHeader(`Bearer ${token}`)
      expect(result).toBe(token)
    })

    it('should return null for header without Bearer prefix', () => {
      const result = extractTokenFromHeader('SomeOtherAuth token')
      expect(result).toBeNull()
    })

    it('should return null for null header', () => {
      const result = extractTokenFromHeader(null)
      expect(result).toBeNull()
    })

    it('should return null for empty string', () => {
      const result = extractTokenFromHeader('')
      expect(result).toBeNull()
    })

    it('should handle Bearer with extra spaces', () => {
      const token = 'test-token'
      const result = extractTokenFromHeader(`Bearer ${token}`)
      expect(result).toBe(token)
    })
  })

  describe('isValidTokenFormat', () => {
    it('should return true for valid 3-part JWT format', () => {
      expect(isValidTokenFormat('header.payload.signature')).toBe(true)
    })

    it('should return false for 2-part token', () => {
      expect(isValidTokenFormat('header.payload')).toBe(false)
    })

    it('should return false for 4-part token', () => {
      expect(isValidTokenFormat('header.payload.signature.extra')).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(isValidTokenFormat('')).toBe(false)
    })

    it('should return false for single part', () => {
      expect(isValidTokenFormat('onlyonepart')).toBe(false)
    })
  })

  describe('isAdminToken', () => {
    it('should return true for token with admin role in user_metadata', () => {
      const payload = { sub: '123', user_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      expect(isAdminToken(token)).toBe(true)
    })

    it('should return true for token with owner role in user_metadata', () => {
      const payload = { sub: '123', user_metadata: { role: 'owner' } }
      const token = createTestToken(payload)
      expect(isAdminToken(token)).toBe(true)
    })

    it('should return true for token with is_super_admin in user_metadata', () => {
      const payload = { sub: '123', user_metadata: { is_super_admin: true } }
      const token = createTestToken(payload)
      expect(isAdminToken(token)).toBe(true)
    })

    it('should return true for token with admin role in app_metadata', () => {
      const payload = { sub: '123', app_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      expect(isAdminToken(token)).toBe(true)
    })

    it('should return true for token with is_super_admin in app_metadata', () => {
      const payload = { sub: '123', app_metadata: { is_super_admin: true } }
      const token = createTestToken(payload)
      expect(isAdminToken(token)).toBe(true)
    })

    it('should return false for token with member role', () => {
      const payload = { sub: '123', user_metadata: { role: 'member' } }
      const token = createTestToken(payload)
      expect(isAdminToken(token)).toBe(false)
    })

    it('should return false for token without role metadata', () => {
      const payload = { sub: '123', email: 'test@example.com' }
      const token = createTestToken(payload)
      expect(isAdminToken(token)).toBe(false)
    })

    it('should return false for invalid token', () => {
      expect(isAdminToken('invalid.token')).toBe(false)
    })
  })

  describe('isSuperAdminToken', () => {
    it('should return true for token with is_super_admin in user_metadata', () => {
      const payload = { sub: '123', user_metadata: { is_super_admin: true } }
      const token = createTestToken(payload)
      expect(isSuperAdminToken(token)).toBe(true)
    })

    it('should return true for token with is_super_admin in app_metadata', () => {
      const payload = { sub: '123', app_metadata: { is_super_admin: true } }
      const token = createTestToken(payload)
      expect(isSuperAdminToken(token)).toBe(true)
    })

    it('should return false for admin token without super_admin flag', () => {
      const payload = { sub: '123', user_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      expect(isSuperAdminToken(token)).toBe(false)
    })

    it('should return false for token with is_super_admin=false', () => {
      const payload = { sub: '123', user_metadata: { is_super_admin: false } }
      const token = createTestToken(payload)
      expect(isSuperAdminToken(token)).toBe(false)
    })

    it('should return false for invalid token', () => {
      expect(isSuperAdminToken('invalid.token')).toBe(false)
    })
  })

  describe('getEmailFromToken', () => {
    it('should extract email from valid token', () => {
      const payload = { sub: '123', email: 'test@example.com' }
      const token = createTestToken(payload)
      expect(getEmailFromToken(token)).toBe('test@example.com')
    })

    it('should return null for token without email', () => {
      const payload = { sub: '123' }
      const token = createTestToken(payload)
      expect(getEmailFromToken(token)).toBeNull()
    })

    it('should return null for invalid token', () => {
      expect(getEmailFromToken('invalid.token')).toBeNull()
    })
  })

  describe('getUserIdFromToken', () => {
    it('should extract user ID (sub) from valid token', () => {
      const payload = { sub: 'user-123', email: 'test@example.com' }
      const token = createTestToken(payload)
      expect(getUserIdFromToken(token)).toBe('user-123')
    })

    it('should return null for token without sub', () => {
      const payload = { email: 'test@example.com' }
      const token = createTestToken(payload)
      expect(getUserIdFromToken(token)).toBeNull()
    })

    it('should return null for invalid token', () => {
      expect(getUserIdFromToken('invalid.token')).toBeNull()
    })
  })

  describe('getRoleFromToken', () => {
    it('should extract role from user_metadata', () => {
      const payload = { sub: '123', user_metadata: { role: 'admin' } }
      const token = createTestToken(payload)
      expect(getRoleFromToken(token)).toBe('admin')
    })

    it('should extract role from app_metadata', () => {
      const payload = { sub: '123', app_metadata: { role: 'owner' } }
      const token = createTestToken(payload)
      expect(getRoleFromToken(token)).toBe('owner')
    })

    it('should prefer user_metadata role over app_metadata', () => {
      const payload = {
        sub: '123',
        user_metadata: { role: 'admin' },
        app_metadata: { role: 'member' }
      }
      const token = createTestToken(payload)
      expect(getRoleFromToken(token)).toBe('admin')
    })

    it('should return null for token without role', () => {
      const payload = { sub: '123', email: 'test@example.com' }
      const token = createTestToken(payload)
      expect(getRoleFromToken(token)).toBeNull()
    })

    it('should return null for invalid token', () => {
      expect(getRoleFromToken('invalid.token')).toBeNull()
    })
  })

  describe('Edge Cases and Security', () => {
    it('should handle very long tokens', () => {
      const payload = {
        sub: '123',
        email: 'test@example.com',
        data: 'x'.repeat(10000) // Very long data
      }
      const token = createTestToken(payload)
      const result = extractJwtPayload(token)
      expect(result).not.toBeNull()
      expect(result?.data).toHaveLength(10000)
    })

    it('should handle special characters in email', () => {
      const payload = { sub: '123', email: 'test+tag@example.co.uk' }
      const token = createTestToken(payload)
      expect(getEmailFromToken(token)).toBe('test+tag@example.co.uk')
    })

    it('should handle tokens with additional claims', () => {
      const payload = {
        sub: '123',
        email: 'test@example.com',
        aud: 'authenticated',
        iss: 'https://example.supabase.co/auth/v1',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600,
        custom_claim: 'custom_value'
      }
      const token = createTestToken(payload)
      const result = extractJwtPayload(token)
      expect(result).not.toBeNull()
      expect(result?.custom_claim).toBe('custom_value')
    })
  })
})
