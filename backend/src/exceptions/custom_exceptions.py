"""
Custom Exception Classes for EV Navigation System
Hierarchical exception structure for better error handling and debugging
"""

from typing import Optional, Dict, Any
from fastapi import status


class EVNavigationException(Exception):
    """Base exception class for all EV Navigation errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


# ==================== Database Exceptions ====================

class DatabaseException(EVNavigationException):
    """Database-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_ERROR",
            details=details
        )


class VehicleNotFoundException(EVNavigationException):
    """Vehicle not found in database"""
    
    def __init__(self, vehicle_id: str):
        super().__init__(
            message=f"Vehicle with ID '{vehicle_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="VEHICLE_NOT_FOUND",
            details={"vehicle_id": vehicle_id}
        )


class ChargingStationNotFoundException(EVNavigationException):
    """Charging station not found"""
    
    def __init__(self, station_id: str):
        super().__init__(
            message=f"Charging station with ID '{station_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="CHARGING_STATION_NOT_FOUND",
            details={"station_id": station_id}
        )


# ==================== Cache/Service Exceptions ====================

class RedisException(EVNavigationException):
    """Redis cache-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="REDIS_ERROR",
            details=details
        )


class QdrantException(EVNavigationException):
    """Qdrant vector database errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="QDRANT_ERROR",
            details=details
        )


# ==================== AI Service Exceptions ====================

class AIServiceException(EVNavigationException):
    """AI/OpenRouter service errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="AI_SERVICE_ERROR",
            details=details
        )


# ==================== Business Logic Exceptions ====================

class RouteCalculationException(EVNavigationException):
    """Route calculation/optimization errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="ROUTE_CALCULATION_ERROR",
            details=details
        )


class ValidationException(EVNavigationException):
    """Input validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        validation_details = details or {}
        if field:
            validation_details["field"] = field
        
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=validation_details
        )


# ==================== Security Exceptions ====================

class AuthenticationException(EVNavigationException):
    """Authentication/authorization errors"""
    
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class RateLimitException(EVNavigationException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


# ==================== External Service Exceptions ====================

class ExternalServiceException(EVNavigationException):
    """External service (geopy, maps API, etc.) errors"""
    
    def __init__(self, service_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        service_details = details or {}
        service_details["service"] = service_name
        
        super().__init__(
            message=f"{service_name} service error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=service_details
        )
