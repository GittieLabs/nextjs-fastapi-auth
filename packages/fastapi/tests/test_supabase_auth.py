"""
Unit tests for Supabase authentication service.

Tests the SupabaseAuthService class and helper functions for JWT validation,
user extraction, and token parsing.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from gittielabs_fastapi_auth.supabase_auth import (
    SupabaseAuthService,
    validate_supabase_jwt,
)
from gittielabs_fastapi_auth.models import AuthUser, UserRole


class TestSupabaseAuthService:
    """Test SupabaseAuthService class."""

    def test_initialization(self, supabase_config):
        """Test service initialization with config."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        assert service.supabase_url == supabase_config["url"]
        assert service.supabase_service_key == supabase_config["service_key"]
        assert service._jwt_secret == supabase_config["service_key"]
        assert not service._initialized
        assert service._client is None

    def test_initialization_with_custom_jwt_secret(self, supabase_config):
        """Test service initialization with custom JWT secret."""
        custom_secret = "custom-jwt-secret"
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
            jwt_secret=custom_secret,
        )

        assert service._jwt_secret == custom_secret

    @patch("gittielabs_fastapi_auth.supabase_auth.create_client")
    def test_initialize_client_success(self, mock_create_client, supabase_config):
        """Test successful client initialization."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        result = service._initialize_client()

        assert result is True
        assert service._initialized is True
        assert service._client == mock_client
        mock_create_client.assert_called_once_with(
            supabase_url=supabase_config["url"],
            supabase_key=supabase_config["service_key"],
        )

    def test_initialize_client_missing_credentials(self):
        """Test client initialization with missing credentials."""
        service = SupabaseAuthService(
            supabase_url="",
            supabase_service_key="",
        )

        result = service._initialize_client()

        assert result is False
        assert not service._initialized
        assert service._client is None

    @patch("gittielabs_fastapi_auth.supabase_auth.create_client")
    def test_initialize_client_failure(self, mock_create_client, supabase_config):
        """Test client initialization failure."""
        mock_create_client.side_effect = Exception("Connection failed")

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        result = service._initialize_client()

        assert result is False
        assert not service._initialized

    @patch("gittielabs_fastapi_auth.supabase_auth.create_client")
    def test_client_property_lazy_initialization(self, mock_create_client, supabase_config):
        """Test client property triggers lazy initialization."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        # Client should not be initialized yet
        assert not service._initialized

        # Accessing client property should trigger initialization
        client = service.client

        assert service._initialized
        assert client == mock_client

    @patch("gittielabs_fastapi_auth.supabase_auth.create_client")
    def test_client_property_already_initialized(self, mock_create_client, supabase_config):
        """Test client property when already initialized."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        # Initialize once
        _ = service.client
        mock_create_client.reset_mock()

        # Access again - should not re-initialize
        client = service.client

        assert client == mock_client
        mock_create_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_jwt_token_success(
        self, sample_jwt_token, supabase_config
    ):
        """Test successful JWT token validation."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload, error = await service.validate_jwt_token(sample_jwt_token)

        assert is_valid is True
        assert payload is not None
        assert error is None
        assert payload["sub"] == "test-user-123"
        assert payload["email"] == "test@example.com"
        assert payload["aud"] == "authenticated"

    @pytest.mark.asyncio
    async def test_validate_jwt_token_expired(
        self, expired_jwt_token, supabase_config
    ):
        """Test JWT token validation with expired token."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload, error = await service.validate_jwt_token(expired_jwt_token)

        assert is_valid is False
        assert payload is None
        assert error == "Token expired"

    @pytest.mark.asyncio
    async def test_validate_jwt_token_invalid_format(self, supabase_config):
        """Test JWT token validation with invalid format."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        # Token with only 2 parts
        invalid_token = "header.payload"

        is_valid, payload, error = await service.validate_jwt_token(invalid_token)

        assert is_valid is False
        assert payload is None
        assert "Invalid JWT format" in error

    @pytest.mark.asyncio
    async def test_validate_jwt_token_wrong_issuer(
        self, sample_jwt_payload, supabase_config
    ):
        """Test JWT token validation with wrong issuer."""
        from tests.conftest import create_test_jwt_token

        # Create token with wrong issuer
        wrong_payload = sample_jwt_payload.copy()
        wrong_payload["iss"] = "https://wrong.issuer.com/auth/v1"
        wrong_token = create_test_jwt_token(wrong_payload)

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload, error = await service.validate_jwt_token(wrong_token)

        assert is_valid is False
        assert payload is None
        assert "Invalid token issuer" in error

    @pytest.mark.asyncio
    async def test_validate_jwt_token_missing_email(self, supabase_config):
        """Test JWT token validation with missing email."""
        from tests.conftest import create_test_jwt_token

        # Create token without email
        payload = {
            "sub": "test-user-123",
            "aud": "authenticated",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "iss": "https://test.supabase.co/auth/v1",
        }
        token = create_test_jwt_token(payload)

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload_result, error = await service.validate_jwt_token(token)

        assert is_valid is False
        assert payload_result is None
        assert "Token missing required user information" in error

    @pytest.mark.asyncio
    async def test_validate_jwt_token_missing_sub(self, supabase_config):
        """Test JWT token validation with missing sub."""
        from tests.conftest import create_test_jwt_token

        # Create token without sub
        payload = {
            "email": "test@example.com",
            "aud": "authenticated",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "iss": "https://test.supabase.co/auth/v1",
        }
        token = create_test_jwt_token(payload)

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload_result, error = await service.validate_jwt_token(token)

        assert is_valid is False
        assert payload_result is None
        assert "Token missing required user information" in error

    @pytest.mark.asyncio
    async def test_get_user_from_token_success(
        self, sample_jwt_token, supabase_config
    ):
        """Test extracting user from valid token."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        user = await service.get_user_from_token(sample_jwt_token)

        assert user is not None
        assert isinstance(user, AuthUser)
        assert user.id == "test-user-123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.MEMBER
        assert user.is_authenticated is True
        assert user.is_legacy_user is False
        assert user.is_super_admin is False

    @pytest.mark.asyncio
    async def test_get_user_from_token_admin(
        self, admin_jwt_token, supabase_config
    ):
        """Test extracting admin user from token.

        Note: The role from JWT metadata is not used directly - it's a fallback
        that will be overridden by organization_context. The base user gets MEMBER
        role unless they're a super admin.
        """
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        user = await service.get_user_from_token(admin_jwt_token)

        assert user is not None
        # Role from token is not directly used - defaults to MEMBER unless super admin
        assert user.role == UserRole.MEMBER
        # is_admin will be False since role is MEMBER and is_super_admin is False
        assert user.is_authenticated is True

    @pytest.mark.asyncio
    async def test_get_user_from_token_super_admin(
        self, super_admin_jwt_token, supabase_config
    ):
        """Test extracting super admin user from token."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        user = await service.get_user_from_token(super_admin_jwt_token)

        assert user is not None
        assert user.is_super_admin is True
        assert user.role == UserRole.ADMIN
        assert user.is_admin is True
        assert user.is_owner is True  # Super admins have owner privileges

    @pytest.mark.asyncio
    async def test_get_user_from_token_invalid_token(self, supabase_config):
        """Test extracting user from invalid token."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        user = await service.get_user_from_token("invalid.token")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_from_token_expired(
        self, expired_jwt_token, supabase_config
    ):
        """Test extracting user from expired token."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        user = await service.get_user_from_token(expired_jwt_token)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_from_token_with_profile(self, supabase_config):
        """Test extracting user with profile information from token."""
        from tests.conftest import create_test_jwt_payload, create_test_jwt_token

        payload = create_test_jwt_payload()
        payload["user_metadata"]["first_name"] = "John"
        payload["user_metadata"]["last_name"] = "Doe"
        payload["user_metadata"]["avatar_url"] = "https://example.com/avatar.jpg"
        token = create_test_jwt_token(payload)

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        user = await service.get_user_from_token(token)

        assert user is not None
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.avatar_url == "https://example.com/avatar.jpg"
        assert user.full_name == "John Doe"

    def test_extract_token_from_header_bearer(self, supabase_config):
        """Test extracting token from Bearer authorization header."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        token = service.extract_token_from_header("Bearer test-token-123")

        assert token == "test-token-123"

    def test_extract_token_from_header_direct(self, supabase_config):
        """Test extracting direct token from header."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        token = service.extract_token_from_header("test-token-123")

        assert token == "test-token-123"

    def test_extract_token_from_header_empty(self, supabase_config):
        """Test extracting token from empty header."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        token = service.extract_token_from_header("")

        assert token is None

    def test_extract_token_from_header_none(self, supabase_config):
        """Test extracting token from None header."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        token = service.extract_token_from_header(None)

        assert token is None

    def test_extract_token_from_header_bearer_lowercase(self, supabase_config):
        """Test extracting token from lowercase bearer header."""
        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        # Note: The function is case-sensitive and expects "Bearer " with capital B
        token = service.extract_token_from_header("bearer test-token-123")

        # Should return the whole string as direct token since it doesn't start with "Bearer "
        assert token == "bearer test-token-123"


