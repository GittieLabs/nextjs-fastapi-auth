# Basic Usage Example

This example demonstrates how to use `@gittielabs/nextjs-fastapi-auth` in a Next.js + FastAPI application.

## Project Structure

```
your-project/
├── frontend/              # Next.js application
│   ├── src/
│   │   ├── middleware.ts  # Auth middleware
│   │   ├── app/
│   │   │   ├── api/       # API routes
│   │   │   ├── admin/     # Admin pages
│   │   │   └── dashboard/ # Protected pages
│   └── package.json
└── backend/               # FastAPI application
    ├── main.py           # FastAPI app
    ├── auth/             # Auth configuration
    └── requirements.txt
```

## Frontend (Next.js)

### 1. Install Package

```bash
npm install @gittielabs/nextjs-fastapi-auth
```

### 2. Configure Middleware

```typescript
// src/middleware.ts
import { createAuthMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'

export default createAuthMiddleware({
  supabase: {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  },
  mainDomain: 'myapp.com',
  protectedRoutes: ['/dashboard', '/admin', '/settings'],
  publicRoutes: ['/', '/auth/login', '/auth/signup'],
  adminRoutes: ['/admin'],
  marketingRoutes: ['/pricing', '/features', '/about'],
  debug: process.env.NODE_ENV === 'development',
})

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
```

### 3. Use Client Authentication

```typescript
// app/api/jobs/route.ts - Client-side authenticated fetch
import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'
import { createClient } from '@/lib/supabase/client'

export async function GET() {
  const supabase = createClient()

  const response = await authenticatedFetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/jobs`,
    {
      method: 'GET',
    },
    supabase
  )

  if (!response.ok) {
    return Response.json({ error: 'Failed to fetch jobs' }, { status: response.status })
  }

  const data = await response.json()
  return Response.json(data)
}
```

### 4. Use Server-Side Validation

```typescript
// app/api/admin/users/route.ts - Admin API route
import { NextRequest, NextResponse } from 'next/server'
import { validateAdminAuth, proxyToBackend } from '@gittielabs/nextjs-fastapi-auth/server'

