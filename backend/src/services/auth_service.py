"""Authentication service for user management and JWT token handling."""

# Standard library imports
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

# Third-party imports
import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AuthService:
    """Handle user authentication, password hashing, and JWT tokens."""

    def __init__(self) -> None:
        """Initialize authentication service with JWT configuration."""
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 7

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to check against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def create_access_token(self, user_id: int, email: str) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User's database ID
            email: User's email address

        Returns:
            JWT access token string
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {"sub": str(user_id), "email": email, "exp": expire, "type": "access"}
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(self, user_id: int) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: User's database ID

        Returns:
            JWT refresh token string
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string to verify

        Returns:
            Decoded token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def get_user_from_token(self, token: str) -> Optional[int]:
        """
        Extract user ID from a valid token.

        Args:
            token: JWT token string

        Returns:
            User ID if token is valid, None otherwise
        """
        payload = self.verify_token(token)
        if payload:
            try:
                return int(payload.get("sub"))
            except (ValueError, TypeError):
                return None
        return None
