# Error Handling System Documentation

## 🎯 Overview

The EV Navigation API implements a comprehensive, production-ready error handling system that provides:
- **Standardized error responses** across all endpoints
- **Structured exception hierarchy** for better error management
- **Detailed logging** for debugging and monitoring
- **Type-safe error handling** with full Pydantic validation

## 📋 Error Response Format

All errors follow a consistent JSON structure:

```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "Human-readable error description",
  "details": {
    "field": "field_name",
    "additional_context": "value"
  },
  "timestamp": "2025-10-25T16:35:01.620257",
  "path": "/api/endpoint"
}
```

### Fields:
- **error**: Always `true` for error responses
- **error_code**: Machine-readable error identifier (e.g., `VALIDATION_ERROR`, `DATABASE_ERROR`)
- **message**: Human-readable error message
- **details**: Additional context specific to the error type
- **timestamp**: UTC timestamp when error occurred
- **path**: API endpoint where error occurred

## 🏗️ Exception Hierarchy

### Base Exception
```python
EVNavigationException
├── DatabaseException
│   ├── VehicleNotFoundException
│   └── ChargingStationNotFoundException
├── RedisException
├── QdrantException
├── AIServiceException
├── RouteCalculationException
├── ValidationException
├── AuthenticationException
├── RateLimitException
└── ExternalServiceException
```

## 📝 Exception Types

### 1. **Database Exceptions** (503 Service Unavailable)

#### `DatabaseException`
Database connection or query failures.

**Example:**
```python
raise DatabaseException(
    message="Failed to connect to database",
    details={"error": str(e)}
)
```

**Response:**
```json
{
  "error": true,
  "error_code": "DATABASE_ERROR",
  "message": "Failed to connect to database",
  "status_code": 503,
  "details": {"error": "Connection timeout"}
}
```

#### `VehicleNotFoundException` (404 Not Found)
Vehicle not found in database.

```python
raise VehicleNotFoundException(vehicle_id="tesla-model-3")
```

#### `ChargingStationNotFoundException` (404 Not Found)
Charging station not found.

```python
raise ChargingStationNotFoundException(station_id="station-123")
```

### 2. **Cache/Service Exceptions** (503 Service Unavailable)

#### `RedisException`
Redis cache errors.

#### `QdrantException`
Vector database errors.

### 3. **AI Service Exceptions** (503 Service Unavailable)

#### `AIServiceException`
OpenRouter/AI service failures.

```python
raise AIServiceException(
    message="AI service error",
    details={"error": str(e)}
)
```

### 4. **Business Logic Exceptions**

#### `RouteCalculationException` (422 Unprocessable Entity)
Route planning/optimization errors.

#### `ValidationException` (400 Bad Request)
Input validation errors.

```python
raise ValidationException(
    message="Message cannot be empty",
    field="message"
)
```

**Response:**
```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "Message cannot be empty",
  "details": {"field": "message"},
  "timestamp": "2025-10-25T16:35:01.620257",
  "path": "/api/ai-chat"
}
```

### 5. **Security Exceptions**

#### `AuthenticationException` (401 Unauthorized)
Authentication failures.

#### `RateLimitException` (429 Too Many Requests)
Rate limit exceeded.

```python
raise RateLimitException(
    message="Rate limit exceeded",
    retry_after=60  # seconds
)
```

### 6. **Pydantic Validation Errors** (422 Unprocessable Entity)

Automatically handled for request body validation.

**Example Request:**
```json
{
  "invalid_field": 123
}
```

**Error Response:**
```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "validation_errors": [
      {
        "field": "body -> start_location",
        "message": "Field required",
        "type": "missing"
      },
      {
        "field": "body -> destination",
        "message": "Field required",
        "type": "missing"
      }
    ]
  },
  "timestamp": "2025-10-25T16:35:07.354258",
  "path": "/api/plan-route"
}
```

## 🔧 Usage Examples

### Endpoint with Error Handling

