# Admin Dashboard Example

This example demonstrates role-based access control and admin functionality using `@gittielabs/nextjs-fastapi-auth`.

## Status: Coming Soon

This example is planned to demonstrate:
- Role-based route protection (admin, owner, member roles)
- Admin-only UI components and pages
- User management interface
- Permission-based feature access
- Super admin vs organization admin differentiation

## Features to be Implemented

### Frontend (Next.js)
- Admin layout with navigation
- User management page (list, create, update, delete)
- Role assignment interface
- Protected admin routes
- Permission-based UI rendering

### Backend (FastAPI)
- Admin access verification endpoints
- User CRUD operations with role checks
- Organization admin context
- Super admin capabilities
- Audit logging

## Preview Structure

```
admin-dashboard/
├── frontend/
│   ├── app/
│   │   ├── admin/
│   │   │   ├── layout.tsx           # Admin layout
│   │   │   ├── users/page.tsx       # User management
│   │   │   ├── roles/page.tsx       # Role management
│   │   │   └── settings/page.tsx    # Admin settings
│   │   └── components/
│   │       ├── admin-nav.tsx
│   │       └── role-badge.tsx
│   └── middleware.ts
│
└── backend/
    ├── dependencies/
    │   └── admin.py                 # Admin access checks
    ├── routers/
    │   ├── admin_users.py           # User management endpoints
    │   └── admin_roles.py           # Role management endpoints
    └── main.py
```

## Key Concepts

### Admin Route Protection

Frontend protects admin routes:

```typescript
// Only admins can access
const auth = validateAdminAuth(request)
if (auth.error) return auth.error
```

### Role-Based Access

Backend verifies specific admin roles:

```python
@app.get("/api/v1/admin/users")
async def list_users(request: Request):
    # Verify user has admin access
    current_org, accessible_orgs, user = verify_admin_access(
        request,
        required_role=AdminRole.ORG_ADMIN  # or ORG_OWNER
    )

    # User is verified as admin
    return {"users": [...]}
```

### Permission Checks

UI components adapt to user permissions:

```typescript
{user.role === 'admin' && (
  <AdminPanel />
)}

{user.is_super_admin && (
  <SuperAdminTools />
)}
```

## Admin Roles Hierarchy

The library defines several admin roles with different permission levels:

1. **Super Admin** (`is_super_admin: true`)
   - Access to all organizations
   - System-wide administration
   - Can manage any resource

2. **Organization Owner** (`AdminRole.ORG_OWNER`)
   - Full control within their organization
   - Can manage members and roles
   - Billing and subscription management

3. **Organization Admin** (`AdminRole.ORG_ADMIN`)
   - Administrative access within organization
   - Can manage most resources
   - Limited billing access

4. **Organization Billing** (`AdminRole.ORG_BILLING`)
   - Billing and subscription management
   - Limited to financial operations

## Example Use Cases

### User Management
- List all users in organization
- Create new users with specific roles
- Update user permissions
- Deactivate/remove users

### Access Control
- View and modify user roles
- Set organization-level permissions
- Configure feature flags per organization

### Audit Logging
- Track admin actions
- View user activity logs
- Export audit reports

## For Now

Please refer to the [basic example](../basic-nextjs-fastapi/) for foundational authentication.

The admin dashboard will build on those concepts with role-based access control and admin-specific features.

## Coming Next

1. Admin layout and navigation
2. User management CRUD interface
3. Role assignment and permissions
4. Activity logging and audit trails
5. Super admin tools and organization switching
