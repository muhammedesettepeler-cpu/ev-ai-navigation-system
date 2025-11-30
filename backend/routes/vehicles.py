"""
Vehicle Routes - Endpoints for vehicle model information
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class VehicleModel(BaseModel):
    id: int
    manufacturer: str
    model: str
    year: int
    category: str
    battery_capacity_kwh: float
    range_km: int
    energy_consumption_kwh_per_100km: float
    fast_charge_power_kw: Optional[int] = None
    supported_connectors: List[str]
    price_usd: int
    acceleration_0_100_kmh: Optional[float] = None
    top_speed_kmh: Optional[int] = None

class VehicleComparison(BaseModel):
    vehicles: List[VehicleModel]
    comparison_metrics: Dict[str, Any]

# Import vehicle data from our data module
import sys
from pathlib import Path
# Add parent directory to path to access data module
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from data.car_models.ev_models import FLAT_CAR_MODELS, get_car_by_id, get_cars_by_manufacturer

@router.get("/", response_model=List[VehicleModel])
async def get_all_vehicles(
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_range: Optional[int] = Query(None, description="Minimum range in km"),
    max_price: Optional[int] = Query(None, description="Maximum price in USD")
):
    """
    Get all available vehicle models with optional filters
    """
    try:
        vehicles = FLAT_CAR_MODELS.copy()
        
        # Apply filters
        if manufacturer:
            vehicles = [v for v in vehicles if v["manufacturer"].lower() == manufacturer.lower()]
        
        if category:
            vehicles = [v for v in vehicles if v["category"] == category]
        
        if min_range:
            vehicles = [v for v in vehicles if v["range_km"] >= min_range]
        
        if max_price:
            vehicles = [v for v in vehicles if v["price_usd"] <= max_price]
        
        # Convert to VehicleModel format
        vehicle_models = []
        for vehicle in vehicles:
            model = VehicleModel(
                id=vehicle["id"],
                manufacturer=vehicle["manufacturer"],
                model=vehicle["model"],
                year=vehicle["year"],
                category=vehicle["category"],
                battery_capacity_kwh=vehicle["battery_capacity_kwh"],
                range_km=vehicle["range_km"],
                energy_consumption_kwh_per_100km=vehicle["energy_consumption_kwh_per_100km"],
                fast_charge_power_kw=vehicle.get("fast_charge_power_kw"),
                supported_connectors=vehicle["supported_connectors"],
                price_usd=vehicle["price_usd"],
                acceleration_0_100_kmh=vehicle.get("acceleration_0_100_kmh"),
                top_speed_kmh=vehicle.get("top_speed_kmh")
            )
            vehicle_models.append(model)
        
        logger.info(f"Returning {len(vehicle_models)} vehicles")
        return vehicle_models
        
    except Exception as e:
        logger.error(f"Vehicle query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vehicle query failed: {str(e)}")

@router.get("/manufacturers")
async def get_manufacturers():
    """
    Get list of available manufacturers
    """
    manufacturers = list(set(v["manufacturer"] for v in FLAT_CAR_MODELS))
    return {
        "manufacturers": sorted(manufacturers),
        "count": len(manufacturers)
    }

@router.get("/categories")
async def get_categories():
    """
    Get list of available vehicle categories
    """
    categories = list(set(v["category"] for v in FLAT_CAR_MODELS))
    return {
        "categories": sorted(categories),
        "descriptions": {
            "sedan": "Traditional four-door passenger cars",
            "suv": "Sport Utility Vehicles with higher ground clearance",
            "hatchback": "Compact cars with rear hatch door"
        }
    }

@router.get("/{vehicle_id}", response_model=VehicleModel)
async def get_vehicle_by_id(vehicle_id: str):
    """
    Get detailed information for a specific vehicle
    """
    try:
        vehicle_data = get_car_by_id(vehicle_id)
        
        if not vehicle_data:
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
        
        vehicle = VehicleModel(
            id=vehicle_data["id"],
            manufacturer=vehicle_data["manufacturer"],
            model=vehicle_data["model"], 
            year=vehicle_data["year"],
            category=vehicle_data["category"],
            battery_capacity_kwh=vehicle_data["battery_capacity_kwh"],
            range_km=vehicle_data["range_km"],
            energy_consumption_kwh_per_100km=vehicle_data["energy_consumption_kwh_per_100km"],
            fast_charge_power_kw=vehicle_data.get("fast_charge_power_kw"),
            supported_connectors=vehicle_data["supported_connectors"],
            price_usd=vehicle_data["price_usd"],
            acceleration_0_100_kmh=vehicle_data.get("acceleration_0_100_kmh"),
            top_speed_kmh=vehicle_data.get("top_speed_kmh")
        )
        
        return vehicle
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vehicle lookup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vehicle lookup failed: {str(e)}")

@router.post("/compare", response_model=VehicleComparison)
async def compare_vehicles(vehicle_ids: List[str]):
    """
    Compare multiple vehicles side by side
    """
    try:
        if len(vehicle_ids) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 vehicles can be compared")
        
        vehicles = []
        for vehicle_id in vehicle_ids:
            vehicle_data = get_car_by_id(vehicle_id)
            if not vehicle_data:
                raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
            
            vehicle = VehicleModel(
                id=vehicle_data["id"],
                manufacturer=vehicle_data["manufacturer"],
                model=vehicle_data["model"],
                year=vehicle_data["year"],
                category=vehicle_data["category"],
                battery_capacity_kwh=vehicle_data["battery_capacity_kwh"],
                range_km=vehicle_data["range_km"],
                energy_consumption_kwh_per_100km=vehicle_data["energy_consumption_kwh_per_100km"],
                fast_charge_power_kw=vehicle_data.get("fast_charge_power_kw"),
                supported_connectors=vehicle_data["supported_connectors"],
                price_usd=vehicle_data["price_usd"],
                acceleration_0_100_kmh=vehicle_data.get("acceleration_0_100_kmh"),
                top_speed_kmh=vehicle_data.get("top_speed_kmh")
            )
            vehicles.append(vehicle)
        
        # Calculate comparison metrics
        ranges = [v.range_km for v in vehicles]
        prices = [v.price_usd for v in vehicles]
        charging_powers = [v.fast_charge_power_kw or 0 for v in vehicles]
        
        comparison_metrics = {
            "range_comparison": {
                "highest": max(ranges),
                "lowest": min(ranges),
                "average": sum(ranges) / len(ranges)
            },
            "price_comparison": {
                "highest": max(prices),
                "lowest": min(prices),
                "average": sum(prices) / len(prices)
            },
            "charging_speed": {
                "fastest": max(charging_powers),
                "slowest": min(charging_powers),
                "average": sum(charging_powers) / len(charging_powers)
            },
            "efficiency_winner": min(vehicles, key=lambda x: x.energy_consumption_kwh_per_100km).model,
            "value_winner": min(vehicles, key=lambda x: x.price_usd / x.range_km).model
        }
        
        return VehicleComparison(
            vehicles=vehicles,
            comparison_metrics=comparison_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vehicle comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/recommendations/by-use-case")
async def get_recommendations_by_use_case(
    use_case: str = Query(..., description="Use case: daily_commute, long_distance, family, luxury, budget"),
    budget: Optional[int] = Query(None, description="Maximum budget in USD")
):
    """
    Get vehicle recommendations based on use case
    """
    try:
        all_vehicles = FLAT_CAR_MODELS.copy()
        
        # Apply budget filter
        if budget:
            all_vehicles = [v for v in all_vehicles if v["price_usd"] <= budget]
        
        recommendations = []
        
        if use_case == "daily_commute":
            # Prioritize efficiency and value
            candidates = sorted(all_vehicles, key=lambda x: x["energy_consumption_kwh_per_100km"])
            recommendations = candidates[:3]
            
        elif use_case == "long_distance":
            # Prioritize range and fast charging
            candidates = sorted(all_vehicles, key=lambda x: (-x["range_km"], -(x.get("fast_charge_power_kw") or 0)))
            recommendations = candidates[:3]
            
        elif use_case == "family":
            # Prioritize SUVs and space
            candidates = [v for v in all_vehicles if v["category"] == "suv"]
            candidates = sorted(candidates, key=lambda x: -x["range_km"])
            recommendations = candidates[:3]
            
        elif use_case == "luxury":
            # Prioritize premium features and performance
            candidates = sorted(all_vehicles, key=lambda x: -x["price_usd"])
            recommendations = candidates[:3]
            
        elif use_case == "budget":
            # Prioritize lowest cost
            candidates = sorted(all_vehicles, key=lambda x: x["price_usd"])
            recommendations = candidates[:3]
        
        return {
            "use_case": use_case,
            "recommendations": recommendations,
            "criteria": f"Optimized for {use_case.replace('_', ' ')} use case",
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")