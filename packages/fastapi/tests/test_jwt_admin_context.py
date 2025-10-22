"""
Unit tests for JWT-based admin context utilities.

Tests the JWTAdminContext class and helper functions for role-based
admin access control using JWT AuthUser data.
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException, Request

from gittielabs_fastapi_auth.jwt_admin_context import (
    JWTAdminContext,
    AdminRole,
    verify_admin_access,
    get_admin_organization_context,
    check_organization_admin_access,
)
from gittielabs_fastapi_auth.models import AuthUser, UserRole


def create_mock_request_with_user(user: AuthUser) -> Request:
    """Helper to create mock request with user in state"""
    mock_request = Mock(spec=Request)
    mock_request.state = Mock()
    mock_request.state.user = user
    return mock_request


def create_mock_request_without_user() -> Request:
    """Helper to create mock request without user"""
    mock_request = Mock(spec=Request)
    mock_request.state = Mock(spec=[])  # No user attribute
    return mock_request


class TestAdminRole:
    """Test AdminRole enum"""

    def test_admin_role_values(self):
        """Test admin role enum values"""
        assert AdminRole.SUPER_ADMIN.value == "super_admin"
        assert AdminRole.ORG_ADMIN.value == "admin"
        assert AdminRole.ORG_OWNER.value == "owner"
        assert AdminRole.ORG_BILLING.value == "billing"


class TestJWTAdminContext:
    """Test JWTAdminContext class methods"""

    def test_verify_admin_access_super_admin(self, test_super_admin_user):
        """Test admin access verification for super admin"""
        mock_request = create_mock_request_with_user(test_super_admin_user)

        current_org, accessible_orgs, user = JWTAdminContext.verify_admin_access(
            mock_request
        )

        assert current_org == "org-456"
        assert "org-456" in accessible_orgs
        assert "org-789" in accessible_orgs
        assert user == test_super_admin_user
        assert user.is_super_admin is True

    def test_verify_admin_access_org_admin(self, test_admin_user):
        """Test admin access verification for org admin"""
        mock_request = create_mock_request_with_user(test_admin_user)

        current_org, accessible_orgs, user = JWTAdminContext.verify_admin_access(
            mock_request, AdminRole.ORG_ADMIN
        )

        assert current_org == "org-456"
        assert accessible_orgs == ["org-456"]  # Only admin in org-456
        assert user == test_admin_user

    def test_verify_admin_access_owner(self, test_owner_user):
        """Test admin access verification for owner"""
        mock_request = create_mock_request_with_user(test_owner_user)

        current_org, accessible_orgs, user = JWTAdminContext.verify_admin_access(
            mock_request, AdminRole.ORG_OWNER
        )

        assert current_org == "org-456"
        assert accessible_orgs == ["org-456"]
        assert user == test_owner_user

    def test_verify_admin_access_member_fails(self, test_member_user):
        """Test that member users cannot access admin endpoints"""
        mock_request = create_mock_request_with_user(test_member_user)

        with pytest.raises(HTTPException) as exc_info:
            JWTAdminContext.verify_admin_access(mock_request)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    def test_verify_admin_access_no_user(self):
        """Test admin access verification with no authenticated user"""
        mock_request = create_mock_request_without_user()

        with pytest.raises(HTTPException) as exc_info:
            JWTAdminContext.verify_admin_access(mock_request)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    def test_verify_admin_access_not_authenticated(self):
        """Test admin access with unauthenticated user"""
        user = AuthUser(
            id="test-123",
            email="test@example.com",
            organization_id="org-456",
            role=UserRole.ADMIN,
            is_authenticated=False,  # Not authenticated
        )
        mock_request = create_mock_request_with_user(user)

        with pytest.raises(HTTPException) as exc_info:
            JWTAdminContext.verify_admin_access(mock_request)

        assert exc_info.value.status_code == 401

    def test_verify_admin_access_owner_requirement(self, test_admin_user):
        """Test that admin user fails owner-level requirement"""
        mock_request = create_mock_request_with_user(test_admin_user)

        with pytest.raises(HTTPException) as exc_info:
            JWTAdminContext.verify_admin_access(mock_request, AdminRole.ORG_OWNER)

        assert exc_info.value.status_code == 403
        assert "owner" in exc_info.value.detail

    def test_verify_admin_access_billing_role(self):
        """Test billing role admin access"""
        user = AuthUser(
            id="billing-123",
            email="billing@example.com",
            organization_id="org-456",
            role=UserRole.MEMBER,
            is_authenticated=True,
            organizations=[
                {"id": "org-456", "name": "Test Org", "role": "billing"},
            ],
        )
        mock_request = create_mock_request_with_user(user)

        current_org, accessible_orgs, _ = JWTAdminContext.verify_admin_access(
            mock_request, AdminRole.ORG_BILLING
        )

        assert current_org == "org-456"
        assert "org-456" in accessible_orgs

    def test_verify_admin_access_multiple_admin_orgs(self):
        """Test user with admin access to multiple orgs"""
        user = AuthUser(
            id="multi-admin-123",
            email="multi@example.com",
            organization_id="org-456",
            role=UserRole.ADMIN,
            is_authenticated=True,
            organizations=[
                {"id": "org-456", "name": "First Org", "role": "admin"},
                {"id": "org-789", "name": "Second Org", "role": "owner"},
                {"id": "org-999", "name": "Third Org", "role": "member"},
            ],
        )
        mock_request = create_mock_request_with_user(user)

        current_org, accessible_orgs, _ = JWTAdminContext.verify_admin_access(
            mock_request
        )

        assert current_org == "org-456"  # User's current org
        assert len(accessible_orgs) == 2  # admin in org-456 and owner in org-789
        assert "org-456" in accessible_orgs
        assert "org-789" in accessible_orgs
        assert "org-999" not in accessible_orgs  # Member only

    def test_verify_admin_access_fallback_to_primary_org(self):
        """Test fallback to primary org when organizations list not available"""
        user = AuthUser(
            id="admin-123",
            email="admin@example.com",
            organization_id="org-456",
            role=UserRole.ADMIN,
            is_authenticated=True,
            organizations=[],  # Empty organizations list
        )
        mock_request = create_mock_request_with_user(user)

        current_org, accessible_orgs, _ = JWTAdminContext.verify_admin_access(
            mock_request
        )

        assert current_org == "org-456"
        assert accessible_orgs == ["org-456"]

    def test_verify_admin_access_uses_first_admin_org_if_not_current(self):
        """Test that first admin org is used if current org has no admin access"""
        user = AuthUser(
            id="admin-123",
            email="admin@example.com",
            organization_id="org-999",  # Member only here
            role=UserRole.MEMBER,
            is_authenticated=True,
            organizations=[
                {"id": "org-456", "name": "Admin Org", "role": "admin"},
                {"id": "org-789", "name": "Owner Org", "role": "owner"},
                {"id": "org-999", "name": "Member Org", "role": "member"},
            ],
        )
        mock_request = create_mock_request_with_user(user)

        current_org, accessible_orgs, _ = JWTAdminContext.verify_admin_access(
            mock_request
        )

        assert current_org == "org-456"  # First admin org
        assert len(accessible_orgs) == 2

    def test_get_admin_organization_context_success(self, test_admin_user):
        """Test getting comprehensive admin organization context"""
        mock_request = create_mock_request_with_user(test_admin_user)

        context = JWTAdminContext.get_admin_organization_context(mock_request)

        assert context["current_organization_id"] == "org-456"
        assert "org-456" in context["accessible_organizations"]
        assert context["is_super_admin"] is False
        assert context["user_id"] == "admin-user-123"
        assert context["user_email"] == "admin@example.com"
        assert context["primary_role"] == "admin"
        assert len(context["organization_details"]) == 2

    def test_get_admin_organization_context_super_admin(self, test_super_admin_user):
        """Test admin context for super admin"""
        mock_request = create_mock_request_with_user(test_super_admin_user)

        context = JWTAdminContext.get_admin_organization_context(mock_request)

        assert context["is_super_admin"] is True
        assert len(context["accessible_organizations"]) == 2

    def test_get_admin_organization_context_no_user(self):
        """Test admin context with no user"""
        mock_request = create_mock_request_without_user()

        with pytest.raises(HTTPException) as exc_info:
            JWTAdminContext.get_admin_organization_context(mock_request)

        assert exc_info.value.status_code == 401

    def test_get_admin_organization_context_member_fails(self, test_member_user):
        """Test that member cannot get admin context"""
        mock_request = create_mock_request_with_user(test_member_user)

        with pytest.raises(HTTPException) as exc_info:
            JWTAdminContext.get_admin_organization_context(mock_request)

        assert exc_info.value.status_code == 403

    def test_check_organization_admin_access_has_access(self, test_admin_user):
        """Test checking org admin access when user has access"""
        mock_request = create_mock_request_with_user(test_admin_user)

        has_access = JWTAdminContext.check_organization_admin_access(
            mock_request, "org-456"
        )

        assert has_access is True

    def test_check_organization_admin_access_no_access(self, test_admin_user):
        """Test checking org admin access when user lacks access"""
        mock_request = create_mock_request_with_user(test_admin_user)

        has_access = JWTAdminContext.check_organization_admin_access(
            mock_request, "org-999"
        )

        assert has_access is False

    def test_check_organization_admin_access_super_admin(self, test_super_admin_user):
        """Test super admin has access to all orgs"""
        mock_request = create_mock_request_with_user(test_super_admin_user)

        has_access_456 = JWTAdminContext.check_organization_admin_access(
            mock_request, "org-456"
        )
        has_access_789 = JWTAdminContext.check_organization_admin_access(
            mock_request, "org-789"
        )

        assert has_access_456 is True
        assert has_access_789 is True

    def test_check_organization_admin_access_no_user(self):
        """Test org access check with no user returns False"""
        mock_request = create_mock_request_without_user()

        has_access = JWTAdminContext.check_organization_admin_access(
            mock_request, "org-456"
        )

        assert has_access is False

    def test_get_user_admin_organizations(self, test_admin_user):
        """Test getting list of user's admin organizations"""
        mock_request = create_mock_request_with_user(test_admin_user)

        admin_orgs = JWTAdminContext.get_user_admin_organizations(mock_request)

        assert len(admin_orgs) == 1
        assert admin_orgs[0]["id"] == "org-456"
        assert admin_orgs[0]["role"] == "admin"

    def test_get_user_admin_organizations_super_admin(self, test_super_admin_user):
        """Test super admin gets all organizations"""
        mock_request = create_mock_request_with_user(test_super_admin_user)

        admin_orgs = JWTAdminContext.get_user_admin_organizations(mock_request)

        assert len(admin_orgs) == 2

    def test_get_user_admin_organizations_member(self, test_member_user):
        """Test member user gets empty list"""
        mock_request = create_mock_request_with_user(test_member_user)

        admin_orgs = JWTAdminContext.get_user_admin_organizations(mock_request)

        assert admin_orgs == []

    def test_get_user_admin_organizations_no_user(self):
        """Test getting admin orgs with no user returns empty list"""
        mock_request = create_mock_request_without_user()

        admin_orgs = JWTAdminContext.get_user_admin_organizations(mock_request)

        assert admin_orgs == []

    def test_get_user_admin_organizations_mixed_roles(self):
        """Test user with mixed roles across organizations"""
        user = AuthUser(
            id="mixed-123",
            email="mixed@example.com",
            organization_id="org-456",
            role=UserRole.MEMBER,
            is_authenticated=True,
            organizations=[
                {"id": "org-456", "name": "Admin Org", "role": "admin"},
                {"id": "org-789", "name": "Member Org", "role": "member"},
                {"id": "org-999", "name": "Owner Org", "role": "owner"},
                {"id": "org-111", "name": "Billing Org", "role": "billing"},
            ],
        )
        mock_request = create_mock_request_with_user(user)

        admin_orgs = JWTAdminContext.get_user_admin_organizations(mock_request)

        assert len(admin_orgs) == 3  # admin, owner, billing
        org_ids = [org["id"] for org in admin_orgs]
        assert "org-456" in org_ids
        assert "org-999" in org_ids
        assert "org-111" in org_ids
        assert "org-789" not in org_ids  # Member only


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_verify_admin_access_convenience(self, test_admin_user):
        """Test verify_admin_access convenience function"""
        mock_request = create_mock_request_with_user(test_admin_user)

        current_org, accessible_orgs, user = verify_admin_access(mock_request)

        assert current_org == "org-456"
        assert "org-456" in accessible_orgs
        assert user == test_admin_user

    def test_verify_admin_access_convenience_with_role(self, test_owner_user):
        """Test convenience function with specific role requirement"""
        mock_request = create_mock_request_with_user(test_owner_user)

        current_org, accessible_orgs, user = verify_admin_access(
            mock_request, AdminRole.ORG_OWNER
        )

        assert current_org == "org-456"
        assert user == test_owner_user

    def test_get_admin_organization_context_convenience(self, test_admin_user):
        """Test get_admin_organization_context convenience function"""
        mock_request = create_mock_request_with_user(test_admin_user)

        context = get_admin_organization_context(mock_request)

        assert context["user_id"] == "admin-user-123"
        assert context["current_organization_id"] == "org-456"

    def test_check_organization_admin_access_convenience(self, test_admin_user):
        """Test check_organization_admin_access convenience function"""
        mock_request = create_mock_request_with_user(test_admin_user)

        has_access = check_organization_admin_access(mock_request, "org-456")

        assert has_access is True

    def test_check_organization_admin_access_convenience_no_access(
        self, test_admin_user
    ):
        """Test convenience function returns False for no access"""
        mock_request = create_mock_request_with_user(test_admin_user)

        has_access = check_organization_admin_access(mock_request, "org-999")

        assert has_access is False


