# @gittielabs/nextjs-fastapi-auth

Authentication and authorization library for Next.js 15+ applications with Supabase backend integration.

## Installation

```bash
npm install @gittielabs/nextjs-fastapi-auth
# or
yarn add @gittielabs/nextjs-fastapi-auth
# or
pnpm add @gittielabs/nextjs-fastapi-auth
```

## Features

- 🔐 **JWT Token Management** - Extract and validate Supabase JWT tokens
- 🛡️ **Admin Authentication** - Server-side admin role verification
- 🔄 **Auth Middleware** - Automatic authentication and subdomain handling
- 🌐 **Multi-Tenancy** - Organization context via subdomains
- 📡 **WebSocket Support** - Authenticated WebSocket connections
- 🚀 **Next.js 15 Compatible** - Full support for async cookies and headers

## Quick Start

### 1. Environment Setup

Create a `.env.local` file:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 2. Middleware Setup

Create or update `middleware.ts`:

```typescript
import { authMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'

export default authMiddleware

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
}
```

### 3. Protected API Routes

Use admin authentication in API routes:

```typescript
// app/api/admin/users/route.ts
import { validateAdminAuth } from '@gittielabs/nextjs-fastapi-auth/server'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const auth = validateAdminAuth(request)

  if (auth.error) {
    return auth.error
  }

  // User is authenticated as admin
  return NextResponse.json({
    user: auth.user,
    message: 'Admin access granted'
  })
}
```

### 4. Client-Side Authentication

Use authenticated fetch for API calls:

```typescript
'use client'

import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'

export default function MyComponent() {
  const fetchData = async () => {
    const response = await authenticatedFetch('/api/data')
    const data = await response.json()
    console.log(data)
  }

  return <button onClick={fetchData}>Fetch Data</button>
}
```

## Core Components

### JWT Utilities

Extract and decode JWT tokens:

```typescript
import {
  extractJwtFromRequest,
  extractJwtPayload,
  extractSubdomainFromJwt
} from '@gittielabs/nextjs-fastapi-auth/jwt'

// Extract JWT from NextRequest
const token = extractJwtFromRequest(request)

// Decode JWT payload
const payload = extractJwtPayload(token)
if (payload) {
  console.log('User ID:', payload.sub)
  console.log('Email:', payload.email)
}

// Extract organization subdomain
const subdomain = extractSubdomainFromJwt(token)
```

### Admin Authentication

Validate admin access in API routes:

```typescript
import { validateAdminAuth } from '@gittielabs/nextjs-fastapi-auth/server'

export async function POST(request: NextRequest) {
  const auth = validateAdminAuth(request)

  if (auth.error) {
    return auth.error // Returns 401 or 403 response
  }

  // Access authenticated user data
  const { user } = auth
  console.log('Admin user:', user.email)
  console.log('Organization:', user.organization_subdomain)

  // Proceed with admin operation...
}
```

### Middleware

The auth middleware handles:
- Authentication verification
- Subdomain-based routing
- WWW redirect
- Protected route enforcement

```typescript
import { authMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'

// Use as-is or customize configuration
export default authMiddleware

// Or create custom middleware
import { NextRequest, NextResponse } from 'next/server'
import { extractJwtFromRequest } from '@gittielabs/nextjs-fastapi-auth/jwt'

export async function middleware(request: NextRequest) {
  const token = extractJwtFromRequest(request)

  if (!token && request.nextUrl.pathname.startsWith('/protected')) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}
```

### Authenticated Fetch

Client-side fetch with automatic authentication:

```typescript
import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'

// Automatically includes Authorization header
const response = await authenticatedFetch('/api/data', {
  method: 'POST',
  body: JSON.stringify({ key: 'value' }),
})

const data = await response.json()
```

### WebSocket Support

Create authenticated WebSocket connections:

```typescript
import { createAuthenticatedWebSocket } from '@gittielabs/nextjs-fastapi-auth/client'

const ws = await createAuthenticatedWebSocket('wss://api.example.com/ws')

ws.onmessage = (event) => {
  console.log('Message:', event.data)
}

ws.send(JSON.stringify({ action: 'subscribe', channel: 'updates' }))
```

## User Roles and Permissions

The library supports role-based access control:

```typescript
interface JwtPayload {
  sub: string                    // User ID
  email: string                  // User email
  user_metadata: {
    role?: string                // User role
    is_super_admin?: boolean     // Super admin flag
    organization_subdomain?: string
  }
  // ... other Supabase JWT fields
}
```

