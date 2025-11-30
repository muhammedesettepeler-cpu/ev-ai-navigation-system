"""User authentication models for the EV Navigation System."""

# Standard library imports
from datetime import datetime

# Third-party imports
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

# Local imports
from src.database.connection import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    favorite_routes = relationship(
        "FavoriteRoute", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email='{self.email}')>"


class FavoriteRoute(Base):
    """Favorite route model for saving user's preferred routes."""

    __tablename__ = "favorite_routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    route_name = Column(String(200), nullable=False)
    start_address = Column(String(500))
    end_address = Column(String(500))
    start_lat = Column(String(50))
    start_lon = Column(String(50))
    end_lat = Column(String(50))
    end_lon = Column(String(50))
    vehicle_id = Column(Integer)
    vehicle_range_km = Column(Integer)
    battery_capacity_kwh = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation of FavoriteRoute."""
        return f"<FavoriteRoute(id={self.id}, name='{self.route_name}')>"
