# Quickstart Guide

Get up and running with `@gittielabs/nextjs-fastapi-auth` in under 10 minutes.

## Prerequisites

- Node.js 18+ (for Next.js 15+)
- Python 3.9+
- Supabase account with a project created
- Basic familiarity with Next.js and FastAPI

## Step 1: Get Your Supabase Credentials

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings > API
4. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Anon/Public Key**
   - **Service Role Key** (keep this secret!)

## Step 2: Frontend Setup (Next.js)

### Install the Package

```bash
npm install @gittielabs/nextjs-fastapi-auth
# or
yarn add @gittielabs/nextjs-fastapi-auth
# or
pnpm add @gittielabs/nextjs-fastapi-auth
```

### Configure Environment Variables

Create `.env.local` in your Next.js project root:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Set Up Middleware

Create `middleware.ts` in your project root:

```typescript
import { authMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'

export default authMiddleware

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
}
```

### Create a Protected API Route

Create `app/api/protected/route.ts`:

```typescript
import { validateAdminAuth } from '@gittielabs/nextjs-fastapi-auth/server'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const auth = validateAdminAuth(request)

  if (auth.error) {
    return auth.error
  }

  return NextResponse.json({
    message: 'You are authenticated!',
    user: auth.user,
  })
}
```

### Use Authenticated Fetch

Create `app/components/DataFetcher.tsx`:

```typescript
'use client'

import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'
import { useState } from 'react'

export default function DataFetcher() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await authenticatedFetch('/api/protected')
      const result = await response.json()
      setData(result)
    } catch (error) {
      console.error('Failed to fetch:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button onClick={fetchData} disabled={loading}>
        {loading ? 'Loading...' : 'Fetch Protected Data'}
      </button>
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  )
}
```

## Step 3: Backend Setup (FastAPI)

### Install the Package

```bash
pip install gittielabs-nextjs-fastapi-auth
```

### Configure Environment Variables

Create `.env` in your FastAPI project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Set Up Your FastAPI App

Create or update `main.py`:

```python
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from gittielabs_fastapi_auth import (
    SupabaseAuthService,
    get_organization_id_from_request,
    verify_admin_access,
)
import os

app = FastAPI(title="My API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize auth service
auth_service = SupabaseAuthService(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_service_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/user/me")
async def get_current_user(request: Request):
    """Get the current authenticated user."""
    auth_header = request.headers.get("authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = auth_service.extract_token_from_header(auth_header)
    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "organization_id": user.organization_id,
    }

@app.get("/api/v1/organization/data")
async def get_organization_data(request: Request):
    """Get organization-specific data."""
    # Authenticate user
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization required")

    token = auth_service.extract_token_from_header(auth_header)
    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get organization context
    org_id = get_organization_id_from_request(request)

    # Your business logic here
    return {
        "organization_id": org_id,
        "user_email": user.email,
        "message": "Organization data would go here",
    }

@app.get("/api/v1/admin/users")
async def list_admin_users(request: Request):
    """Admin-only endpoint to list users."""
    # Verify admin access
    current_org, accessible_orgs, user = verify_admin_access(request)

    # Your admin business logic here
    return {
        "current_organization": current_org,
        "accessible_organizations": accessible_orgs,
        "admin_email": user.email,
        "message": "User list would go here",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Run Your FastAPI Server

```bash
uvicorn main:app --reload
```

## Step 4: Test Your Setup

### Test Authentication Flow

1. **Start both servers:**
   ```bash
   # Terminal 1 - Next.js
   npm run dev

   # Terminal 2 - FastAPI
   uvicorn main:app --reload
   ```

2. **Create a test user in Supabase:**
   - Go to Authentication > Users in Supabase Dashboard
   - Create a new user
   - Note their email and set a password

3. **Add login to your Next.js app:**

```typescript
// app/login/page.tsx
'use client'

import { createClient } from '@supabase/supabase-js'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      setError(error.message)
      return
    }

    router.push('/dashboard')
  }

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px' }}>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
        />
        <button
          type="submit"
          style={{ width: '100%', padding: '10px' }}
        >
          Login
        </button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  )
}
```

4. **Test the protected route:**

```typescript
// app/dashboard/page.tsx
'use client'

import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'
import { useEffect, useState } from 'react'

export default function DashboardPage() {
  const [userData, setUserData] = useState<any>(null)

  useEffect(() => {
    const fetchUser = async () => {
      const response = await authenticatedFetch('http://localhost:8000/api/v1/user/me')
      const data = await response.json()
      setUserData(data)
    }

    fetchUser()
  }, [])

  if (!userData) {
    return <div>Loading...</div>
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Dashboard</h1>
      <pre>{JSON.stringify(userData, null, 2)}</pre>
    </div>
  )
}
```

5. **Try it out:**
   - Navigate to `http://localhost:3000/login`
   - Log in with your test user credentials
   - You should be redirected to the dashboard
   - The dashboard should display your user data fetched from FastAPI

## Next Steps

- [Learn about configuration options](./configuration.md)
- [Explore common patterns](./patterns.md)
- [Check out example projects](../examples/)
- [Read the API reference](./api-reference.md)

## Troubleshooting

### "No JWT token found"

**Problem:** The authentication isn't working.

**Solution:**
1. Check that cookies are being set after login
2. Verify your `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are correct
3. Ensure you're using `httpOnly` cookies for tokens

### "Invalid JWT token"

**Problem:** FastAPI is rejecting the token.

**Solution:**
1. Verify `SUPABASE_SERVICE_ROLE_KEY` is correct (not the anon key)
2. Check token hasn't expired
3. Ensure the token is being sent in the Authorization header

### CORS Errors

**Problem:** Browser blocking requests from Next.js to FastAPI.

**Solution:**
1. Add CORS middleware to FastAPI (shown in Step 3)
2. Allow your Next.js origin (`http://localhost:3000`)
3. Set `allow_credentials=True`

### "Organization context not found"

**Problem:** Multi-tenant features not working.

**Solution:**
1. This is expected if you haven't set up subdomain routing yet
2. You can skip organization context for simple single-tenant apps
3. See [Multi-Tenant Guide](./patterns.md#multi-tenant-setup) for full setup

## Support

Need help?
- [GitHub Issues](https://github.com/gittielabs/nextjs-fastapi-auth/issues)
- [Discussions](https://github.com/gittielabs/nextjs-fastapi-auth/discussions)
