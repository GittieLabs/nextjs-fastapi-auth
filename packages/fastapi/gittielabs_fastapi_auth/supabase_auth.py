"""
Supabase authentication module for JWT validation and user management.

This module handles Supabase JWT token validation, user fetching, and
role-based access control when the application is in authentication mode.
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import jwt
from loguru import logger
from supabase import Client, create_client

from .models import AuthUser, UserRole


class SupabaseAuthService:
    """
    Service for Supabase authentication and user management.

    Handles JWT token validation, user information extraction, and
    organization membership lookups.
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_service_key: str,
        jwt_secret: Optional[str] = None,
    ):
        """
        Initialize Supabase auth service.

        Args:
            supabase_url: Supabase project URL
            supabase_service_key: Supabase service role key
            jwt_secret: Optional JWT secret (defaults to service key)
        """
        self.supabase_url = supabase_url
        self.supabase_service_key = supabase_service_key
        self._jwt_secret = jwt_secret or supabase_service_key
        self._client: Optional[Client] = None
        self._initialized = False

    def _initialize_client(self) -> bool:
        """Initialize Supabase client if not already done."""
        if self._initialized:
            return True

        if not self.supabase_url or not self.supabase_service_key:
            logger.warning("Supabase credentials not configured")
            return False

        try:
            self._client = create_client(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_service_key,
            )

            self._initialized = True
            logger.info("Supabase authentication client initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return False

    @property
    def client(self) -> Optional[Client]:
        """Get Supabase client, initializing if needed."""
        if not self._initialized:
            self._initialize_client()
        return self._client

    async def validate_jwt_token(
        self, token: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate a Supabase JWT token.

        This performs basic JWT validation including format, expiration,
        and issuer checks. For production, you may want to add signature
        verification.

        Args:
            token: JWT token to validate

        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        try:
            logger.debug("Attempting Supabase JWT token validation...")

            # Decode without verification to check the basic structure and content
            unverified = jwt.decode(token, options={"verify_signature": False})
            logger.debug(
                f"Unverified token contents: iss={unverified.get('iss')}, "
                f"aud={unverified.get('aud')}, sub={unverified.get('sub')}"
            )

            # Check if this looks like a Supabase token
            expected_iss = self.supabase_url + "/auth/v1"
            if unverified.get("iss") != expected_iss:
                logger.warning(
                    f"Token issuer mismatch: expected {expected_iss}, "
                    f"got {unverified.get('iss')}"
                )
                return False, None, f"Invalid token issuer: {unverified.get('iss')}"

            # Check expiration
            exp = unverified.get("exp")
            if exp:
                if (
                    datetime.fromtimestamp(exp, tz=timezone.utc)
                    < datetime.now(timezone.utc)
                ):
                    logger.warning("Token has expired")
                    return False, None, "Token expired"

            # Extract user information from the JWT payload
            payload = {
                "sub": unverified.get("sub"),
                "email": unverified.get("email"),
                "aud": unverified.get("aud"),
                "exp": unverified.get("exp"),
                "iat": unverified.get("iat"),
                "iss": unverified.get("iss"),
                "user_metadata": unverified.get("user_metadata", {}),
                "app_metadata": unverified.get("app_metadata", {}),
            }

            if not payload["email"] or not payload["sub"]:
                logger.warning(
                    f"Token missing required fields: email={payload['email']}, "
                    f"sub={payload['sub']}"
                )
                return False, None, "Token missing required user information"

            logger.info(
                f"Successfully validated Supabase token for user: {payload['email']}"
            )
            return True, payload, None

        except jwt.DecodeError as e:
            logger.error(f"JWT decode error: {e}")
            logger.debug(f"Token parts: {len(token.split('.'))}")
            logger.debug(f"Token preview: {token[:50]}...")
            return False, None, f"Invalid JWT format: {str(e)}"
        except Exception as e:
            logger.error(f"Supabase token validation error: {e}")
            return False, None, f"Invalid token: {str(e)}"

    async def get_user_from_token(self, token: str) -> Optional[AuthUser]:
        """
        Get user information from a valid JWT token.

        This creates an AuthUser from the JWT payload. For full organization
        membership data, you should also query your database.

        Args:
            token: Validated JWT token

        Returns:
            AuthUser if token is valid, None otherwise
        """
        is_valid, payload, error = await self.validate_jwt_token(token)

        if not is_valid or not payload:
            logger.debug(f"Token validation failed: {error}")
            return None

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            logger.warning(
                f"Missing required user info in token: user_id={user_id}, email={email}"
            )
            return None

        try:
            # Extract admin/super_admin status from JWT token metadata
            user_metadata = payload.get("user_metadata", {})
            jwt_is_super_admin = user_metadata.get("is_super_admin", False)
            token_role = user_metadata.get(
                "role", "admin" if jwt_is_super_admin else "member"
            )

            logger.debug(
                f"JWT token for {email}: is_super_admin={jwt_is_super_admin}, "
                f"token_role={token_role}"
            )

            # Create basic AuthUser from token data
            fallback_role = UserRole.ADMIN if jwt_is_super_admin else UserRole.MEMBER

            user = AuthUser(
                id=user_id,
                email=email,
                organization_id="",  # Will be set by organization context
                role=fallback_role,
                # Profile information from token
                first_name=payload.get("user_metadata", {}).get("first_name", ""),
                last_name=payload.get("user_metadata", {}).get("last_name", ""),
                avatar_url=payload.get("user_metadata", {}).get("avatar_url"),
                # Authentication context
                is_authenticated=True,
                is_legacy_user=False,
                is_super_admin=jwt_is_super_admin,
                # Organizations - empty for now, will be populated by org-specific logic
                organizations=[],
                # Session info
                session_id=None,
                expires_at=payload.get("exp"),
            )

            logger.debug(f"Created AuthUser from token for {email}")
            return user

        except Exception as e:
            logger.error(f"Failed to create user from token {user_id}: {e}")
            return None

    def extract_token_from_header(self, authorization_header: str) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Args:
            authorization_header: Authorization header value

        Returns:
            JWT token if found, None otherwise
        """
        if not authorization_header:
            return None

        # Handle "Bearer <token>" format
        if authorization_header.startswith("Bearer "):
            return authorization_header[7:]  # Remove "Bearer " prefix

        # Handle direct token
        return authorization_header


async def validate_supabase_jwt(token: str, supabase_url: str) -> Optional[Dict]:
    """
    Validate a Supabase JWT token and extract user information.

    This is a simplified validation function that decodes the JWT
    without strict signature verification. Use this for development
    or when you trust the token source.

    Args:
        token: The Supabase JWT token to validate
        supabase_url: Supabase project URL

    Returns:
        Dict containing user information if valid, None if invalid
    """
    try:
        # Decode without strict validation
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Extract user information from the JWT payload
        user_info = {
            "id": decoded.get("sub"),
            "email": decoded.get("email"),
            "user_metadata": decoded.get("user_metadata", {}),
            "app_metadata": decoded.get("app_metadata", {}),
            "aud": decoded.get("aud"),
            "exp": decoded.get("exp"),
            "iat": decoded.get("iat"),
            "iss": decoded.get("iss"),
        }

        # Validate required fields
        if not user_info["email"] or not user_info["id"]:
            logger.warning("Supabase JWT missing required fields (email or id)")
            return None

        # Check expiration
        exp = user_info.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            timezone.utc
        ):
            logger.warning("Supabase JWT has expired")
            return None

        logger.debug(f"Validated Supabase JWT for user: {user_info['email']}")
        return user_info

    except jwt.DecodeError:
        logger.warning("Invalid Supabase JWT format")
        return None
    except jwt.ExpiredSignatureError:
        logger.warning("Supabase JWT has expired")
        return None
    except Exception as e:
        logger.error(f"Error validating Supabase JWT: {e}")
        return None
