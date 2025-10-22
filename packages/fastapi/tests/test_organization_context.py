"""
Unit tests for organization context utilities.

Tests the OrganizationContext class and helper functions for extracting
organization IDs and subdomains from requests in multi-tenant architecture.
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from gittielabs_fastapi_auth.organization_context import (
    OrganizationContext,
    get_organization_id_from_request,
    get_organization_id_from_request_optional,
    extract_subdomain_from_request,
)


class TestOrganizationContext:
    """Test OrganizationContext class methods."""

    def test_get_organization_id_from_state(self, mock_request_with_subdomain):
        """Test getting organization ID from request.state (set by middleware)."""
        result = OrganizationContext.get_organization_id_from_request(
            mock_request_with_subdomain
        )

        assert result == "org-123"

    def test_get_organization_id_from_state_converts_to_string(self):
        """Test that organization ID is converted to string."""
        from tests.conftest import create_test_jwt_token, create_test_jwt_payload
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with integer org_id
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "authorization": f"Bearer {create_test_jwt_token(create_test_jwt_payload())}",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock()
        mock_request.state.organization_id = 12345  # Integer

        result = OrganizationContext.get_organization_id_from_request(mock_request)

        assert result == "12345"
        assert isinstance(result, str)

    def test_get_organization_id_from_subdomain_header_error(self):
        """Test that subdomain header without state raises helpful error."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with subdomain header but no state
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "ktg",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # Empty spec means no attributes

        with pytest.raises(HTTPException) as exc_info:
            OrganizationContext.get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400
        assert "ktg" in exc_info.value.detail
        assert "not resolved" in exc_info.value.detail

    def test_get_organization_id_from_host_header_localhost(self):
        """Test extracting subdomain from localhost Host header."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with localhost subdomain in Host
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "ktg.localhost:3000",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        with pytest.raises(HTTPException) as exc_info:
            OrganizationContext.get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400
        assert "ktg" in exc_info.value.detail
        assert "not resolved" in exc_info.value.detail

    def test_get_organization_id_from_host_header_production(self):
        """Test extracting subdomain from production domain Host header."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with production subdomain in Host
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "ktg.govreadyai.app",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        with pytest.raises(HTTPException) as exc_info:
            OrganizationContext.get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400
        assert "ktg" in exc_info.value.detail

    def test_get_organization_id_no_context_raises_error(self):
        """Test that request without any org context raises error."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request without any org context
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        with pytest.raises(HTTPException) as exc_info:
            OrganizationContext.get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400
        assert "No organization context available" in exc_info.value.detail

    def test_get_organization_id_www_subdomain_ignored(self):
        """Test that 'www' subdomain is ignored."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with www subdomain
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "www.govreadyai.app",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        with pytest.raises(HTTPException) as exc_info:
            OrganizationContext.get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400
        assert "No organization context available" in exc_info.value.detail

    def test_get_organization_id_localhost_subdomain_ignored(self):
        """Test that 'localhost' as subdomain is ignored."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with plain localhost
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "localhost:3000",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        with pytest.raises(HTTPException) as exc_info:
            OrganizationContext.get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400
        assert "No organization context available" in exc_info.value.detail

    def test_get_organization_id_super_admin_logged(self):
        """Test that super admin requests are logged (still requires org context)."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with super admin flag but no org context
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "localhost:3000",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=['api_key_type'])  # Only has api_key_type
        mock_request.state.api_key_type = "super_admin"

        with pytest.raises(HTTPException) as exc_info:
            OrganizationContext.get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400

    def test_get_organization_id_optional_success(self, mock_request_with_subdomain):
        """Test optional get returns org ID when available."""
        result = OrganizationContext.get_organization_id_from_request_optional(
            mock_request_with_subdomain
        )

        assert result == "org-123"

    def test_get_organization_id_optional_returns_none(self):
        """Test optional get returns None when org ID not available."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request without org context
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        result = OrganizationContext.get_organization_id_from_request_optional(
            mock_request
        )

        assert result is None

    def test_get_organization_id_optional_returns_none_on_subdomain_error(self):
        """Test optional get returns None even when subdomain detected but not resolved."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request with subdomain but no state
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "ktg",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        result = OrganizationContext.get_organization_id_from_request_optional(
            mock_request
        )

        assert result is None

    def test_extract_subdomain_from_header(self):
        """Test extracting subdomain from x-organization-subdomain header."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "ktg",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result == "ktg"

    def test_extract_subdomain_from_localhost_host(self):
        """Test extracting subdomain from localhost Host header."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "ktg.localhost:3000",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result == "ktg"

    def test_extract_subdomain_from_production_host(self):
        """Test extracting subdomain from production Host header."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "ktg.govreadyai.app",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result == "ktg"

    def test_extract_subdomain_header_priority(self):
        """Test that x-organization-subdomain header takes priority over Host."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "from-header",
            "host": "from-host.govreadyai.app",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result == "from-header"

    def test_extract_subdomain_www_ignored(self):
        """Test that 'www' subdomain is ignored."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "www.govreadyai.app",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result is None

    def test_extract_subdomain_localhost_ignored(self):
        """Test that plain 'localhost' is ignored."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "localhost:3000",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result is None

    def test_extract_subdomain_no_matching_domain(self):
        """Test that non-matching domains return None."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "example.com",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result is None

    def test_extract_subdomain_empty_host(self):
        """Test extracting subdomain from empty Host header."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result is None


