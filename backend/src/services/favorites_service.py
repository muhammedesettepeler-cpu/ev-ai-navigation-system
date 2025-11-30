logger = logging.getLogger(__name__)


class FavoritesService:
    """Handle favorite routes CRUD operations."""

    async def create_favorite(
        self,
        user_id: int,
        route_name: str,
        start_address: str,
        end_address: str,
        start_lat: str,
        start_lon: str,
        end_lat: str,
        end_lon: str,
        vehicle_id: Optional[int] = None,
        vehicle_range_km: Optional[int] = None,
        battery_capacity_kwh: Optional[int] = None,
    ) -> Optional[Dict[str, any]]:
        """
        Save a new favorite route for user.

        Args:
            user_id: User's database ID
            route_name: Name for the route
            start_address: Starting address
            end_address: Destination address
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Ending latitude
            end_lon: Ending longitude
            vehicle_id: Optional vehicle ID
            vehicle_range_km: Optional vehicle range
            battery_capacity_kwh: Optional battery capacity

        Returns:
            Created favorite route data if successful, None if duplicate name

        Raises:
            Exception: If database operation fails
        """
        async with AsyncSessionLocal() as session:
            # Check for duplicate route name for this user
            result = await session.execute(
                select(FavoriteRoute).where(
                    FavoriteRoute.user_id == user_id,
                    FavoriteRoute.route_name == route_name,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.warning(
                    f"Duplicate favorite route name '{route_name}' for user {user_id}"
                )
                return None

            # Create new favorite route
            new_favorite = FavoriteRoute(
                user_id=user_id,
                route_name=route_name,
                start_address=start_address,
                end_address=end_address,
                start_lat=start_lat,
                start_lon=start_lon,
                end_lat=end_lat,
                end_lon=end_lon,
                vehicle_id=vehicle_id,
                vehicle_range_km=vehicle_range_km,
                battery_capacity_kwh=battery_capacity_kwh,
                created_at=datetime.utcnow(),
            )

            session.add(new_favorite)
            await session.commit()
            await session.refresh(new_favorite)

            logger.info(f"Favorite route '{route_name}' created for user {user_id}")

            return self._format_favorite(new_favorite)

    async def get_user_favorites(self, user_id: int) -> List[Dict[str, any]]:
        """
        Get all favorite routes for a user.

        Args:
            user_id: User's database ID

        Returns:
            List of favorite route dictionaries
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(FavoriteRoute)
                .where(FavoriteRoute.user_id == user_id)
                .order_by(FavoriteRoute.created_at.desc())
            )
            favorites = result.scalars().all()

            return [self._format_favorite(fav) for fav in favorites]

    async def get_favorite_by_id(
        self, favorite_id: int, user_id: int
    ) -> Optional[Dict[str, any]]:
        """
        Get a specific favorite route.

        Args:
            favorite_id: Favorite route ID
            user_id: User's database ID (for authorization)

        Returns:
            Favorite route data if found and authorized, None otherwise
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(FavoriteRoute).where(
                    FavoriteRoute.id == favorite_id, FavoriteRoute.user_id == user_id
                )
            )
            favorite = result.scalar_one_or_none()

            if favorite:
                return self._format_favorite(favorite)
            return None

    async def delete_favorite(self, favorite_id: int, user_id: int) -> bool:
        """
        Delete a favorite route.

        Args:
            favorite_id: Favorite route ID to delete
            user_id: User's database ID (for authorization)

        Returns:
            True if deleted successfully, False if not found
        """
        async with AsyncSessionLocal() as session:
            # Check if favorite exists and belongs to user
            result = await session.execute(
                select(FavoriteRoute).where(
                    FavoriteRoute.id == favorite_id, FavoriteRoute.user_id == user_id
                )
            )
            favorite = result.scalar_one_or_none()

            if not favorite:
                logger.warning(
                    f"Favorite {favorite_id} not found or unauthorized for user {user_id}"
                )
                return False

            await session.delete(favorite)
            await session.commit()

            logger.info(f"Favorite route {favorite_id} deleted by user {user_id}")
            return True

    async def update_favorite(
        self, favorite_id: int, user_id: int, route_name: Optional[str] = None
    ) -> Optional[Dict[str, any]]:
        """
        Update a favorite route (currently only supports renaming).

        Args:
            favorite_id: Favorite route ID
            user_id: User's database ID (for authorization)
            route_name: New name for the route

        Returns:
            Updated favorite route data if successful, None if not found
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(FavoriteRoute).where(
                    FavoriteRoute.id == favorite_id, FavoriteRoute.user_id == user_id
                )
            )
            favorite = result.scalar_one_or_none()

            if not favorite:
                return None

            if route_name:
                favorite.route_name = route_name
                favorite.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(favorite)

            logger.info(f"Favorite route {favorite_id} updated by user {user_id}")
            return self._format_favorite(favorite)

    def _format_favorite(self, favorite: FavoriteRoute) -> Dict[str, any]:
        """
        Format FavoriteRoute model to dictionary.

        Args:
            favorite: FavoriteRoute model instance

        Returns:
            Formatted dictionary
        """
        return {
            "id": favorite.id,
            "route_name": favorite.route_name,
            "start_address": favorite.start_address,
            "end_address": favorite.end_address,
            "start_lat": favorite.start_lat,
            "start_lon": favorite.start_lon,
            "end_lat": favorite.end_lat,
            "end_lon": favorite.end_lon,
            "vehicle_id": favorite.vehicle_id,
            "vehicle_range_km": favorite.vehicle_range_km,
            "battery_capacity_kwh": favorite.battery_capacity_kwh,
            "created_at": favorite.created_at.isoformat(),
            "updated_at": favorite.updated_at.isoformat(),
        }