Roles are used by the admin authentication to control access:
- Super admins have access to all organizations
- Organization admins can access their organization's admin routes
- Regular users are blocked from admin routes

## API Reference

### JWT Functions

#### `extractJwtFromRequest(request: NextRequest): string | null`
Extract JWT token from request headers or cookies.

#### `extractJwtPayload(token: string): JwtPayload | null`
Decode and parse JWT payload.

#### `extractSubdomainFromJwt(token: string): string | null`
Extract organization subdomain from JWT metadata.

#### `extractSubdomainFromRequest(request: NextRequest): string | null`
Extract subdomain from request hostname.

### Server Functions

#### `validateAdminAuth(request: NextRequest): { user: JwtPayload } | { error: NextResponse }`
Validate that the request is from an authenticated admin user.

Returns either:
- `{ user: JwtPayload }` - User is authenticated as admin
- `{ error: NextResponse }` - Authentication failed (401 or 403)

### Middleware

#### `authMiddleware(request: NextRequest): Promise<NextResponse>`
Complete authentication middleware with:
- WWW redirect
- Subdomain handling
- Authentication verification
- Protected route enforcement

### Client Functions

#### `authenticatedFetch(url: string, options?: RequestInit): Promise<Response>`
Fetch with automatic JWT authentication.

#### `createAuthenticatedWebSocket(url: string): Promise<WebSocket>`
Create WebSocket connection with JWT authentication.

## TypeScript Support

This library is written in TypeScript and includes full type definitions:

```typescript
import type {
  JwtPayload,
  AdminAuthResult,
  AuthenticatedUser
} from '@gittielabs/nextjs-fastapi-auth'
```

## Development

### Running Tests

```bash
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Building

```bash
npm run build
```

### Linting

```bash
npm run lint
```

## Best Practices

### 1. Server-Side Authentication

Always validate authentication on the server side:

```typescript
// ✅ Good - Server-side validation
export async function GET(request: NextRequest) {
  const auth = validateAdminAuth(request)
  if (auth.error) return auth.error
  // ... secure operation
}

// ❌ Bad - Client-side only
'use client'
export default function AdminPanel() {
  // Client-side checks can be bypassed
}
```

### 2. Environment Variables

Keep sensitive keys secure:

```typescript
// ✅ Good - Use environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL

// ❌ Bad - Hardcoded values
const supabaseUrl = 'https://myproject.supabase.co'
```

### 3. Error Handling

Handle authentication errors gracefully:

```typescript
const auth = validateAdminAuth(request)

if (auth.error) {
  // Log error details server-side
  console.error('Auth failed:', auth.error)

  // Return user-friendly error
  return auth.error
}
```

### 4. Multi-Tenancy

Use subdomains for organization isolation:

```typescript
// Extract subdomain for data filtering
const subdomain = extractSubdomainFromRequest(request)

// Filter queries by organization
const data = await db.query({
  where: { organization_subdomain: subdomain }
})
```

## Troubleshooting

### "No JWT token found"

Ensure the client is sending the Authorization header:

```typescript
// Check if token exists in cookies
const cookies = await import('next/headers')
const cookieStore = await cookies.cookies()
const token = cookieStore.get('sb-access-token')
```

### "Invalid JWT token"

Verify your Supabase configuration:
- Check `NEXT_PUBLIC_SUPABASE_URL` is correct
- Ensure `SUPABASE_SERVICE_ROLE_KEY` is the service role key (not anon key)
- Confirm the JWT hasn't expired

### "Subdomain not found"

Ensure your middleware is properly configured:

```typescript
export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
```

## Migration Guide

### From Previous Versions

If migrating from an older version:

1. Update to Next.js 15+
2. Make cookies and headers async:

```typescript
// Before
const cookieStore = cookies()

// After (Next.js 15+)
const cookieStore = await cookies()
```

3. Update middleware exports:

```typescript
// Before
export { middleware } from '@gittielabs/nextjs-fastapi-auth'

// After
import { authMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'
export default authMiddleware
```

## Contributing

Contributions are welcome! Please see the main repository for guidelines.

## License

MIT © GittieLabs

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/gittielabs/nextjs-fastapi-auth/issues)
- Documentation: [Full docs](https://github.com/gittielabs/nextjs-fastapi-auth)
