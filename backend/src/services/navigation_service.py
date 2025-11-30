"""
Navigation Service - Core business logic for route planning and optimization
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import math
from datetime import datetime

if TYPE_CHECKING:
    from models.navigation import Waypoint

logger = logging.getLogger(__name__)

class NavigationService:
    """
    Core navigation service for EV route planning
    """
    
    def __init__(self):
        # Mock data for demonstration
        self.vehicle_specs_cache = {}
        
    async def get_vehicle_specs(self, vehicle_model: str) -> Optional[Dict[str, Any]]:
        """
        Get vehicle specifications by model name
        
        Args:
            vehicle_model: Vehicle model identifier
            
        Returns:
            Vehicle specifications or None if not found
        """
        try:
            # Import here to avoid circular imports
            from data.car_models.ev_models import get_car_by_id, FLAT_CAR_MODELS
            
            # First try exact ID match
            specs = get_car_by_id(vehicle_model)
            if specs:
                return self._normalize_vehicle_specs(specs)
            
            # Try fuzzy matching by model name
            for vehicle in FLAT_CAR_MODELS:
                if vehicle_model.lower() in vehicle["model"].lower() or vehicle["model"].lower() in vehicle_model.lower():
                    return self._normalize_vehicle_specs(vehicle)
            
            logger.warning(f"Vehicle model not found: {vehicle_model}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vehicle specs: {e}")
            return None
    
    def _normalize_vehicle_specs(self, raw_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize vehicle specs to standard format"""
        return {
            "model": raw_specs["model"],
            "manufacturer": raw_specs["manufacturer"],
            "battery_capacity_kwh": raw_specs["battery_capacity_kwh"],
            "range_km": raw_specs["epa_range_km"],
            "energy_consumption_kwh_per_100km": raw_specs["energy_consumption_kwh_per_100km"],
            "max_charging_power_kw": raw_specs["max_charging_power_kw"],
            "supported_connectors": raw_specs["supported_connectors"]
        }
    
    async def calculate_base_route(
        self, 
        start: Tuple[float, float], 
        destination: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Calculate base route without charging considerations
        
        Args:
            start: Starting coordinates (lat, lon)
            destination: Destination coordinates (lat, lon)
            
        Returns:
            Route information with segments and distance
        """
        try:
            # Simple great circle distance calculation for demo
            distance_km = self._calculate_distance(start[0], start[1], destination[0], destination[1])
            
            # Create mock route segments
            segments = []
            num_segments = max(2, int(distance_km / 100))  # Roughly 100km per segment
            
            for i in range(num_segments):
                segment_start_lat = start[0] + (destination[0] - start[0]) * (i / num_segments)
                segment_start_lon = start[1] + (destination[1] - start[1]) * (i / num_segments)
                segment_end_lat = start[0] + (destination[0] - start[0]) * ((i + 1) / num_segments)
                segment_end_lon = start[1] + (destination[1] - start[1]) * ((i + 1) / num_segments)
                
                segment_distance = distance_km / num_segments
                
                segment = {
                    "segment_id": i,
                    "start": (segment_start_lat, segment_start_lon),
                    "end": (segment_end_lat, segment_end_lon),
                    "distance_km": segment_distance,
                    "estimated_time_minutes": int(segment_distance * 1.2),  # Rough time estimate
                    "elevation_gain_m": max(0, (i % 3 - 1) * 100),  # Mock elevation changes
                    "avg_speed_kmh": 80
                }
                segments.append(segment)
            
            return {
                "start": start,
                "destination": destination,
                "total_distance_km": distance_km,
                "estimated_time_minutes": int(distance_km * 1.2),
                "segments": segments
            }
            
        except Exception as e:
            logger.error(f"Base route calculation failed: {e}")
            raise
    
    async def find_charging_stations_on_route(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float], 
        vehicle_model: str
    ) -> List[Dict[str, Any]]:
        """
        Find charging stations along a route
        
        Args:
            start_coords: Starting coordinates
            end_coords: End coordinates
            vehicle_model: Vehicle model for connector compatibility
            
        Returns:
            List of compatible charging stations
        """
        try:
            # Get vehicle specs for connector compatibility
            vehicle_specs = await self.get_vehicle_specs(vehicle_model)
            if not vehicle_specs:
                logger.warning(f"Vehicle specs not found for {vehicle_model}")
                compatible_connectors = ["CCS1", "CCS2"]  # Default fallback
            else:
                compatible_connectors = vehicle_specs["supported_connectors"]
            
            # Mock charging stations along route
            mock_stations = [
                {
                    "id": "station_1",
                    "name": "Highway Charging Plaza",
                    "latitude": (start_coords[0] + end_coords[0]) / 2,
                    "longitude": (start_coords[1] + end_coords[1]) / 2,
                    "connector_types": ["CCS1", "CHAdeMO"],
                    "max_power_kw": 150,
                    "network": "Electrify America",
                    "distance_from_route_km": 2.5
                },
                {
                    "id": "station_2", 
                    "name": "Tesla Supercharger",
                    "latitude": start_coords[0] + (end_coords[0] - start_coords[0]) * 0.3,
                    "longitude": start_coords[1] + (end_coords[1] - start_coords[1]) * 0.3,
                    "connector_types": ["Tesla", "CCS1"],
                    "max_power_kw": 250,
                    "network": "Tesla",
                    "distance_from_route_km": 1.0
                }
            ]
            
            # Filter by connector compatibility
            compatible_stations = []
            for station in mock_stations:
                if any(connector in compatible_connectors for connector in station["connector_types"]):
                    compatible_stations.append(station)
            
            logger.info(f"Found {len(compatible_stations)} compatible charging stations")
            return compatible_stations
            
        except Exception as e:
            logger.error(f"Charging station search failed: {e}")
            return []
    
    async def get_route_alternatives(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        vehicle_model: str,
        max_alternatives: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get alternative routes with different strategies
        
        Args:
            start: Starting coordinates
            end: End coordinates
            vehicle_model: Vehicle model
            max_alternatives: Maximum number of alternatives
            
        Returns:
            List of alternative routes
        """
        try:
            base_distance = self._calculate_distance(start[0], start[1], end[0], end[1])
            
            alternatives = []
            
            # Route 1: Fastest route (highway priority)
            alternatives.append({
                "route_id": "fastest",
                "name": "Fastest Route",
                "description": "Prioritizes highways and speed",
                "total_distance_km": base_distance,
                "estimated_time_minutes": int(base_distance * 0.9),
                "charging_stops": 2,
                "route_type": "highway_priority"
            })
            
            # Route 2: Most efficient (energy optimized)
            alternatives.append({
                "route_id": "efficient",
                "name": "Most Efficient",
                "description": "Optimized for energy consumption",
                "total_distance_km": base_distance * 1.1,
                "estimated_time_minutes": int(base_distance * 1.2),
                "charging_stops": 1,
                "route_type": "energy_optimized"
            })
            
            # Route 3: Scenic route (if requested)
            if max_alternatives >= 3:
                alternatives.append({
                    "route_id": "scenic",
                    "name": "Scenic Route",
                    "description": "Takes scenic roads with amenities",
                    "total_distance_km": base_distance * 1.3,
                    "estimated_time_minutes": int(base_distance * 1.5),
                    "charging_stops": 3,
                    "route_type": "scenic"
                })
            
            return alternatives[:max_alternatives]
            
        except Exception as e:
            logger.error(f"Route alternatives calculation failed: {e}")
            return []
    
    async def calculate_energy_consumption(
        self,
        waypoints: List[Any],  # Accept both Waypoint objects and dicts
        vehicle_model: str
    ) -> Dict[str, Any]:
        """
        Calculate estimated energy consumption for a route
        
        Args:
            waypoints: List of route waypoints (Waypoint objects or dicts)
            vehicle_model: Vehicle model
            
        Returns:
            Energy consumption analysis
        """
        try:
            vehicle_specs = await self.get_vehicle_specs(vehicle_model)
            if not vehicle_specs:
                raise ValueError(f"Vehicle specs not found for {vehicle_model}")
            
            total_distance = 0
            for i in range(len(waypoints) - 1):
                wp1 = waypoints[i]
                # Handle both Waypoint objects and dicts
                if isinstance(wp1, dict):
                    segment_distance = wp1.get('distance_to_next', 50)
                else:
                    segment_distance = getattr(wp1, 'distance_to_next', None) or 50
                total_distance += segment_distance
            
            # Base energy consumption
            base_consumption = total_distance * vehicle_specs["energy_consumption_kwh_per_100km"] / 100
            
            # Apply factors
            weather_factor = 1.1  # 10% increase for adverse weather
            terrain_factor = 1.05  # 5% for elevation changes
            speed_factor = 1.02   # 2% for highway speeds
            
            total_consumption = base_consumption * weather_factor * terrain_factor * speed_factor
            
            # Battery analysis
            battery_capacity = vehicle_specs["battery_capacity_kwh"]
            consumption_percentage = (total_consumption / battery_capacity) * 100
            
            return {
                "total_distance_km": total_distance,
                "estimated_consumption_kwh": round(total_consumption, 2),
                "consumption_percentage": round(consumption_percentage, 1),
                "range_remaining_km": max(0, vehicle_specs["range_km"] - total_distance),
                "factors": {
                    "base_consumption": round(base_consumption, 2),
                    "weather_impact": round((weather_factor - 1) * 100, 1),
                    "terrain_impact": round((terrain_factor - 1) * 100, 1),
                    "speed_impact": round((speed_factor - 1) * 100, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Energy consumption calculation failed: {e}")
            raise
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance between two points in km
        """
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