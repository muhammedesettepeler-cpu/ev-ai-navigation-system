"""
Global Exception Handlers for FastAPI Application
Provides consistent error responses across all endpoints
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from typing import Union
from datetime import datetime

from src.exceptions.custom_exceptions import EVNavigationException

logger = logging.getLogger(__name__)


async def ev_navigation_exception_handler(
    request: Request, 
    exc: Exception  # Changed to Exception for FastAPI compatibility
) -> JSONResponse:
    """
    Handle all custom EV Navigation exceptions
    Provides structured error response with logging
    """
    # Type guard
    if not isinstance(exc, EVNavigationException):
        return await generic_exception_handler(request, exc)
    
    # Log error with details
    logger.error(
        f"EVNavigationException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return structured error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception  # Changed to Exception for FastAPI compatibility
) -> JSONResponse:
    """
    Handle Pydantic validation errors
    Formats validation errors in a user-friendly way
    """
    # Type guard
    if not isinstance(exc, (RequestValidationError, ValidationError)):
        return await generic_exception_handler(request, exc)
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
        errors.append({
            "field": field_path,
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error")
        })
    
    # Log validation error
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {
                "validation_errors": errors
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle all uncaught exceptions
    Provides safe error response without exposing internals
    """
    # Log the full exception with traceback
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return generic error (don't expose internal details in production)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {
                "error_type": type(exc).__name__
                # Don't include actual error message in production for security
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


async def http_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle FastAPI HTTPException
    Provides consistent format for HTTP errors
    """
    from fastapi import HTTPException
    
    if isinstance(exc, HTTPException):
        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "error_code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {},
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    # Fallback to generic handler
    return await generic_exception_handler(request, exc)
