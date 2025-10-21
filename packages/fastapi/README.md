# @gittielabs/nextjs-fastapi-auth (FastAPI)

Authentication and authorization library for FastAPI backends in Next.js + FastAPI applications with Supabase.

## Installation

```bash
pip install gittielabs-nextjs-fastapi-auth
```

## Features

- 🔐 **Supabase JWT Validation** - Validate and decode Supabase JWT tokens
- 👤 **User Management** - Extract user information from JWT tokens
- 🏢 **Multi-Tenancy** - Organization context from subdomains
- 🛡️ **Admin Access Control** - Role-based admin verification
- 🚀 **FastAPI Integration** - Easy dependency injection patterns

## Quick Start

### 1. Supabase Authentication

```python
from fastapi import FastAPI, Header, HTTPException
from gittielabs_fastapi_auth import SupabaseAuthService

app = FastAPI()
auth_service = SupabaseAuthService(
    supabase_url="https://your-project.supabase.co",
    supabase_service_key="your-service-role-key"
)

@app.get("/api/user/me")
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    token = auth_service.extract_token_from_header(authorization)
    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user
```

### 2. Organization Context

```python
from fastapi import Request
from gittielabs_fastapi_auth import get_organization_id_from_request

@app.get("/api/org/data")
async def get_org_data(request: Request):
    # Extract organization ID from subdomain header or request state
    org_id = get_organization_id_from_request(request)

    # Use org_id to filter data...
    return {"organization_id": org_id}
```

### 3. Admin Access Control

```python
from fastapi import Request
from gittielabs_fastapi_auth import verify_admin_access, AdminRole

@app.get("/api/admin/users")
async def list_users(request: Request):
    # Verify user has admin access
    current_org, accessible_orgs, user = verify_admin_access(
        request,
        required_role=AdminRole.ORG_ADMIN
    )

    # User is verified as admin, proceed with operation
    return {
        "current_org": current_org,
        "accessible_orgs": accessible_orgs,
        "user_email": user.email
    }
```

## Core Components

### Models

```python
from gittielabs_fastapi_auth import AuthUser, UserRole, OrganizationInfo

# AuthUser - Authenticated user with organization context
user = AuthUser(
    id="user-id",
    email="user@example.com",
    organization_id="org-id",
    role=UserRole.ADMIN,
    is_super_admin=False,
    organizations=[{"id": "org-id", "name": "My Org", "role": "admin"}]
)
```

### SupabaseAuthService

Handles JWT validation and user extraction:

```python
service = SupabaseAuthService(
    supabase_url="...",
    supabase_service_key="..."
)

# Validate JWT token
is_valid, payload, error = await service.validate_jwt_token(token)

# Get user from token
user = await service.get_user_from_token(token)

# Extract token from header
token = service.extract_token_from_header("Bearer abc123...")
```

### Organization Context

Extract organization context from requests:

```python
from gittielabs_fastapi_auth import (
    get_organization_id_from_request,
    get_organization_id_from_request_optional,
    extract_subdomain_from_request
)

# Required organization context (raises HTTPException if not found)
org_id = get_organization_id_from_request(request)

# Optional organization context (returns None if not found)
org_id = get_organization_id_from_request_optional(request)

# Extract subdomain from headers
subdomain = extract_subdomain_from_request(request)
```

### Admin Access Control

Verify admin access and get organization context:

```python
from gittielabs_fastapi_auth import (
    verify_admin_access,
    get_admin_organization_context,
    check_organization_admin_access,
    AdminRole
)

# Verify admin access (raises HTTPException if not admin)
current_org, accessible_orgs, user = verify_admin_access(
    request,
    required_role=AdminRole.ORG_ADMIN  # or ORG_OWNER, ORG_BILLING
)

# Get comprehensive admin context
context = get_admin_organization_context(request)
# Returns: {
#   "current_organization_id": "...",
#   "accessible_organizations": ["...", "..."],
#   "is_super_admin": False,
#   "user_id": "...",
#   "user_email": "..."
# }

# Check if user has admin access to specific org
has_access = check_organization_admin_access(request, "org-id")
```

## User Roles

The library defines four user roles with different permission levels:

- `UserRole.VIEWER` - Read-only access
- `UserRole.MEMBER` - Standard member with read/write access
- `UserRole.ADMIN` - Administrative access within organization
- `UserRole.OWNER` - Full ownership and control

Super admins have access to all organizations regardless of role.

## Development

### Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint
ruff check .

# Type check
mypy .
```

## License

MIT © GittieLabs
