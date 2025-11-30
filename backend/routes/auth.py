"""Authentication routes for user registration and login."""

# Standard library imports
import logging
from typing import Annotated

# Third-party imports
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

# Local imports
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize service
user_service = UserService()


# Pydantic models
class UserRegisterRequest(BaseModel):
    """User registration request model."""

    email: str
    password: str
    username: str | None = None


class UserLoginRequest(BaseModel):
    """User login request model."""

    email: str
    password: str


class TokenRefreshRequest(BaseModel):
    """Token refresh request model."""

    refresh_token: str


# Helper function to get user from token
async def get_current_user(authorization: Annotated[str | None, Header()] = None):
    """
    Extract and validate user from Authorization header.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        User ID if valid

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )

        user_id = user_service.auth_service.get_user_from_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return user_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: UserRegisterRequest):
    """
    Register a new user account.

    Args:
        request: User registration data

    Returns:
        Created user data

    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        user_data = await user_service.create_user(
            email=request.email, password=request.password, username=request.username
        )

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        logger.info(f"New user registered: {request.email}")
        return {
            "success": True,
            "user": user_data,
            "message": "User registered successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login")
async def login_user(request: UserLoginRequest):
    """
    Authenticate user and return access tokens.

    Args:
        request: User login credentials

    Returns:
        User data with access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        auth_data = await user_service.authenticate_user(
            email=request.email, password=request.password
        )

        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        logger.info(f"User logged in: {request.email}")
        return {"success": True, **auth_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh")
async def refresh_token(request: TokenRefreshRequest):
    """
    Generate new access token using refresh token.

    Args:
        request: Refresh token

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        new_token = await user_service.refresh_access_token(
            refresh_token=request.refresh_token
        )

        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        return {"success": True, "access_token": new_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.get("/me")
async def get_current_user_info(user_id: Annotated[int, Depends(get_current_user)]):
    """
    Get current authenticated user's information.

    Args:
        user_id: Extracted from JWT token

    Returns:
        User profile data

    Raises:
        HTTPException: If user not found
    """
    try:
        user_data = await user_service.get_user_by_id(user_id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {"success": True, "user": user_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information",
        )
