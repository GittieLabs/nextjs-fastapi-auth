"""
Pytest configuration and fixtures for FastAPI package tests
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from fastapi.datastructures import Headers


def create_test_jwt_payload(
    sub: str = "test-user-123",
    email: str = "test@example.com",
    role: str = "member",
    is_super_admin: bool = False,
    exp: int = None,
) -> Dict[str, Any]:
    """Create a test JWT payload"""
    if exp is None:
        exp = int((datetime.now(timezone.utc).timestamp())) + 3600  # 1 hour from now

    return {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "exp": exp,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": "https://test.supabase.co/auth/v1",
        "user_metadata": {
            "role": role,
            "is_super_admin": is_super_admin,
        },
        "app_metadata": {},
    }


def create_test_jwt_token(payload: Dict[str, Any] = None) -> str:
    """Create a test JWT token (not cryptographically valid)"""
    import json
    import base64

    if payload is None:
        payload = create_test_jwt_payload()

    # Create header
    header = {"alg": "HS256", "typ": "JWT"}
    header_encoded = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip("=")

    # Create payload
    payload_encoded = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")

    # Create signature (fake)
    signature = "test-signature"

    return f"{header_encoded}.{payload_encoded}.{signature}"


@pytest.fixture
def sample_jwt_payload():
    """Fixture providing a sample JWT payload"""
    return create_test_jwt_payload()


@pytest.fixture
def sample_jwt_token(sample_jwt_payload):
    """Fixture providing a sample JWT token"""
    return create_test_jwt_token(sample_jwt_payload)


@pytest.fixture
def admin_jwt_payload():
    """Fixture providing an admin JWT payload"""
    return create_test_jwt_payload(
        sub="admin-user-456",
        email="admin@example.com",
        role="admin",
    )


@pytest.fixture
def admin_jwt_token(admin_jwt_payload):
    """Fixture providing an admin JWT token"""
    return create_test_jwt_token(admin_jwt_payload)


@pytest.fixture
def super_admin_jwt_payload():
    """Fixture providing a super admin JWT payload"""
    return create_test_jwt_payload(
        sub="super-admin-789",
        email="super@example.com",
        role="admin",
        is_super_admin=True,
    )


@pytest.fixture
def super_admin_jwt_token(super_admin_jwt_payload):
    """Fixture providing a super admin JWT token"""
    return create_test_jwt_token(super_admin_jwt_payload)


@pytest.fixture
def expired_jwt_payload():
    """Fixture providing an expired JWT payload"""
    return create_test_jwt_payload(
        exp=int(datetime.now(timezone.utc).timestamp()) - 3600  # 1 hour ago
    )


@pytest.fixture
def expired_jwt_token(expired_jwt_payload):
    """Fixture providing an expired JWT token"""
    return create_test_jwt_token(expired_jwt_payload)


@pytest.fixture
def mock_supabase_client():
    """Fixture providing a mock Supabase client"""
    client = Mock()
    client.auth = Mock()
    client.auth.get_user = AsyncMock()
    client.auth.sign_in_with_password = AsyncMock()
    client.table = Mock()
    return client


@pytest.fixture
def mock_request_with_token(sample_jwt_token):
    """Fixture providing a mock FastAPI request with authorization token"""
    mock_request = Mock(spec=Request)
    mock_request.headers = Headers({
        "authorization": f"Bearer {sample_jwt_token}",
        "content-type": "application/json",
    })
    mock_request.url = Mock()
    mock_request.url.path = "/api/v1/test"
    mock_request.state = Mock()
    return mock_request


@pytest.fixture
def mock_request_with_subdomain(sample_jwt_token):
    """Fixture providing a mock request with subdomain header"""
    mock_request = Mock(spec=Request)
    mock_request.headers = Headers({
        "authorization": f"Bearer {sample_jwt_token}",
        "x-organization-subdomain": "ktg",
        "host": "ktg.localhost:3000",
    })
    mock_request.url = Mock()
    mock_request.url.path = "/api/v1/test"
    mock_request.state = Mock()
    mock_request.state.organization_id = "org-123"
    return mock_request


@pytest.fixture
def mock_request_no_auth():
    """Fixture providing a mock request without authorization"""
    mock_request = Mock(spec=Request)
    mock_request.headers = Headers({
        "content-type": "application/json",
    })
    mock_request.url = Mock()
    mock_request.url.path = "/api/v1/test"
    mock_request.state = Mock()
    return mock_request


@pytest.fixture
def test_organization_data():
    """Fixture providing test organization data"""
    return {
        "id": "org-123",
        "name": "Test Organization",
        "subdomain": "ktg",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_user_data():
    """Fixture providing test user data"""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "member",
        "organization_id": "org-123",
    }


@pytest.fixture
def supabase_config():
    """Fixture providing test Supabase configuration"""
    return {
        "url": "https://test.supabase.co",
        "service_key": "test-service-key",
        "anon_key": "test-anon-key",
    }


@pytest.fixture
def test_admin_user():
    """Fixture providing a test admin user with AuthUser model"""
    from gittielabs_fastapi_auth.models import AuthUser, UserRole

    return AuthUser(
        id="admin-user-123",
        email="admin@example.com",
        organization_id="org-456",
        role=UserRole.ADMIN,
        first_name="Admin",
        last_name="User",
        is_authenticated=True,
        is_super_admin=False,
        organizations=[
            {"id": "org-456", "name": "Test Org", "role": "admin"},
            {"id": "org-789", "name": "Other Org", "role": "member"},
        ],
    )


@pytest.fixture
def test_super_admin_user():
    """Fixture providing a test super admin user"""
    from gittielabs_fastapi_auth.models import AuthUser, UserRole

    return AuthUser(
        id="super-admin-123",
        email="super@example.com",
        organization_id="org-456",
        role=UserRole.ADMIN,
        first_name="Super",
        last_name="Admin",
        is_authenticated=True,
        is_super_admin=True,
        organizations=[
            {"id": "org-456", "name": "Test Org", "role": "admin"},
            {"id": "org-789", "name": "Other Org", "role": "admin"},
        ],
    )


@pytest.fixture
def test_owner_user():
    """Fixture providing a test owner user"""
    from gittielabs_fastapi_auth.models import AuthUser, UserRole

    return AuthUser(
        id="owner-user-123",
        email="owner@example.com",
        organization_id="org-456",
        role=UserRole.OWNER,
        first_name="Owner",
        last_name="User",
        is_authenticated=True,
        is_super_admin=False,
        organizations=[
            {"id": "org-456", "name": "Test Org", "role": "owner"},
        ],
    )


@pytest.fixture
def test_member_user():
    """Fixture providing a test member user (non-admin)"""
    from gittielabs_fastapi_auth.models import AuthUser, UserRole

    return AuthUser(
        id="member-user-123",
        email="member@example.com",
        organization_id="org-456",
        role=UserRole.MEMBER,
        first_name="Member",
        last_name="User",
        is_authenticated=True,
        is_super_admin=False,
        organizations=[
            {"id": "org-456", "name": "Test Org", "role": "member"},
        ],
    )
