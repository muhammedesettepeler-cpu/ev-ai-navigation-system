"""Favorite routes endpoints for managing user's saved routes."""

# Standard library imports
import logging
from typing import Annotated

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

# Local imports
from routes.auth import get_current_user
from src.services.favorites_service import FavoritesService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize service
favorites_service = FavoritesService()


# Pydantic models
class FavoriteRouteCreate(BaseModel):
    """Create favorite route request model."""

    route_name: str
    start_address: str
    end_address: str
    start_lat: str
    start_lon: str
    end_lat: str
    end_lon: str
    vehicle_id: int | None = None
    vehicle_range_km: int | None = None
    battery_capacity_kwh: int | None = None


class FavoriteRouteUpdate(BaseModel):
    """Update favorite route request model."""

    route_name: str


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_favorite_route(
    request: FavoriteRouteCreate, user_id: Annotated[int, Depends(get_current_user)]
):
    """
    Save a new favorite route for the authenticated user.

    Args:
        request: Favorite route data
        user_id: Authenticated user ID from token

    Returns:
        Created favorite route

    Raises:
        HTTPException: If duplicate name or creation fails
    """
    try:
        favorite = await favorites_service.create_favorite(
            user_id=user_id,
            route_name=request.route_name,
            start_address=request.start_address,
            end_address=request.end_address,
            start_lat=request.start_lat,
            start_lon=request.start_lon,
            end_lat=request.end_lat,
            end_lon=request.end_lon,
            vehicle_id=request.vehicle_id,
            vehicle_range_km=request.vehicle_range_km,
            battery_capacity_kwh=request.battery_capacity_kwh,
        )

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Route name '{request.route_name}' already exists",
            )

        logger.info(f"Favorite route created: {request.route_name} for user {user_id}")
        return {
            "success": True,
            "favorite": favorite,
            "message": "Favorite route saved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create favorite error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save favorite route",
        )


@router.get("/")
async def get_user_favorites(user_id: Annotated[int, Depends(get_current_user)]):
    """
    Get all favorite routes for the authenticated user.

    Args:
        user_id: Authenticated user ID from token

    Returns:
        List of user's favorite routes

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        favorites = await favorites_service.get_user_favorites(user_id)

        return {"success": True, "favorites": favorites, "count": len(favorites)}

    except Exception as e:
        logger.error(f"Get favorites error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve favorites",
        )


@router.get("/{favorite_id}")
async def get_favorite_by_id(
    favorite_id: int, user_id: Annotated[int, Depends(get_current_user)]
):
    """
    Get a specific favorite route by ID.

    Args:
        favorite_id: Favorite route ID
        user_id: Authenticated user ID from token

    Returns:
        Favorite route data

    Raises:
        HTTPException: If not found or unauthorized
    """
    try:
        favorite = await favorites_service.get_favorite_by_id(favorite_id, user_id)

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Favorite route not found"
            )

        return {"success": True, "favorite": favorite}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get favorite error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve favorite",
        )


@router.put("/{favorite_id}")
async def update_favorite_route(
    favorite_id: int,
    request: FavoriteRouteUpdate,
    user_id: Annotated[int, Depends(get_current_user)],
):
    """
    Update a favorite route (rename).

    Args:
        favorite_id: Favorite route ID
        request: Update data
        user_id: Authenticated user ID from token

    Returns:
        Updated favorite route

    Raises:
        HTTPException: If not found or unauthorized
    """
    try:
        favorite = await favorites_service.update_favorite(
            favorite_id=favorite_id, user_id=user_id, route_name=request.route_name
        )

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Favorite route not found"
            )

        logger.info(f"Favorite route {favorite_id} updated by user {user_id}")
        return {
            "success": True,
            "favorite": favorite,
            "message": "Favorite route updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update favorite error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update favorite",
        )


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite_route(
    favorite_id: int, user_id: Annotated[int, Depends(get_current_user)]
):
    """
    Delete a favorite route.

    Args:
        favorite_id: Favorite route ID
        user_id: Authenticated user ID from token

    Returns:
        None (204 No Content on success)

    Raises:
        HTTPException: If not found or unauthorized
    """
    try:
        deleted = await favorites_service.delete_favorite(favorite_id, user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Favorite route not found"
            )

        logger.info(f"Favorite route {favorite_id} deleted by user {user_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete favorite error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete favorite",
        )
