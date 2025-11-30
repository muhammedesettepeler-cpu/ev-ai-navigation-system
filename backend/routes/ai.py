"""AI-powered chat and vehicle search endpoints."""

# Standard library imports
import logging

# Third-party imports
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Local imports
import orchestrator

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Pydantic models
class ChatMessage(BaseModel):
    """Chat message request model."""

    message: str


class VehicleSearchQuery(BaseModel):
    """Vehicle search query model."""

    query: str


@router.post("/chat")
async def ai_chat(request: ChatMessage):
    """
    AI-powered chat for EV navigation questions.

    Args:
        request: User message

    Returns:
        AI response

    Raises:
        HTTPException: If chat fails
    """
    try:
        response = await orchestrator.ai_service.handleConversation(request.message)
        return {
            "success": True,
            "response": response,
            "message": "Chat processed successfully",
        }
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message",
        )


@router.post("/search-vehicles")
async def search_vehicles(request: VehicleSearchQuery):
    """
    Search for vehicles using natural language query.

    Args:
        request: Search query

    Returns:
        Matching vehicles

    Raises:
        HTTPException: If search fails
    """
    try:
        # This would integrate with Qdrant semantic search
        # For now, return simple database query
        vehicles = await orchestrator.database_service.get_all_vehicles()

        # Simple text matching (can be enhanced with Qdrant later)
        query_lower = request.query.lower()
        filtered = [
            v
            for v in vehicles
            if query_lower in v.get("brand", "").lower()
            or query_lower in v.get("model", "").lower()
        ]

        return {
            "success": True,
            "vehicles": filtered,
            "count": len(filtered),
            "query": request.query,
        }
    except Exception as e:
        logger.error(f"Vehicle search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search vehicles",
        )
