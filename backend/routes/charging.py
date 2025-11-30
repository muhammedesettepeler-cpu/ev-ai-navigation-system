"""
Charging Station Routes - Endpoints for charging station information
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

from services.charging_station_service import charging_station_service

logger = logging.getLogger(__name__)
router = APIRouter()

class ChargingStationInfo(BaseModel):
    id: str
    name: str
    network: str
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    connector_types: List[str]
    max_power_kw: int
    pricing_info: Dict[str, Any]
    amenities: List[str]
    is_available: bool
    distance_km: Optional[float] = None

class ChargingStationSearch(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 50
    connector_types: Optional[List[str]] = None
    min_power_kw: Optional[int] = None
    networks: Optional[List[str]] = None

# Mock charging stations data
MOCK_CHARGING_STATIONS = [
    {
        "id": "supercharger_001",
        "name": "Tesla Supercharger - Downtown",
        "network": "Tesla",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "address": "123 Electric Ave",
        "city": "New York",
        "state": "NY",
        "connector_types": ["Tesla", "CCS1"],
        "max_power_kw": 250,
        "pricing_info": {"per_kwh": 0.28, "idle_fee": 0.50},
        "amenities": ["WiFi", "Restaurant", "Shopping"],
        "is_available": True
    },
    {
        "id": "ea_002",
        "name": "Electrify America - Mall Plaza",
        "network": "Electrify America", 
        "latitude": 40.7589,
        "longitude": -73.9851,
        "address": "456 Charging Blvd",
        "city": "New York",
        "state": "NY",
        "connector_types": ["CCS1", "CHAdeMO"],
        "max_power_kw": 350,
        "pricing_info": {"per_kwh": 0.31, "per_minute": 0.16},
        "amenities": ["WiFi", "Shopping", "Food Court"],
        "is_available": True
    },
    {
        "id": "evgo_003",
        "name": "EVgo Fast Charger",
        "network": "EVgo",
        "latitude": 40.7505,
        "longitude": -73.9934,
        "address": "789 Power Street", 
        "city": "New York",
        "state": "NY",
        "connector_types": ["CCS1", "CHAdeMO"],
        "max_power_kw": 100,
        "pricing_info": {"per_kwh": 0.25, "membership_discount": 0.05},
        "amenities": ["WiFi", "Convenience Store"],
        "is_available": False
    }
]

@router.get("/stations")
async def get_charging_stations(
    lat: Optional[float] = Query(None, description="Latitude for radius search"),
    lon: Optional[float] = Query(None, description="Longitude for radius search"), 
    radius: float = Query(100, description="Search radius in km"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_power: Optional[int] = Query(None, description="Minimum power in kW"),
    max_power: Optional[int] = Query(None, description="Maximum power in kW")
):
    """
    Get charging stations with optional filters
    - If lat/lon provided: returns stations within radius
    - If city provided: returns stations in that city
    - If no filters: returns all stations
    """
    try:
        # City-based search
        if city:
            logger.info(f"Searching charging stations in city: {city}")
            stations = charging_station_service.get_stations_by_city(city)
            return {
                "count": len(stations),
                "stations": stations,
                "filter": {"type": "city", "value": city}
            }
        
        # Radius-based search
        if lat is not None and lon is not None:
            logger.info(f"Searching charging stations near ({lat}, {lon}) within {radius}km")
            stations = charging_station_service.get_stations_in_radius(lat, lon, radius)
        else:
            # Get all stations
            logger.info("Getting all charging stations")
            stations = charging_station_service.get_all_stations()
        
        # Apply power filters
        if min_power is not None or max_power is not None:
            min_p = min_power if min_power is not None else 0
            max_p = max_power if max_power is not None else 1000
            stations = [s for s in stations if min_p <= s.get('power_kw', 0) <= max_p]
        
        logger.info(f"Found {len(stations)} charging stations")
        return {
            "count": len(stations),
            "stations": stations,
            "filter": {
                "radius_km": radius if lat and lon else None,
                "min_power": min_power,
                "max_power": max_power
            }
        }
        
    except Exception as e:
        logger.error(f"Charging station search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/networks")
async def get_charging_networks():
    """
    Get information about charging networks
    """
    return {
        "networks": [
            {
                "name": "Tesla Supercharger",
                "connector_types": ["Tesla", "CCS1"],
                "max_power_kw": 250,
                "coverage": "Extensive highway coverage",
                "membership_required": False,
                "pricing_model": "Per kWh"
            },
            {
                "name": "Electrify America",
                "connector_types": ["CCS1", "CHAdeMO"],
                "max_power_kw": 350,
                "coverage": "Major highways and cities",
                "membership_required": False,
                "pricing_model": "Per kWh or per minute"
            },
            {
                "name": "EVgo",
                "connector_types": ["CCS1", "CHAdeMO"],
                "max_power_kw": 100,
                "coverage": "Urban areas",
                "membership_required": False,
                "pricing_model": "Per kWh with membership discounts"
            },
            {
                "name": "ChargePoint",
                "connector_types": ["CCS1", "Type2", "CHAdeMO"],
                "max_power_kw": 62,
                "coverage": "Widespread Level 2 charging",
                "membership_required": False,
                "pricing_model": "Varies by location"
            }
        ]
    }

@router.get("/connectors")
async def get_connector_info():
    """
    Get information about charging connector types
    """
    return {
        "connectors": [
            {
                "type": "CCS1",
                "name": "Combined Charging System (North America)",
                "power_levels": ["Level 2 AC", "DC Fast Charging"],
                "max_power_kw": 350,
                "vehicles": ["BMW", "Mercedes", "Volkswagen", "Hyundai", "Ford"]
            },
            {
                "type": "CCS2", 
                "name": "Combined Charging System (Europe)",
                "power_levels": ["Level 2 AC", "DC Fast Charging"],
                "max_power_kw": 350,
                "vehicles": ["BMW", "Mercedes", "Audi", "Volkswagen"]
            },
            {
                "type": "CHAdeMO",
                "name": "CHAdeMO (Japan)",
                "power_levels": ["DC Fast Charging"],
                "max_power_kw": 400,
                "vehicles": ["Nissan Leaf", "Nissan Ariya"]
            },
            {
                "type": "Tesla",
                "name": "Tesla Supercharger",
                "power_levels": ["DC Fast Charging"],
                "max_power_kw": 250,
                "vehicles": ["Tesla Model S", "Tesla Model 3", "Tesla Model X", "Tesla Model Y"]
            },
            {
                "type": "Type2",
                "name": "Type 2 (Mennekes)",
                "power_levels": ["Level 2 AC"],
                "max_power_kw": 22,
                "vehicles": ["Most European EVs"]
            }
        ]
    }

@router.get("/pricing")
async def get_charging_pricing():
    """
    Get pricing information for different charging networks
    """
    return {
        "pricing_comparison": [
            {
                "network": "Tesla Supercharger",
                "pricing_model": "Per kWh",
                "average_cost_per_kwh": 0.28,
                "peak_pricing": True,
                "membership_discount": None,
                "idle_fees": "Yes, after charging complete"
            },
            {
                "network": "Electrify America", 
                "pricing_model": "Per kWh or per minute",
                "average_cost_per_kwh": 0.31,
                "peak_pricing": False,
                "membership_discount": "Pass+ membership",
                "idle_fees": "Yes, after 10 minutes"
            },
            {
                "network": "EVgo",
                "pricing_model": "Per kWh",
                "average_cost_per_kwh": 0.25,
                "peak_pricing": True,
                "membership_discount": "Up to $0.05/kWh",
                "idle_fees": "Yes, varies by location"
            }
        ],
        "cost_estimation": {
            "description": "Estimated cost to charge from 20% to 80% battery",
            "examples": [
                {"vehicle": "Tesla Model 3", "battery_kwh": 82, "cost_range": "$12-16"},
                {"vehicle": "BMW iX", "battery_kwh": 111, "cost_range": "$16-22"},
                {"vehicle": "Nissan Leaf", "battery_kwh": 62, "cost_range": "$9-13"}
            ]
        }
    }

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate approximate distance between two points in km
    (Simplified for demo - use proper geospatial calculations in production)
    """
    import math
    
    # Convert to radians
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in km
    radius = 6371
    
    return radius * c