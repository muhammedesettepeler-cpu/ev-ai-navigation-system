"""Status check endpoints for database, Redis, and Qdrant services."""

# Standard library imports
import logging

# Third-party imports
from fastapi import APIRouter

# Local imports (services initialized in orchestrator)
import orchestrator

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/test-db")
async def test_database():
    """
    Test database connection.

    Returns:
        Connection status and details

    Raises:
        DatabaseException: If connection fails
    """
    try:
        return await orchestrator.database_service.test_connection()
    except Exception as e:
        from src.exceptions.custom_exceptions import DatabaseException

        raise DatabaseException(
            message="Failed to connect to database", details={"error": str(e)}
        )


@router.get("/redis-status")
async def get_redis_status():
    """
    Get Redis connection status.

    Returns:
        Redis connection information

    Raises:
        RedisException: If status check fails
    """
    try:
        return await orchestrator.redis_service.get_connection_status()
    except Exception as e:
        from src.exceptions.custom_exceptions import RedisException

        raise RedisException(
            message="Failed to get Redis status", details={"error": str(e)}
        )


@router.get("/qdrant-status")
async def get_qdrant_status():
    """
    Get Qdrant vector database status.

    Returns:
        Qdrant connection status
    """
    return {"status": "disabled", "message": "Qdrant currently disabled"}


@router.get("/qdrant-stats")
async def get_qdrant_stats():
    """
    Get Qdrant collection statistics.

    Returns:
        Collection statistics or unavailable message
    """
    return {"status": "disabled", "message": "Qdrant currently disabled"}
