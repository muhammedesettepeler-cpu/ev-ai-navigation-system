"""
Database initialization and connection setup
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    JSON,
    Text,
    select,
    and_,
)
import os
import math
from datetime import datetime
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres123@localhost:5432/ev_navigation",
)

# SQLAlchemy setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()


# Database Models
class VehicleModel(Base):
    __tablename__ = "vehicle_models"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, index=True)
    manufacturer = Column(String(50), index=True)
    model_name = Column(String(100), index=True)
    year = Column(Integer)
    category = Column(String(20))
    battery_capacity_kwh = Column(Float)
    epa_range_km = Column(Float)
    energy_consumption_kwh_per_100km = Column(Float)
    max_charging_power_kw = Column(Float)
    supported_connectors = Column(JSON)
    specifications = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String(100), unique=True, index=True)
    name = Column(String(200))
    network = Column(String(100))
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    country = Column(String(50))
    connector_types = Column(JSON)
    charging_powers = Column(JSON)
    pricing = Column(JSON)
    amenities = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_verified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    start_latitude = Column(Float)
    start_longitude = Column(Float)
    end_latitude = Column(Float)
    end_longitude = Column(Float)
    vehicle_model_id = Column(String(100))
    waypoints = Column(JSON)
    charging_stops = Column(JSON)
    total_distance_km = Column(Float)
    estimated_time_minutes = Column(Integer)
    estimated_energy_kwh = Column(Float)
    route_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserQuery(Base):
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    query_text = Column(Text)
    query_type = Column(String(50))  # route_planning, charging_info, vehicle_info, etc.
    response_text = Column(Text)
    context_used = Column(JSON)
    satisfaction_score = Column(Float)  # User feedback
    created_at = Column(DateTime, default=datetime.utcnow)


# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Initialize database
async def init_db():
    """Create database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


# Close database connections
async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


# Database utilities
class DatabaseManager:
    """Database management utilities"""

    @staticmethod
    async def add_vehicle_model(vehicle_data: dict) -> int:
        """Add a vehicle model to database"""
        async with AsyncSessionLocal() as session:
            vehicle = VehicleModel(**vehicle_data)
            session.add(vehicle)
            await session.commit()
            await session.refresh(vehicle)
            return vehicle.id  # type: ignore

    @staticmethod
    async def get_vehicle_by_model_id(model_id: str) -> VehicleModel:
        """Get vehicle by model ID"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(VehicleModel).where(VehicleModel.model_id == model_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def add_charging_station(station_data: dict) -> int:
        """Add charging station to database"""
        async with AsyncSessionLocal() as session:
            station = ChargingStation(**station_data)
            session.add(station)
            await session.commit()
            await session.refresh(station)
            return station.id  # type: ignore

    @staticmethod
    async def get_charging_stations_near(lat: float, lon: float, radius_km: float = 50):
        """Get charging stations within radius"""
        # This would use PostGIS in a real implementation
        # For now, we'll use a simple bounding box
        lat_delta = radius_km / 111  # Rough conversion
        lon_delta = radius_km / (111 * abs(math.cos(math.radians(lat))))

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChargingStation).where(
                    and_(
                        ChargingStation.latitude.between(
                            lat - lat_delta, lat + lat_delta
                        ),
                        ChargingStation.longitude.between(
                            lon - lon_delta, lon + lon_delta
                        ),
                        ChargingStation.is_active,
                    )
                )
            )
            return result.scalars().all()

    @staticmethod
    async def save_route(route_data: dict) -> int:
        """Save a calculated route"""
        async with AsyncSessionLocal() as session:
            route = Route(**route_data)
            session.add(route)
            await session.commit()
            await session.refresh(route)
            return route.id  # type: ignore

    @staticmethod
    async def log_user_query(query_data: dict) -> int:
        """Log user query for analytics"""
        async with AsyncSessionLocal() as session:
            query = UserQuery(**query_data)
            session.add(query)
            await session.commit()
            await session.refresh(query)
            return query.id  # type: ignore
