"""
Organization context utilities for multi-tenant architecture.

This module provides utilities to extract organization context from requests
for subdomain-based multi-tenancy.
"""

from typing import Optional

from fastapi import HTTPException, Request
from loguru import logger


class OrganizationContext:
    """
    Utility class for managing organization context in requests.

    Provides methods to extract organization IDs from subdomain headers,
    host headers, or request state set by middleware.
    """

    @staticmethod
    def get_organization_id_from_request(request: Request) -> str:
        """
        Get organization ID from request context.

        Checks multiple sources in order:
        1. request.state.organization_id (set by middleware)
        2. x-organization-subdomain header
        3. Extracted from Host header

        Args:
            request: FastAPI request object

        Returns:
            Organization ID string

        Raises:
            HTTPException: If no organization context is available
        """
        logger.debug(
            f"[ORG_CONTEXT] Getting organization ID from request to {request.url.path}"
        )

        # First try to get from middleware-set context
        org_id = getattr(request.state, "organization_id", None)
        logger.debug(f"[ORG_CONTEXT] Middleware-set org_id: {org_id}")

        if org_id:
            logger.debug(
                f"[ORG_CONTEXT] Found organization ID from request state: {org_id}"
            )
            return str(org_id)

        # Check for super admin API key type for logging
        api_key_type = getattr(request.state, "api_key_type", None)
        logger.debug(f"[ORG_CONTEXT] API key type: {api_key_type}")

        if api_key_type == "super_admin":
            logger.debug(
                "[ORG_CONTEXT] Super admin request - continuing to look for subdomain context"
            )

        # For subdomain-based authentication, check subdomain header
        subdomain_header = request.headers.get("x-organization-subdomain")
        logger.debug(f"[ORG_CONTEXT] x-organization-subdomain header: {subdomain_header}")

        # Also check if subdomain can be extracted from Host header as fallback
        host_header = request.headers.get("host", "")
        logger.debug(f"[ORG_CONTEXT] Host header: {host_header}")

        # If no subdomain header, try to extract from Host header
        if not subdomain_header and host_header:
            if ".localhost" in host_header or ".govreadyai.app" in host_header:
                subdomain_from_host = host_header.split(".")[0]
                if subdomain_from_host not in ["www", "localhost"]:
                    subdomain_header = subdomain_from_host
                    logger.debug(
                        f"[ORG_CONTEXT] Extracted subdomain from Host header: {subdomain_header}"
                    )

        if subdomain_header:
            logger.debug(
                f"[ORG_CONTEXT] Subdomain detected: {subdomain_header} "
                f"- should be resolved by middleware or database lookup"
            )
            # NOTE: Actual subdomain->org_id resolution should happen in middleware
            # or via a custom database lookup function. This library provides
            # the utilities, but the app needs to implement the actual lookup.
            raise HTTPException(
                status_code=400,
                detail=f"Subdomain '{subdomain_header}' detected but not resolved to organization ID. "
                f"Ensure your middleware or database lookup is properly configured.",
            )

        # If no organization context is available, this is an error
        logger.error("[ORG_CONTEXT] No organization context available in request")
        raise HTTPException(
            status_code=400,
            detail="No organization context available - ensure proper authentication",
        )

    @staticmethod
    def get_organization_id_from_request_optional(
        request: Request,
    ) -> Optional[str]:
        """
        Get organization ID from request context, returning None if not available.

        Args:
            request: FastAPI request object

        Returns:
            Organization ID string or None
        """
        try:
            return OrganizationContext.get_organization_id_from_request(request)
        except HTTPException:
            return None

    @staticmethod
    def extract_subdomain_from_request(request: Request) -> Optional[str]:
        """
        Extract subdomain from request headers.

        Checks x-organization-subdomain header and Host header.

        Args:
            request: FastAPI request object

        Returns:
            Subdomain string or None
        """
        # Check subdomain header first
        subdomain = request.headers.get("x-organization-subdomain")
        if subdomain:
            return subdomain

        # Try to extract from Host header
        host_header = request.headers.get("host", "")
        if ".localhost" in host_header or ".govreadyai.app" in host_header:
            subdomain_from_host = host_header.split(".")[0]
            if subdomain_from_host not in ["www", "localhost"]:
                return subdomain_from_host

        return None


# Helper functions for common patterns
def get_organization_id_from_request(request: Request) -> str:
    """
    Convenience function to get organization ID from request.

    Args:
        request: FastAPI request object

    Returns:
        Organization ID string

    Raises:
        HTTPException: If no organization context is available
    """
    return OrganizationContext.get_organization_id_from_request(request)


def get_organization_id_from_request_optional(request: Request) -> Optional[str]:
    """
    Convenience function to optionally get organization ID from request.

    Args:
        request: FastAPI request object

    Returns:
        Organization ID string or None
    """
    return OrganizationContext.get_organization_id_from_request_optional(request)


def extract_subdomain_from_request(request: Request) -> Optional[str]:
    """
    Convenience function to extract subdomain from request.

    Args:
        request: FastAPI request object

    Returns:
        Subdomain string or None
    """
    return OrganizationContext.extract_subdomain_from_request(request)
