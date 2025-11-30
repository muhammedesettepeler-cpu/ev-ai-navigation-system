"""
Data Models for Navigation System
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

class WaypointType(str, Enum):
    START = "start"
    DESTINATION = "destination"
    CHARGING = "charging"
    NAVIGATION = "navigation"
    WAYPOINT = "waypoint"

class Waypoint(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    waypoint_type: WaypointType = Field(..., description="Type of waypoint")
    charging_station_id: Optional[str] = Field(None, description="Charging station ID if applicable")
    estimated_arrival_time: Optional[datetime] = Field(None, description="Estimated arrival time")
    estimated_charging_time: Optional[int] = Field(None, description="Estimated charging time in minutes")
    estimated_battery_level: Optional[float] = Field(None, description="Estimated battery level at this point")
    distance_to_next: Optional[float] = Field(None, description="Distance to next waypoint in km")

class ChargingStop(BaseModel):
    station_id: str = Field(..., description="Unique station identifier")
    station_name: str = Field(..., description="Name of charging station")
    location: Tuple[float, float] = Field(..., description="Coordinates (lat, lon)")
    connector_type: str = Field(..., description="Type of charging connector")
    charging_power_kw: float = Field(..., description="Charging power in kW")
    estimated_charging_time_minutes: int = Field(..., description="Estimated charging time")
    estimated_cost: float = Field(..., description="Estimated charging cost")
    battery_level_before: float = Field(..., description="Battery level before charging")
    battery_level_after: float = Field(..., description="Battery level after charging")
    amenities: Optional[List[str]] = Field(default=[], description="Available amenities")

class RoutePreferences(BaseModel):
    avoid_highways: bool = Field(default=False, description="Avoid highway routes")
    prefer_fast_charging: bool = Field(default=True, description="Prefer fast charging stations")
    max_charging_stops: int = Field(default=5, description="Maximum number of charging stops")
    min_charging_power_kw: float = Field(default=50, description="Minimum charging power")
    preferred_charging_networks: List[str] = Field(default=[], description="Preferred charging networks")
    max_detour_for_charging_km: float = Field(default=10, description="Max detour for charging")

class RouteRequest(BaseModel):
    start: Tuple[float, float] = Field(..., description="Starting coordinates (lat, lon)")
    destination: Tuple[float, float] = Field(..., description="Destination coordinates (lat, lon)")
    vehicle_model: str = Field(..., description="Vehicle model identifier")
    current_battery_level: float = Field(..., ge=0, le=1, description="Current battery level (0-1)")
    preferences: Optional[RoutePreferences] = Field(default=None, description="Route preferences")

class RouteResponse(BaseModel):
    waypoints: List[Waypoint] = Field(..., description="Route waypoints")
    total_distance_km: float = Field(..., description="Total route distance")
    estimated_time_minutes: int = Field(..., description="Estimated total time")
    estimated_energy_consumption_kwh: float = Field(..., description="Estimated energy consumption")
    charging_stops: List[ChargingStop] = Field(..., description="Required charging stops")
    final_battery_level: float = Field(..., description="Expected final battery level")
    route_efficiency_score: float = Field(..., description="Route efficiency score 0-100")
    insights: List[str] = Field(default=[], description="AI-generated insights")
    preferences_applied: Dict[str, Any] = Field(default={}, description="Applied preferences")