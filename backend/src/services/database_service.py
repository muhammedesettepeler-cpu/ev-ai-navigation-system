"""Database service for PostgreSQL operations."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import asyncpg

logger = logging.getLogger(__name__)


class DatabaseService:
    """Handle database operations with asyncpg."""

    def __init__(self):
        """Initialize database configuration."""
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "admin123"),
            "database": os.getenv("POSTGRES_DB", "ev_navigation"),
        }

    async def get_connection(self):
        """Get database connection with error handling."""
        try:
            conn = await asyncpg.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise Exception(f"Database connection failed: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection and get stats."""
        try:
            conn = await self.get_connection()

            # Get vehicle count
            vehicle_count = await conn.fetchval("SELECT COUNT(*) FROM vehicle_models")

            # Get charging stations count
            try:
                charging_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM charging_stations"
                )
            except:
                charging_count = 0  # Table might not exist yet

            await conn.close()

            return {
                "status": "connected",
                "database": "PostgreSQL",
                "vehicles": vehicle_count,
                "charging_stations": charging_count,
                "host": self.db_config["host"],
                "port": self.db_config["port"],
            }

        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_all_vehicles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all vehicles from database."""
        try:
            conn = await self.get_connection()

            vehicles = await conn.fetch(
                """
                SELECT manufacturer, model_name, epa_range_km, 
                       battery_capacity_kwh, max_charging_power_kw
                FROM vehicle_models 
                ORDER BY manufacturer, model_name
                LIMIT $1
            """,
                limit,
            )

            await conn.close()

            # Format vehicles
            vehicle_list = []
            for v in vehicles:
                vehicle_list.append(
                    {
                        "brand": v["manufacturer"],
                        "model": v["model_name"],
                        "range_km": v["epa_range_km"],
                        "battery_kwh": v["battery_capacity_kwh"],
                        "charging_kw": v["max_charging_power_kw"],
                    }
                )

            return vehicle_list

        except Exception as e:
            logger.error(f"Get vehicles error: {e}")
            return []

    async def get_charging_stations(self) -> List[Dict[str, Any]]:
        """Get charging stations from database."""
        try:
            conn = await self.get_connection()

            stations = await conn.fetch("""
                SELECT name, latitude, longitude, power_kw, connector_types
                FROM charging_stations 
                WHERE is_active = TRUE
                LIMIT 100
            """)

            await conn.close()

            station_list = []
            for s in stations:
                station_list.append(
                    {
                        "name": s["name"],
                        "latitude": float(s["latitude"]),
                        "longitude": float(s["longitude"]),
                        "power_kw": s["power_kw"],
                        "connectors": s.get("connector_types", ["CCS2"]),
                    }
                )

            return station_list

        except Exception as e:
            logger.error(f"Get charging stations error: {e}")
            return []
