"""
JWT-based admin context utilities for role-based admin access control.

This module leverages the existing JWT AuthUser data structure to provide
simple admin access verification without additional database queries.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request
from loguru import logger

from .models import AuthUser


class AdminRole(str, Enum):
    """Admin role levels for access control."""

    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "admin"
    ORG_OWNER = "owner"
    ORG_BILLING = "billing"


class JWTAdminContext:
    """
    JWT-based admin access control using existing AuthUser data.

    Provides methods to verify admin access, check permissions, and
    get organization context from authenticated users.
    """

    @staticmethod
    def verify_admin_access(
        request: Request, required_role: AdminRole = AdminRole.ORG_ADMIN
    ) -> Tuple[str, List[str], AuthUser]:
        """
        Verify admin access using JWT AuthUser data.

        Args:
            request: FastAPI request object
            required_role: Minimum required role for access

        Returns:
            Tuple of (current_org_id, accessible_org_ids, auth_user)

        Raises:
            HTTPException: If user doesn't have required admin access
        """
        # Get authenticated user from request state (set by middleware)
        user: AuthUser = getattr(request.state, "user", None)

        if not user or not user.is_authenticated:
            logger.warning("No authenticated user found in request state")
            raise HTTPException(status_code=401, detail="Authentication required")

        # Super admin has access to everything
        if user.is_super_admin:
            logger.info(f"Super admin access granted for user {user.email}")
            # Get all organizations from user's org list or return current org
            all_org_ids = (
                [org["id"] for org in user.organizations]
                if user.organizations
                else [user.organization_id]
            )
            return user.organization_id, all_org_ids, user

        # Regular users: check admin roles in their organizations
        admin_roles = (
            ["admin", "owner", "billing"]
            if required_role == AdminRole.ORG_ADMIN
            else []
        )
        if required_role == AdminRole.ORG_OWNER:
            admin_roles = ["owner"]
        elif required_role == AdminRole.ORG_BILLING:
            admin_roles = ["owner", "billing"]

        # Get organizations where user has admin access
        admin_org_ids = []
        if user.organizations:
            for org in user.organizations:
                if org.get("role") in admin_roles:
                    admin_org_ids.append(org["id"])
        elif user.role.value in admin_roles and user.organization_id:
            # Fallback to primary org if organizations list not available
            admin_org_ids.append(user.organization_id)

        if not admin_org_ids:
            logger.warning(
                f"User {user.email} has no admin access to any organizations"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Admin access required (minimum role: {required_role.value})",
            )

        # Use current organization if user has admin access there, otherwise use first admin org
        current_org = (
            user.organization_id
            if user.organization_id in admin_org_ids
            else admin_org_ids[0]
        )

        logger.info(
            f"Admin access granted for user {user.email} in {len(admin_org_ids)} organizations"
        )
        return current_org, admin_org_ids, user

    @staticmethod
    def get_admin_organization_context(request: Request) -> Dict[str, Any]:
        """
        Get comprehensive admin organization context from JWT.

        Args:
            request: FastAPI request object

        Returns:
            Dict containing organization context, user roles, and access permissions
        """
        try:
            current_org, accessible_orgs, user = JWTAdminContext.verify_admin_access(
                request
            )

            return {
                "current_organization_id": current_org,
                "accessible_organizations": accessible_orgs,
                "organization_details": user.organizations or [],
                "is_super_admin": user.is_super_admin,
                "user_id": user.id,
                "user_email": user.email,
                "primary_role": user.role.value if user.role else None,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting admin organization context: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to get organization context"
            )

    @staticmethod
    def check_organization_admin_access(
        request: Request, organization_id: str
    ) -> bool:
        """
        Check if current user has admin access to specific organization.

        Args:
            request: FastAPI request object
            organization_id: Organization ID to check

        Returns:
            True if user has admin access, False otherwise
        """
        try:
            _, accessible_orgs, _ = JWTAdminContext.verify_admin_access(request)
            return organization_id in accessible_orgs
        except HTTPException:
            return False

    @staticmethod
    def get_user_admin_organizations(request: Request) -> List[Dict[str, Any]]:
        """
        Get list of organizations where user has admin access.

        Args:
            request: FastAPI request object

        Returns:
            List of organization dictionaries with admin access
        """
        try:
            user: AuthUser = getattr(request.state, "user", None)
            if not user or not user.is_authenticated:
                return []

            if user.is_super_admin:
                return user.organizations or []

            admin_roles = ["admin", "owner", "billing"]
            admin_orgs = []

            if user.organizations:
                for org in user.organizations:
                    if org.get("role") in admin_roles:
                        admin_orgs.append(org)

            return admin_orgs
        except Exception as e:
            logger.error(f"Error getting user admin organizations: {e}")
            return []


# Helper functions for common patterns
def verify_admin_access(
    request: Request, required_role: AdminRole = AdminRole.ORG_ADMIN
) -> Tuple[str, List[str], AuthUser]:
    """
    Convenience function to verify admin access.

    Args:
        request: FastAPI request object
        required_role: Minimum required role for access

    Returns:
        Tuple of (current_org_id, accessible_org_ids, auth_user)

    Raises:
        HTTPException: If user doesn't have required admin access
    """
    return JWTAdminContext.verify_admin_access(request, required_role)


def get_admin_organization_context(request: Request) -> Dict[str, Any]:
    """
    Convenience function to get admin organization context.

    Args:
        request: FastAPI request object

    Returns:
        Dict containing organization context, user roles, and access permissions
    """
    return JWTAdminContext.get_admin_organization_context(request)


def check_organization_admin_access(request: Request, organization_id: str) -> bool:
    """
    Convenience function to check organization admin access.

    Args:
        request: FastAPI request object
        organization_id: Organization ID to check

    Returns:
        True if user has admin access, False otherwise
    """
    return JWTAdminContext.check_organization_admin_access(request, organization_id)
