# @gittielabs/nextjs-fastapi-auth

> A comprehensive, production-ready authentication and authorization library for Next.js + FastAPI applications with Supabase.

[![npm version](https://badge.fury.io/js/%40gittielabs%2Fnextjs-fastapi-auth.svg)](https://www.npmjs.com/package/@gittielabs/nextjs-fastapi-auth)
[![PyPI version](https://badge.fury.io/py/gittielabs-nextjs-fastapi-auth.svg)](https://pypi.org/project/gittielabs-nextjs-fastapi-auth/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Unified Authentication** - Consistent Supabase JWT validation across frontend and backend
- **Multi-Tenant Support** - Built-in organization context with subdomain routing
- **Role-Based Access Control** - Admin, owner, and custom role management
- **Protected Routes** - Middleware and decorators for route protection
- **WebSocket Authentication** - Secure WebSocket connections with token validation
- **Type-Safe** - Full TypeScript and Python type definitions
- **Production-Ready** - Connection pooling, caching, and error handling built-in

## Quick Start

### Installation

```bash
# Frontend (Next.js)
npm install @gittielabs/nextjs-fastapi-auth

# Backend (FastAPI)
pip install gittielabs-nextjs-fastapi-auth
```

### Frontend Setup

```typescript
// middleware.ts
import { createAuthMiddleware } from '@gittielabs/nextjs-fastapi-auth/middleware'

export const middleware = createAuthMiddleware({
  protectedRoutes: ['/dashboard', '/admin'],
  adminRoutes: ['/admin'],
  subdomainAuth: true
})

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)']
}
```

```typescript
// app/api/jobs/route.ts
import { authenticatedFetch } from '@gittielabs/nextjs-fastapi-auth/client'

export async function GET() {
  const response = await authenticatedFetch('/api/v1/jobs')
  return response
}
```

### Backend Setup

```python
# main.py
from fastapi import FastAPI, Depends
from gittielabs_auth.middleware import create_auth_middleware
from gittielabs_auth.dependencies import require_auth, require_organization
from gittielabs_auth.models import AuthUser

app = FastAPI()

# Add authentication middleware
app.add_middleware(
    create_auth_middleware(
        require_auth_paths=["/api/v1/"],
        public_paths=["/health", "/docs"]
    )
)

# Protected endpoint
@app.get("/api/v1/jobs")
async def get_jobs(
    user: AuthUser = Depends(require_auth),
    org_id: str = Depends(require_organization)
):
    return {"user": user.email, "organization": org_id}
```

## Documentation

- [Quickstart Guide](./docs/quickstart.md)
- [Configuration Reference](./docs/configuration.md)
- [Pattern Cookbook](./docs/patterns.md)
- [Migration Guide](./docs/migration-guide.md)
- [API Reference](./docs/api-reference.md)

## Examples

- [Basic Next.js + FastAPI](./examples/basic-nextjs-fastapi/)
- [Multi-Tenant with Subdomains](./examples/multi-tenant-subdomains/)
- [Admin Dashboard](./examples/admin-dashboard/)

## Architecture

### Frontend (Next.js)
- **Middleware** - Route protection and subdomain handling
- **Client Utils** - Authenticated fetch with automatic token injection
- **Server Utils** - API route helpers with admin validation
- **Hooks** - React hooks for auth state and session management
- **WebSocket** - Authenticated WebSocket connections

### Backend (FastAPI)
- **Middleware** - Request authentication with Supabase JWT validation
- **Dependencies** - FastAPI dependencies for route protection
- **Services** - Auth services with connection pooling and caching
- **Context** - Organization and admin context extraction
- **WebSocket** - WebSocket authentication and connection management

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

## License

MIT © [GittieLabs](https://github.com/gittielabs)

## Support

- [GitHub Issues](https://github.com/gittielabs/nextjs-fastapi-auth/issues)
- [Documentation](https://github.com/gittielabs/nextjs-fastapi-auth/wiki)
- [Discussions](https://github.com/gittielabs/nextjs-fastapi-auth/discussions)