```python
@app.post("/api/plan-route")
async def plan_route(request: RouteRequest):
    """Plan route with validation and error handling"""
    try:
        # Validate inputs
        if not request.start_location or len(request.start_location.strip()) == 0:
            raise ValidationException(
                message="Start location cannot be empty",
                field="start_location"
            )
        
        # Business logic
        result = await route_service.calculate_route(request)
        return result
        
    except ValidationException:
        raise  # Re-raise to be handled by global handler
    except Exception as e:
        raise RouteCalculationException(
            message="Failed to calculate route",
            details={"error": str(e)}
        )
```

### Custom Exception Usage

```python
from src.exceptions.custom_exceptions import (
    ValidationException,
    DatabaseException,
    AIServiceException
)

# Validation error
if not user_input:
    raise ValidationException(
        message="Input cannot be empty",
        field="user_input"
    )

# Database error
try:
    vehicle = await db.get_vehicle(vehicle_id)
except Exception as e:
    raise DatabaseException(
        message="Failed to fetch vehicle",
        details={"vehicle_id": vehicle_id, "error": str(e)}
    )

# AI service error
try:
    response = await ai_service.chat(message)
except Exception as e:
    raise AIServiceException(
        message="AI service unavailable",
        details={"error": str(e)}
    )
```

## 🔍 Error Logging

All errors are automatically logged with structured context:

```python
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
```


# Response: 400 Bad Request
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "Start location cannot be empty",
  "details": {"field": "start_location"}
}
```

### Test Pydantic Validation
```bash
curl -X POST http://localhost:8000/api/plan-route \
  -H "Content-Type: application/json" \
  -d '{"invalid_field": 123}'

# Response: 422 Unprocessable Entity
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "validation_errors": [...]
  }
}
```

### Test Successful Request
```bash
curl -X POST http://localhost:8000/api/plan-route \
  -H "Content-Type: application/json" \
  -d '{
    "start_location":"Ankara",
    "destination":"Istanbul",
    "vehicle_model":"Tesla Model 3"
  }'

# Response: 200 OK
{
  "start": "Ankara",
  "destination": "Istanbul",
  "vehicle": "Tesla Model 3",
  "status": "calculated"
}
```

## 🎨 HTTP Status Code Reference

| Code | Exception Type | Description |
|------|---------------|-------------|
| 400 | ValidationException | Bad request - invalid input |
| 401 | AuthenticationException | Authentication required |
| 404 | VehicleNotFoundException, ChargingStationNotFoundException | Resource not found |
| 422 | RouteCalculationException, Pydantic Validation | Unprocessable entity |
| 429 | RateLimitException | Rate limit exceeded |
| 500 | Generic Exception | Internal server error |
| 503 | DatabaseException, RedisException, QdrantException, AIServiceException | Service unavailable |

## 🚀 Best Practices

1. **Always use specific exception types** - Don't use generic `Exception` for business logic errors
2. **Include context in details** - Add relevant information for debugging
3. **Re-raise validation exceptions** - Let global handler format the response
4. **Log before raising** - Add logging at the source for better debugging
5. **Don't expose internals** - Never include sensitive data in error messages

## 📊 Monitoring & Grafana Integration

Error logs are structured for easy integration with Grafana/Loki:

```json
{
  "level": "ERROR",
  "error_code": "DATABASE_ERROR",
  "status_code": 503,
  "path": "/api/vehicles",
  "method": "GET",
  "details": {...}
}
```

### Grafana Query Examples:
```logql
# All errors in last hour
{app="ev_backend"} |= "ERROR" | json

# Validation errors only
{app="ev_backend"} | json | error_code="VALIDATION_ERROR"

# Database errors
{app="ev_backend"} | json | error_code="DATABASE_ERROR"
```

## 🔄 Future Enhancements

- [ ] Error rate limiting per user
- [ ] Detailed error analytics dashboard
- [ ] Automatic error reporting to Sentry
- [ ] Custom error pages for frontend
- [ ] Multi-language error messages
- [ ] Error recovery strategies