class TestEdgeCasesAndSecurity:
    """Test edge cases and security scenarios"""

    def test_super_admin_with_empty_organizations(self):
        """Test super admin with empty organizations list"""
        user = AuthUser(
            id="super-123",
            email="super@example.com",
            organization_id="org-456",
            role=UserRole.ADMIN,
            is_authenticated=True,
            is_super_admin=True,
            organizations=[],  # Empty
        )
        mock_request = create_mock_request_with_user(user)

        current_org, accessible_orgs, _ = JWTAdminContext.verify_admin_access(
            mock_request
        )

        assert current_org == "org-456"
        assert accessible_orgs == ["org-456"]

    def test_admin_with_none_organization_id(self):
        """Test admin with None as organization_id"""
        user = AuthUser(
            id="admin-123",
            email="admin@example.com",
            organization_id=None,
            role=UserRole.ADMIN,
            is_authenticated=True,
            organizations=[
                {"id": "org-456", "name": "Test Org", "role": "admin"},
            ],
        )
        mock_request = create_mock_request_with_user(user)

        current_org, accessible_orgs, _ = JWTAdminContext.verify_admin_access(
            mock_request
        )

        # Should use first admin org
        assert current_org == "org-456"
        assert "org-456" in accessible_orgs

    def test_billing_role_with_owner_requirement_succeeds(self):
        """Test that owner requirement also accepts owner role"""
        user = AuthUser(
            id="owner-123",
            email="owner@example.com",
            organization_id="org-456",
            role=UserRole.OWNER,
            is_authenticated=True,
            organizations=[
                {"id": "org-456", "name": "Test Org", "role": "owner"},
            ],
        )
        mock_request = create_mock_request_with_user(user)

        current_org, accessible_orgs, _ = JWTAdminContext.verify_admin_access(
            mock_request, AdminRole.ORG_BILLING
        )

        assert current_org == "org-456"

    def test_case_sensitivity_in_roles(self):
        """Test that role matching is case-sensitive"""
        user = AuthUser(
            id="user-123",
            email="user@example.com",
            organization_id="org-456",
            role=UserRole.MEMBER,
            is_authenticated=True,
            organizations=[
                {"id": "org-456", "name": "Test Org", "role": "Admin"},  # Capital A
            ],
        )
        mock_request = create_mock_request_with_user(user)

        with pytest.raises(HTTPException) as exc_info:
            JWTAdminContext.verify_admin_access(mock_request)

        assert exc_info.value.status_code == 403

    def test_special_characters_in_organization_id(self):
        """Test organization IDs with special characters"""
        user = AuthUser(
            id="admin-123",
            email="admin@example.com",
            organization_id="org-456-test-uuid-abc",
            role=UserRole.ADMIN,
            is_authenticated=True,
            organizations=[
                {"id": "org-456-test-uuid-abc", "name": "Test", "role": "admin"},
            ],
        )
        mock_request = create_mock_request_with_user(user)

        has_access = JWTAdminContext.check_organization_admin_access(
            mock_request, "org-456-test-uuid-abc"
        )

        assert has_access is True
