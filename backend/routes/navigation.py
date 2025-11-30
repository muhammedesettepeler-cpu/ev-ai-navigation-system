"""
Navigation Routes - Route planning and optimization endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from services.navigation_service import NavigationService
from agents.route_optimizer import RouteOptimizerAgent
from models.navigation import RouteRequest, RouteResponse, Waypoint
from models.vehicle_models import VehicleSpecs

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency injection
def get_navigation_service() -> NavigationService:
    return NavigationService()

def get_route_optimizer() -> RouteOptimizerAgent:
    return RouteOptimizerAgent()

@router.post("/plan-route", response_model=RouteResponse)
async def plan_route(
    request: RouteRequest,
    nav_service: NavigationService = Depends(get_navigation_service),
    optimizer: RouteOptimizerAgent = Depends(get_route_optimizer)
):
    """
    Plan optimal route for electric vehicle with charging stops
    """
    try:
        logger.info(f"Planning route from {request.start} to {request.destination}")
        
        # Get vehicle specifications
        vehicle_specs_dict = await nav_service.get_vehicle_specs(request.vehicle_model)
        if not vehicle_specs_dict:
            raise HTTPException(status_code=400, detail="Vehicle model not found")
        
        # Convert preferences to dict if needed
        preferences_dict = request.preferences.dict() if request.preferences else None
        
        # Plan route with charging optimization
        # Note: RouteOptimizer expects VehicleSpecs but we pass dict (needs fixing in optimizer)
        route = await optimizer.optimize_route(
            start=request.start,
            destination=request.destination,
            vehicle_specs=vehicle_specs_dict,  # Pass dict for now
            current_battery_level=request.current_battery_level,
            preferences=preferences_dict
        )
        
        logger.info(f"Route planned successfully: {len(route.waypoints)} waypoints")
        return route
        
    except Exception as e:
        logger.error(f"Route planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Route planning failed: {str(e)}")

@router.get("/charging-stops")
async def get_charging_stops_along_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    vehicle_model: str,
    nav_service: NavigationService = Depends(get_navigation_service)
):
    """
    Get charging stations along a specific route
    """
    try:
        charging_stops = await nav_service.find_charging_stations_on_route(
            start_coords=(start_lat, start_lon),
            end_coords=(end_lat, end_lon),
            vehicle_model=vehicle_model
        )
        
        return {
            "charging_stations": charging_stops,
            "count": len(charging_stops)
        }
        
    except Exception as e:
        logger.error(f"Charging stops search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Charging stops search failed: {str(e)}")

@router.post("/optimize-existing-route")
async def optimize_existing_route(
    waypoints: List[Waypoint],
    vehicle_model: str,
    current_battery: float,
    nav_service: NavigationService = Depends(get_navigation_service)
):
    """
    Optimize an existing route - stub endpoint (not yet implemented in RouteOptimizerAgent)
    """
    try:
        # For now, return the waypoints as-is with a message
        # TODO: Implement optimize_existing_route in RouteOptimizerAgent
        return {
            "waypoints": waypoints,
            "message": "Route optimization feature coming soon",
            "current_battery": current_battery
        }
        
    except Exception as e:
        logger.error(f"Route optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@router.get("/route-alternatives")
async def get_route_alternatives(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    vehicle_model: str,
    max_alternatives: int = 3,
    nav_service: NavigationService = Depends(get_navigation_service)
):
    """
    Get alternative routes with different charging strategies
    """
    try:
        alternatives = await nav_service.get_route_alternatives(
            start=(start_lat, start_lon),
            end=(end_lat, end_lon),
            vehicle_model=vehicle_model,
            max_alternatives=max_alternatives
        )
        
        return {
            "alternatives": alternatives,
            "count": len(alternatives)
        }
        
    except Exception as e:
        logger.error(f"Route alternatives error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Route alternatives failed: {str(e)}")

@router.post("/calculate-energy-consumption")
async def calculate_energy_consumption(
    route_waypoints: List[Waypoint],
    vehicle_model: str,
    nav_service: NavigationService = Depends(get_navigation_service)
):
    """
    Calculate estimated energy consumption for a route
    """
    try:
        # Convert Waypoint objects to dicts for the service
        waypoints_data = [
            {
                "latitude": wp.latitude,
                "longitude": wp.longitude,
                "waypoint_type": wp.waypoint_type
            }
            for wp in route_waypoints
        ]
        
        consumption_data = await nav_service.calculate_energy_consumption(
            waypoints=waypoints_data,
            vehicle_model=vehicle_model
        )
        
        return consumption_data
        
    except Exception as e:
        logger.error(f"Energy calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Energy calculation failed: {str(e)}")

@router.post("/simple-route")
async def simple_route_planning(
    start_lat: float = Query(..., description="Starting latitude"),
    start_lon: float = Query(..., description="Starting longitude"),
    end_lat: float = Query(..., description="Destination latitude"),
    end_lon: float = Query(..., description="Destination longitude"),
    vehicle_range_km: float = Query(..., description="Vehicle range in km"),
    battery_capacity_kwh: float = Query(..., description="Battery capacity in kWh"),
    current_battery_percent: float = Query(80.0, description="Current battery percentage"),
    min_charge_percent: float = Query(20.0, description="Minimum charge before stopping"),
    preferred_charge_percent: float = Query(80.0, description="Target charge at stations")
):
    """
    Simple route planning endpoint using route_planning_service
    No complex dependencies - direct calculation
    """
    try:
        from services.route_planning_service import route_planning_service
        
        logger.info(f"Simple route: ({start_lat},{start_lon}) -> ({end_lat},{end_lon}), Range: {vehicle_range_km}km")
        
        route_data = route_planning_service.calculate_charging_stops(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            vehicle_range_km=vehicle_range_km,
            battery_capacity_kwh=battery_capacity_kwh,
            current_battery_percent=current_battery_percent,
            min_charge_percent=min_charge_percent,
            preferred_charge_percent=preferred_charge_percent
        )
        
        return route_data
        
    except Exception as e:
        logger.error(f"Simple route planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Route planning failed: {str(e)}")