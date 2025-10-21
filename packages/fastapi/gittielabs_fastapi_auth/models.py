"""
Authentication models and data structures.

Provides Pydantic models for users, organizations, tokens, and auth modes
in Next.js + FastAPI applications with Supabase authentication.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles within an organization."""

    VIEWER = "viewer"
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class AuthUser(BaseModel):
    """
    Authenticated user model that works for both legacy and auth modes.

    Attributes:
        id: User ID from Supabase
        email: User email address
        organization_id: Current/primary organization ID
        role: User role in current organization
        first_name: User's first name
        last_name: User's last name
        avatar_url: User's avatar URL
        is_authenticated: Whether user is authenticated
        is_legacy_user: Whether this is a legacy (default) user
        is_super_admin: Whether user has super admin privileges
        organizations: List of organizations user belongs to
        session_id: Session/token ID
        expires_at: When the session expires
    """

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email address")

    # Organization context
    organization_id: Optional[str] = Field(None, description="Current organization ID")
    role: UserRole = Field(default=UserRole.MEMBER, description="User role in organization")

    # User details
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    avatar_url: Optional[str] = Field(None, description="User's avatar URL")

    # Authentication context
    is_authenticated: bool = Field(default=True, description="Whether user is authenticated")
    is_legacy_user: bool = Field(
        default=False, description="Whether this is a legacy (default) user"
    )
    is_super_admin: bool = Field(
        default=False, description="Whether user has super admin privileges"
    )

    # Organization memberships (for multi-org users)
    organizations: List[Dict[str, str]] = Field(
        default_factory=list, description="List of organizations user belongs to"
    )

    # Session information
    session_id: Optional[str] = Field(None, description="Session/token ID")
    expires_at: Optional[datetime] = Field(None, description="When the session expires")

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [UserRole.ADMIN, UserRole.OWNER] or self.is_super_admin

    @property
    def is_owner(self) -> bool:
        """Check if user is organization owner."""
        return self.role == UserRole.OWNER or self.is_super_admin

    def can_access_organization(self, org_id: str) -> bool:
        """
        Check if user can access a specific organization.

        Args:
            org_id: Organization ID to check

        Returns:
            True if user has access, False otherwise
        """
        if self.is_super_admin:
            return True

        if self.organization_id == org_id:
            return True

        # Check if user is member of other organizations
        return any(org.get("id") == org_id for org in self.organizations)

    def has_permission(self, permission: str, org_id: Optional[str] = None) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission: Permission to check (read, write, delete, admin, owner)
            org_id: Optional organization ID to check permission for

        Returns:
            True if user has permission, False otherwise
        """
        # Super admin has all permissions
        if self.is_super_admin:
            return True

        # Check organization access first
        if org_id and not self.can_access_organization(org_id):
            return False

        # Role-based permissions
        if permission in ["read", "view"]:
            return True  # All authenticated users can read

        if permission in ["write", "create", "update"]:
            return self.role in [UserRole.MEMBER, UserRole.ADMIN, UserRole.OWNER]

        if permission in ["delete", "admin"]:
            return self.role in [UserRole.ADMIN, UserRole.OWNER]

        if permission == "owner":
            return self.role == UserRole.OWNER

        return False


class AuthToken(BaseModel):
    """Authentication token model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")

    # User information embedded in token
    user: AuthUser = Field(..., description="User information")


class AuthMode(BaseModel):
    """Authentication mode information for API clients."""

    auth_required: bool = Field(..., description="Whether authentication is required")
    mode: str = Field(..., description="Authentication mode (legacy or authentication)")
    supports_registration: bool = Field(
        default=False, description="Whether new user registration is enabled"
    )
    supports_social_login: bool = Field(
        default=False, description="Whether social login is available"
    )

    # Login URLs (if auth required)
    login_url: Optional[str] = Field(None, description="Login page URL")
    signup_url: Optional[str] = Field(None, description="Signup page URL")

    # Default organization info (for legacy mode)
    default_organization: Optional[Dict[str, str]] = Field(
        None, description="Default organization info"
    )


class OrganizationInfo(BaseModel):
    """Organization information model."""

    id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Organization name")
    subdomain: str = Field(..., description="Organization subdomain")

    # User's role in this organization
    user_role: UserRole = Field(..., description="User's role in this organization")

    # Organization settings
    settings: Dict = Field(default_factory=dict, description="Organization settings")

    # Membership info
    joined_at: Optional[datetime] = Field(None, description="When user joined organization")
    invited_by: Optional[str] = Field(None, description="Who invited the user")


class CreateLegacyUser(BaseModel):
    """Model for creating a legacy user."""

    organization_id: str = Field(..., description="Organization ID to assign user to")
    email: str = Field(default="user@legacy.com", description="Email for legacy user")
    role: UserRole = Field(default=UserRole.MEMBER, description="Role to assign")

    # Optional user details
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