class TestConvenienceFunctions:
    """Test convenience functions that wrap OrganizationContext methods."""

    def test_get_organization_id_convenience_function(self, mock_request_with_subdomain):
        """Test get_organization_id_from_request convenience function."""
        result = get_organization_id_from_request(mock_request_with_subdomain)

        assert result == "org-123"

    def test_get_organization_id_convenience_function_raises(self):
        """Test convenience function raises HTTPException when no context."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request without org context
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        with pytest.raises(HTTPException) as exc_info:
            get_organization_id_from_request(mock_request)

        assert exc_info.value.status_code == 400

    def test_get_organization_id_optional_convenience_function(
        self, mock_request_with_subdomain
    ):
        """Test get_organization_id_from_request_optional convenience function."""
        result = get_organization_id_from_request_optional(mock_request_with_subdomain)

        assert result == "org-123"

    def test_get_organization_id_optional_convenience_returns_none(self):
        """Test optional convenience function returns None."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        # Create mock request without org context
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock(spec=[])  # No attributes

        result = get_organization_id_from_request_optional(mock_request)

        assert result is None

    def test_extract_subdomain_convenience_function(self):
        """Test extract_subdomain_from_request convenience function."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "ktg",
        })

        result = extract_subdomain_from_request(mock_request)

        assert result == "ktg"

    def test_extract_subdomain_convenience_returns_none(self):
        """Test extract subdomain convenience function returns None."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})

        result = extract_subdomain_from_request(mock_request)

        assert result is None


class TestEdgeCasesAndIntegration:
    """Test edge cases and integration scenarios."""

    def test_subdomain_with_port_number(self):
        """Test subdomain extraction with port number in Host."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "ktg.localhost:8000",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result == "ktg"

    def test_subdomain_case_sensitivity(self):
        """Test that subdomain is returned as-is (case preserved)."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "KTG",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result == "KTG"

    def test_organization_id_empty_string_in_state(self):
        """Test that empty string org ID is still returned."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock()
        mock_request.state.organization_id = ""

        # Empty string is falsy, so it should continue to check headers
        with pytest.raises(HTTPException):
            OrganizationContext.get_organization_id_from_request(mock_request)

    def test_organization_id_zero_in_state(self):
        """Test that 0 as org ID is handled (falsy but valid)."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock()
        mock_request.state.organization_id = 0

        # 0 is falsy, so should continue to check headers and ultimately fail
        with pytest.raises(HTTPException):
            OrganizationContext.get_organization_id_from_request(mock_request)

    def test_multiple_dots_in_subdomain(self):
        """Test subdomain extraction with multiple levels."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "api.ktg.govreadyai.app",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        # Should extract first part
        assert result == "api"

    def test_ip_address_host(self):
        """Test Host with IP address instead of domain."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "host": "127.0.0.1:3000",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result is None

    def test_state_takes_precedence_over_headers(self):
        """Test that request.state.organization_id takes precedence over headers."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "from-header",
            "host": "from-host.govreadyai.app",
        })
        mock_request.url = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.state = Mock()
        mock_request.state.organization_id = "from-state"

        result = OrganizationContext.get_organization_id_from_request(mock_request)

        assert result == "from-state"

    def test_special_characters_in_subdomain(self):
        """Test subdomain with hyphens and numbers."""
        from fastapi import Request
        from fastapi.datastructures import Headers

        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-organization-subdomain": "org-123-test",
        })

        result = OrganizationContext.extract_subdomain_from_request(mock_request)

        assert result == "org-123-test"
