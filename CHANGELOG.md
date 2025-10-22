# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-22

### Added

#### Frontend (Next.js)
- JWT utilities for token extraction, validation, and role checking
- Client-side authenticated fetch with automatic Supabase token injection
- Server-side admin authentication and proxy helpers
- WebSocket authentication with auto-reconnect
- Middleware factory for route protection and subdomain routing
- Organization context injection via headers
- TypeScript type definitions for all APIs
- Subpath exports for tree-shaking and clean imports

#### Backend (FastAPI)
- Supabase JWT validation service
- User extraction from JWT tokens
- Organization context utilities for multi-tenancy
- JWT-based admin access control
- Role-based permission checking
- Pydantic models for users, organizations, and tokens
- Python type hints throughout

#### Documentation
- Comprehensive README with quickstart examples
- Basic usage example with frontend and backend code
- API documentation for both packages
- Installation and setup instructions

### Architecture

#### Frontend Package Structure
```
@gittielabs/nextjs-fastapi-auth/
├── /                  # Main exports (types, JWT utilities)
├── /middleware        # Auth middleware
├── /client           # Client-side utilities
├── /server           # Server-side utilities
├── /hooks            # React hooks (future)
└── /types            # TypeScript types
```

#### Backend Package Structure
```
gittielabs-nextjs-fastapi-auth/
├── models.py                   # Pydantic models
├── supabase_auth.py           # Supabase JWT service
├── organization_context.py    # Multi-tenant context
└── jwt_admin_context.py       # Admin access control
```

### Features

- ✅ Supabase JWT token validation (frontend and backend)
- ✅ Role-based access control (viewer, member, admin, owner, super_admin)
- ✅ Multi-tenant support with subdomain routing
- ✅ Organization context extraction
- ✅ Protected route middleware
- ✅ Authenticated fetch utilities
- ✅ Admin access verification
- ✅ WebSocket authentication
- ✅ Type-safe APIs (TypeScript and Python)

### Security

- JWT tokens validated for format, expiration, and issuer
- Defense in depth: frontend basic validation + backend cryptographic validation
- Secure token transmission via Authorization headers
- Subdomain-based organization isolation
- Role-based access control with permission checking

### Dependencies

#### Frontend
- `next` >= 13.0.0
- `react` >= 18.0.0
- `@supabase/ssr` >= 0.0.10
- `@supabase/supabase-js` >= 2.38.0

#### Backend
- `fastapi` >= 0.100.0
- `pydantic` >= 2.0.0
- `pyjwt` >= 2.8.0
- `supabase` >= 2.0.0
- `loguru` >= 0.7.0

## [Unreleased]

### Planned Features

- FastAPI middleware for automatic request authentication
- FastAPI dependencies for route protection
- React hooks for auth state management
- WebSocket connection manager
- Token refresh utilities
- Session management helpers
- Rate limiting utilities
- Audit logging
- Permission system beyond roles
- OpenAPI/Swagger integration
- Testing utilities and fixtures

---

## Release Process

1. Update version in `package.json` and `pyproject.toml`
2. Update CHANGELOG.md with release notes
3. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. Publish to npm: `npm publish` (in packages/nextjs)
6. Publish to PyPI: `python -m build && twine upload dist/*` (in packages/fastapi)
