# Multi-Tenant Subdomains Example

This example demonstrates multi-tenant architecture with subdomain-based routing using `@gittielabs/nextjs-fastapi-auth`.

## Status: Coming Soon

This example is planned to demonstrate:
- Organization-based subdomain routing (e.g., `acme.example.com`, `corp.example.com`)
- Automatic organization context extraction from subdomains
- Organization-scoped data queries
- Tenant isolation and security
- Organization switcher UI

## Features to be Implemented

### Frontend (Next.js)
- Subdomain middleware configuration
- Organization context provider
- Multi-org switcher component
- Organization-specific pages and layouts

### Backend (FastAPI)
- Organization context dependency injection
- Tenant-scoped database queries
- Cross-origin subdomain handling
- Organization membership validation

## Preview Structure

```
multi-tenant-subdomains/
├── frontend/
│   ├── app/
│   │   ├── [org]/                   # Organization-scoped routes
│   │   │   ├── dashboard/page.tsx
│   │   │   └── settings/page.tsx
│   │   └── components/
│   │       └── org-switcher.tsx
│   └── middleware.ts                # Subdomain routing
│
└── backend/
    ├── dependencies/
    │   └── organization.py          # Org context injection
    └── main.py
```

## Key Concepts

### Subdomain Routing

Extract organization context from subdomains:

```typescript
// Middleware extracts subdomain
// acme.example.com -> org: "acme"
const subdomain = extractSubdomainFromRequest(request)
```

### Organization Context

Backend validates and provides organization context:

```python
@app.get("/api/v1/org/data")
async def get_org_data(
    org_id: str = Depends(require_organization)
):
    # org_id automatically extracted and validated
    return {"organization_id": org_id}
```

### Tenant Isolation

Data is automatically scoped to the organization:

```python
# Query filtered by organization
data = db.query(Model).filter(
    Model.organization_id == org_id
).all()
```

## For Now

Please refer to the [basic example](../basic-nextjs-fastapi/) for a working implementation of the core authentication features.

The multi-tenant example will build on those concepts with organization-specific routing and data scoping.

## Coming Next

1. Local development with subdomain testing
2. Organization membership database schema
3. Organization switcher UI component
4. Tenant-scoped API endpoints
5. Cross-subdomain session handling
