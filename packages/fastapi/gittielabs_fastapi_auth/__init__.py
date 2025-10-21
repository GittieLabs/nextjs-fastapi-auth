"""
@gittielabs/nextjs-fastapi-auth - FastAPI Package

Authentication and authorization library for Next.js + FastAPI applications
with Supabase authentication.

This package provides utilities for:
- JWT token validation and user extraction
- Organization context management (multi-tenancy)
- Admin role-based access control
- Supabase authentication integration
"""

__version__ = "0.1.0"

# Re-export models
from .models import (
    AuthMode,
    AuthToken,
    AuthUser,
    CreateLegacyUser,
    OrganizationInfo,
    UserRole,
)

# Re-export Supabase auth service
from .supabase_auth import SupabaseAuthService, validate_supabase_jwt

# Re-export organization context utilities
from .organization_context import (
    OrganizationContext,
    extract_subdomain_from_request,
    get_organization_id_from_request,
    get_organization_id_from_request_optional,
)

# Re-export JWT admin context utilities
from .jwt_admin_context import (
    AdminRole,
    JWTAdminContext,
    check_organization_admin_access,
    get_admin_organization_context,
    verify_admin_access,
)

__all__ = [
    # Version
    "__version__",
    # Models
    "AuthMode",
    "AuthToken",
    "AuthUser",
    "CreateLegacyUser",
    "OrganizationInfo",
    "UserRole",
    # Supabase Auth
    "SupabaseAuthService",
    "validate_supabase_jwt",
    # Organization Context
    "OrganizationContext",
    "extract_subdomain_from_request",
    "get_organization_id_from_request",
    "get_organization_id_from_request_optional",
    # Admin Context
    "AdminRole",
    "JWTAdminContext",
    "check_organization_admin_access",
    "get_admin_organization_context",
    "verify_admin_access",
]