export async function GET(request: NextRequest) {
  // Validate admin authorization
  const auth = validateAdminAuth(request)
  if (auth.error) return auth.error

  // Proxy to backend with validated token
  const response = await proxyToBackend(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/users`,
    'GET',
    auth.token
  )

  const data = await response.json()
  return NextResponse.json(data)
}
```

### 5. Use JWT Utilities

```typescript
// lib/auth/utils.ts - JWT token inspection
import { extractJwtPayload, isAdminToken, getEmailFromToken } from '@gittielabs/nextjs-fastapi-auth'

export function checkUserRole(token: string) {
  const payload = extractJwtPayload(token)

  if (!payload) {
    return { error: 'Invalid token' }
  }

  return {
    email: getEmailFromToken(token),
    isAdmin: isAdminToken(token),
    userId: payload.sub,
  }
}
```

### 6. WebSocket Authentication

```typescript
// hooks/useRealtimeUpdates.ts
import { useEffect, useState } from 'react'
import { createAuthenticatedWebSocket } from '@gittielabs/nextjs-fastapi-auth/client'
import { createClient } from '@/lib/supabase/client'

export function useRealtimeUpdates() {
  const [status, setStatus] = useState<string>('disconnected')
  const supabase = createClient()

  useEffect(() => {
    const connectWebSocket = async () => {
      const ws = await createAuthenticatedWebSocket({
        supabase,
        url: 'ws://localhost:8000/ws/updates',
        autoReconnect: true,
        debug: true,
        onOpen: () => setStatus('connected'),
        onClose: () => setStatus('disconnected'),
        onMessage: (event) => {
          const data = JSON.parse(event.data)
          console.log('Update received:', data)
        },
      })
    }

    connectWebSocket()
  }, [])

  return { status }
}
```

## Backend (FastAPI)

### 1. Install Package

```bash
pip install gittielabs-nextjs-fastapi-auth
```

### 2. Configure Authentication Service

```python
# auth/config.py
from gittielabs_fastapi_auth import SupabaseAuthService
import os

auth_service = SupabaseAuthService(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY"),
)
```

### 3. Create Authentication Dependencies

```python
# auth/dependencies.py
from fastapi import Depends, HTTPException, Header
from gittielabs_fastapi_auth import AuthUser
from .config import auth_service

async def require_auth(authorization: str = Header(None)) -> AuthUser:
    """Require authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    token = auth_service.extract_token_from_header(authorization)
    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user

async def require_admin(user: AuthUser = Depends(require_auth)) -> AuthUser:
    """Require admin user."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user
```

### 4. Use in API Routes

```python
# main.py
from fastapi import FastAPI, Depends, Request
from gittielabs_fastapi_auth import AuthUser
from auth.dependencies import require_auth, require_admin

app = FastAPI()

@app.get("/api/v1/jobs")
async def list_jobs(user: AuthUser = Depends(require_auth)):
    """Protected endpoint - requires authentication."""
    return {
        "jobs": [...],
        "user_email": user.email,
        "organization_id": user.organization_id
    }

@app.get("/api/v1/admin/users")
async def list_users(user: AuthUser = Depends(require_admin)):
    """Admin endpoint - requires admin role."""
    return {
        "users": [...],
        "admin_email": user.email
    }
```

### 5. Organization Context

```python
# routes/organizations.py
from fastapi import APIRouter, Request, Depends
from gittielabs_fastapi_auth import (
    AuthUser,
    get_organization_id_from_request
)
from auth.dependencies import require_auth

router = APIRouter()

@router.get("/api/v1/org/data")
async def get_org_data(
    request: Request,
    user: AuthUser = Depends(require_auth)
):
    """Get data for current organization from subdomain."""
    org_id = get_organization_id_from_request(request)

    # Query data filtered by organization
    return {
        "organization_id": org_id,
        "user": user.email,
        "data": [...]
    }
```

### 6. Admin Access Control

```python
# routes/admin.py
from fastapi import APIRouter, Request, Depends
from gittielabs_fastapi_auth import (
    verify_admin_access,
    get_admin_organization_context,
    AdminRole
)
from auth.dependencies import require_auth

router = APIRouter()

@router.get("/api/v1/admin/organizations")
async def list_admin_organizations(
    request: Request,
    user = Depends(require_auth)
):
    """List organizations where user has admin access."""
    # Verify admin access and get context
    current_org, accessible_orgs, admin_user = verify_admin_access(
        request,
        required_role=AdminRole.ORG_ADMIN
    )

    return {
        "current_organization": current_org,
        "accessible_organizations": accessible_orgs,
        "admin_email": admin_user.email,
        "is_super_admin": admin_user.is_super_admin
    }

@router.get("/api/v1/admin/context")
async def get_admin_context(
    request: Request,
    user = Depends(require_auth)
):
    """Get comprehensive admin context."""
    context = get_admin_organization_context(request)
    return context
```

## Environment Variables

### Frontend (.env.local)

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT Secret (optional, defaults to service key)
JWT_SECRET=your-jwt-secret
```

## Testing

### Frontend

```typescript
// __tests__/auth.test.ts
import { extractJwtPayload, isAdminToken } from '@gittielabs/nextjs-fastapi-auth'

describe('JWT Utilities', () => {
  it('should extract payload from valid JWT', () => {
    const token = 'eyJ...'  // Valid JWT
    const payload = extractJwtPayload(token)

    expect(payload).toBeTruthy()
    expect(payload?.email).toBe('user@example.com')
  })

  it('should detect admin tokens', () => {
    const adminToken = 'eyJ...'  // Token with admin role
    expect(isAdminToken(adminToken)).toBe(true)

    const userToken = 'eyJ...'  // Token without admin role
    expect(isAdminToken(userToken)).toBe(false)
  })
})
```

### Backend

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from gittielabs_fastapi_auth import SupabaseAuthService

@pytest.mark.asyncio
async def test_validate_jwt_token():
    service = SupabaseAuthService(
        supabase_url="https://test.supabase.co",
        supabase_service_key="test-key"
    )

    valid_token = "eyJ..."  # Valid test JWT
    is_valid, payload, error = await service.validate_jwt_token(valid_token)

    assert is_valid is True
    assert payload is not None
    assert error is None

def test_protected_endpoint_requires_auth(client: TestClient):
    response = client.get("/api/v1/jobs")
    assert response.status_code == 401

def test_protected_endpoint_with_auth(client: TestClient, auth_headers):
    response = client.get("/api/v1/jobs", headers=auth_headers)
    assert response.status_code == 200
```

## Next Steps

- **Customize Roles**: Extend `UserRole` enum with custom roles
- **Add Permissions**: Implement fine-grained permissions beyond roles
- **Database Integration**: Add organization lookup from database
- **Middleware Customization**: Add custom logic to middleware
- **Error Handling**: Implement custom error responses
- **Logging**: Add application-specific logging