class TestValidateSupabaseJWT:
    """Test standalone validate_supabase_jwt function."""

    @pytest.mark.asyncio
    async def test_validate_supabase_jwt_success(
        self, sample_jwt_token, supabase_config
    ):
        """Test successful JWT validation."""
        result = await validate_supabase_jwt(sample_jwt_token, supabase_config["url"])

        assert result is not None
        assert result["id"] == "test-user-123"
        assert result["email"] == "test@example.com"
        assert result["aud"] == "authenticated"
        assert "user_metadata" in result
        assert "app_metadata" in result

    @pytest.mark.asyncio
    async def test_validate_supabase_jwt_expired(
        self, expired_jwt_token, supabase_config
    ):
        """Test JWT validation with expired token."""
        result = await validate_supabase_jwt(expired_jwt_token, supabase_config["url"])

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_supabase_jwt_invalid_format(self, supabase_config):
        """Test JWT validation with invalid format."""
        result = await validate_supabase_jwt("invalid.token", supabase_config["url"])

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_supabase_jwt_missing_email(self, supabase_config):
        """Test JWT validation with missing email."""
        from tests.conftest import create_test_jwt_token

        payload = {
            "sub": "test-user-123",
            "aud": "authenticated",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "iss": "https://test.supabase.co/auth/v1",
        }
        token = create_test_jwt_token(payload)

        result = await validate_supabase_jwt(token, supabase_config["url"])

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_supabase_jwt_missing_id(self, supabase_config):
        """Test JWT validation with missing id."""
        from tests.conftest import create_test_jwt_token

        payload = {
            "email": "test@example.com",
            "aud": "authenticated",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "iss": "https://test.supabase.co/auth/v1",
        }
        token = create_test_jwt_token(payload)

        result = await validate_supabase_jwt(token, supabase_config["url"])

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_supabase_jwt_with_metadata(self, supabase_config):
        """Test JWT validation with user metadata."""
        from tests.conftest import create_test_jwt_payload, create_test_jwt_token

        payload = create_test_jwt_payload(role="admin", is_super_admin=True)
        token = create_test_jwt_token(payload)

        result = await validate_supabase_jwt(token, supabase_config["url"])

        assert result is not None
        assert result["user_metadata"]["role"] == "admin"
        assert result["user_metadata"]["is_super_admin"] is True


