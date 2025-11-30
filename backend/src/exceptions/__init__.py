"""
Custom Exception Classes for EV Navigation System
Provides standardized error handling across the application
"""

from .custom_exceptions import (
    EVNavigationException,
    DatabaseException,
    RedisException,
    QdrantException,
    AIServiceException,
    RouteCalculationException,
    VehicleNotFoundException,
    ChargingStationNotFoundException,
    ValidationException,
    AuthenticationException,
    RateLimitException
)

__all__ = [
    "EVNavigationException",
    "DatabaseException",
    "RedisException",
    "QdrantException",
    "AIServiceException",
    "RouteCalculationException",
    "VehicleNotFoundException",
    "ChargingStationNotFoundException",
    "ValidationException",
    "AuthenticationException",
    "RateLimitException",
]