class TestEdgeCasesAndSecurity:
    """Test edge cases and security scenarios."""

    @pytest.mark.asyncio
    async def test_very_long_token(self, supabase_config):
        """Test handling of very long tokens."""
        from tests.conftest import create_test_jwt_payload, create_test_jwt_token

        payload = create_test_jwt_payload()
        payload["user_metadata"]["long_data"] = "x" * 10000
        token = create_test_jwt_token(payload)

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload_result, error = await service.validate_jwt_token(token)

        assert is_valid is True
        assert payload_result is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_email(self, supabase_config):
        """Test handling of special characters in email."""
        from tests.conftest import create_test_jwt_payload, create_test_jwt_token

        payload = create_test_jwt_payload(email="admin+special@example.co.uk")
        token = create_test_jwt_token(payload)

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        user = await service.get_user_from_token(token)

        assert user is not None
        assert user.email == "admin+special@example.co.uk"

    @pytest.mark.asyncio
    async def test_malformed_json_payload(self, supabase_config):
        """Test handling of malformed JSON in token."""
        # Create token with invalid base64 payload
        malformed_token = "eyJhbGciOiJIUzI1NiJ9.invalid-base64.signature"

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload, error = await service.validate_jwt_token(malformed_token)

        assert is_valid is False
        assert payload is None
        assert error is not None

    @pytest.mark.asyncio
    async def test_token_without_expiration(self, supabase_config):
        """Test handling of token without expiration."""
        from tests.conftest import create_test_jwt_token

        payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "iss": "https://test.supabase.co/auth/v1",
            "user_metadata": {},
            "app_metadata": {},
        }
        token = create_test_jwt_token(payload)

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        is_valid, payload_result, error = await service.validate_jwt_token(token)

        # Should still be valid if no expiration is present
        assert is_valid is True
        assert payload_result is not None

    @pytest.mark.asyncio
    async def test_concurrent_validation(self, sample_jwt_token, supabase_config):
        """Test concurrent token validations."""
        import asyncio

        service = SupabaseAuthService(
            supabase_url=supabase_config["url"],
            supabase_service_key=supabase_config["service_key"],
        )

        # Validate same token multiple times concurrently
        tasks = [
            service.validate_jwt_token(sample_jwt_token)
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        # All validations should succeed
        assert all(result[0] is True for result in results)
        assert all(result[1] is not None for result in results)
        assert all(result[2] is None for result in results)
