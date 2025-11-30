"""
Route Optimizer Agent - Intelligent route optimization with charging stops
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math

from models.navigation import RouteRequest, RouteResponse, Waypoint, ChargingStop, WaypointType
from models.vehicle_models import VehicleSpecs
from services.charging_service import ChargingService
from services.navigation_service import NavigationService
from rag.rag_system import RAGSystem

logger = logging.getLogger(__name__)

@dataclass
class RouteSegment:
    """Route segment between two points"""
    start: Tuple[float, float]
    end: Tuple[float, float]
    distance_km: float
    estimated_consumption_kwh: float
    estimated_time_minutes: int

class RouteOptimizerAgent:
    """
    Intelligent agent for optimizing EV routes with charging considerations
    """
    
    def __init__(self):
        self.charging_service = ChargingService()
        self.navigation_service = NavigationService()
        self.rag_system = RAGSystem()
        
        # Route optimization parameters
        self.SAFETY_BUFFER_PERCENTAGE = 0.20  # 20% battery safety buffer
        self.MAX_CHARGING_DETOUR_KM = 10      # Maximum detour for charging
        self.PREFERRED_CHARGING_LEVEL = 0.80   # Prefer charging to 80%
    
    async def optimize_route(
        self,
        start: Tuple[float, float],
        destination: Tuple[float, float],
        vehicle_specs: Dict[str, Any],  # Accept dict instead of VehicleSpecs for flexibility
        current_battery_level: float,
        preferences: Optional[Dict[str, Any]] = None
    ) -> RouteResponse:
        """
        Optimize route with intelligent charging stop placement
        
        Args:
            start: Starting coordinates (lat, lon)
            destination: Destination coordinates (lat, lon)
            vehicle_specs: Vehicle specifications (dict with keys: battery_capacity_kwh, energy_consumption_kwh_per_100km, etc.)
            current_battery_level: Current battery level (0-1)
            preferences: User preferences for optimization
            
        Returns:
            Optimized route with charging stops
        """
        try:
            logger.info(f"Optimizing route for {vehicle_specs.get('model', 'unknown vehicle')}")
            
            # 1. Calculate base route without charging stops
            base_route = await self.navigation_service.calculate_base_route(start, destination)
            total_distance = base_route['total_distance_km']
            
            # 2. Analyze energy requirements
            energy_analysis = await self._analyze_energy_requirements(
                base_route, vehicle_specs, current_battery_level
            )
            
            # 3. Determine charging strategy
            if energy_analysis['needs_charging']:
                charging_stops = await self._plan_charging_stops(
                    base_route, vehicle_specs, current_battery_level, preferences
                )
            else:
                charging_stops = []
                logger.info("No charging stops needed for this route")
            
            # 4. Create optimized waypoints
            optimized_waypoints = await self._create_optimized_waypoints(
                base_route, charging_stops, vehicle_specs
            )
            
            # 5. Calculate final route metrics
            route_metrics = await self._calculate_route_metrics(
                optimized_waypoints, vehicle_specs, current_battery_level
            )
            
            # 6. Get AI insights about the route
            route_insights = await self._get_route_insights(
                start, destination, charging_stops, route_metrics
            )
            
            # 7. Build response
            route_response = RouteResponse(
                waypoints=optimized_waypoints,
                total_distance_km=route_metrics['total_distance'],
                estimated_time_minutes=route_metrics['total_time'],
                estimated_energy_consumption_kwh=route_metrics['total_energy'],
                charging_stops=charging_stops,
                final_battery_level=route_metrics['final_battery'],
                route_efficiency_score=route_metrics['efficiency_score'],
                insights=route_insights,
                preferences_applied=preferences or {}
            )
            
            logger.info(f"Route optimization completed: {len(charging_stops)} charging stops")
            return route_response
            
        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            raise
    
    async def _analyze_energy_requirements(
        self,
        base_route: Dict[str, Any],
        vehicle_specs: Dict[str, Any],  # Changed from VehicleSpecs to Dict
        current_battery_level: float
    ) -> Dict[str, Any]:
        """Analyze if charging is needed for the route"""
        
        total_distance = base_route['total_distance_km']
        
        # Calculate energy consumption
        # Base consumption + elevation + weather factors
        consumption_rate = vehicle_specs.get('energy_consumption_kwh_per_100km', 20)  # Default 20 kWh/100km
        base_consumption = total_distance * consumption_rate / 100
        
        # Add factors (simplified for now)
        elevation_factor = 1.1  # 10% increase for elevation changes
        weather_factor = 1.05   # 5% increase for adverse weather
        
        total_energy_needed = base_consumption * elevation_factor * weather_factor
        
        # Available energy
        battery_capacity = vehicle_specs.get('battery_capacity_kwh', 60)  # Default 60 kWh
        current_energy_kwh = battery_capacity * current_battery_level
        
        # Safety buffer
        safety_energy = battery_capacity * self.SAFETY_BUFFER_PERCENTAGE
        usable_energy = current_energy_kwh - safety_energy
        
        needs_charging = total_energy_needed > usable_energy
        
        return {
            'needs_charging': needs_charging,
            'total_energy_needed': total_energy_needed,
            'available_energy': usable_energy,
            'energy_deficit': max(0, total_energy_needed - usable_energy),
            'estimated_final_battery': max(0, (current_energy_kwh - total_energy_needed) / battery_capacity)
        }
    
    async def _plan_charging_stops(
        self,
        base_route: Dict[str, Any],
        vehicle_specs: Dict[str, Any],  # Changed from VehicleSpecs to Dict
        current_battery_level: float,
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[ChargingStop]:
        """Plan optimal charging stops along the route"""
        
        charging_stops = []
        route_segments = base_route['segments']
        
        # Extract specs with defaults
        battery_capacity = vehicle_specs.get('battery_capacity_kwh', 60)
        
        # Current state
        current_battery = current_battery_level
        current_position = 0  # Distance traveled
        
        for i, segment in enumerate(route_segments):
            # Calculate energy needed for this segment
            segment_energy = self._calculate_segment_energy(segment, vehicle_specs)
            segment_distance = segment['distance_km']
            
            # Check if we need charging before this segment
            energy_needed = segment_energy + (battery_capacity * self.SAFETY_BUFFER_PERCENTAGE)
            available_energy = battery_capacity * current_battery
            
            if available_energy < energy_needed:
                # Find charging station near segment start
                charging_station = await self.charging_service.find_best_charging_station(
                    location=segment['start'],
                    vehicle_specs=vehicle_specs,
                    max_detour_km=self.MAX_CHARGING_DETOUR_KM,
                    preferences=preferences
                )
                
                if charging_station:
                    # Calculate charging details
                    charge_needed = self.PREFERRED_CHARGING_LEVEL - current_battery
                    charging_time = await self._calculate_charging_time(
                        charge_needed, vehicle_specs, charging_station
                    )
                    
                    charging_stop = ChargingStop(
                        station_id=charging_station['id'],
                        station_name=charging_station['name'],
                        location=charging_station['location'],
                        connector_type=charging_station['connector_type'],
                        charging_power_kw=charging_station['power_kw'],
                        estimated_charging_time_minutes=charging_time,
                        estimated_cost=charging_station['cost_per_kwh'] * charge_needed * battery_capacity,
                        battery_level_before=current_battery,
                        battery_level_after=self.PREFERRED_CHARGING_LEVEL
                    )
                    
                    charging_stops.append(charging_stop)
                    current_battery = self.PREFERRED_CHARGING_LEVEL
                    logger.info(f"Added charging stop: {charging_station['name']}")
            
            # Update battery level after segment
            battery_consumption = segment_energy / battery_capacity
            current_battery = max(0, current_battery - battery_consumption)
            current_position += segment_distance
        
        return charging_stops
    
    def _calculate_segment_energy(self, segment: Dict[str, Any], vehicle_specs: Dict[str, Any]) -> float:
        """Calculate energy consumption for a route segment"""
        
        consumption_rate = vehicle_specs.get('energy_consumption_kwh_per_100km', 20)
        base_consumption = segment['distance_km'] * consumption_rate / 100
        
        # Apply factors
        elevation_factor = 1.0 + (segment.get('elevation_gain_m', 0) / 1000 * 0.1)  # 10% per km elevation
        speed_factor = 1.0 + (max(0, segment.get('avg_speed_kmh', 80) - 80) / 100 * 0.1)  # Highway penalty
        
        return base_consumption * elevation_factor * speed_factor
    
    async def _calculate_charging_time(
        self, 
        charge_needed: float, 
        vehicle_specs: Dict[str, Any],  # Changed from VehicleSpecs to Dict
        charging_station: Dict[str, Any]
    ) -> int:
        """Calculate charging time in minutes"""
        
        battery_capacity = vehicle_specs.get('battery_capacity_kwh', 60)
        max_charging_power = vehicle_specs.get('max_charging_power_kw', 50)
        
        energy_to_add = charge_needed * battery_capacity
        charging_power = min(charging_station['power_kw'], max_charging_power)
        
        # Charging curve - slower as battery fills up
        avg_charging_efficiency = 0.85  # Account for charging curve
        
        charging_time_hours = energy_to_add / (charging_power * avg_charging_efficiency)
        return int(charging_time_hours * 60)
    
    async def _create_optimized_waypoints(
        self,
        base_route: Dict[str, Any],
        charging_stops: List[ChargingStop],
        vehicle_specs: Dict[str, Any]  # Changed from VehicleSpecs to Dict
    ) -> List[Waypoint]:
        """Create optimized waypoints including charging stops"""
        
        waypoints = []
        charging_stop_index = 0
        
        for i, segment in enumerate(base_route['segments']):
            # Add regular waypoint
            waypoint = Waypoint(
                latitude=segment['start'][0],
                longitude=segment['start'][1],
                waypoint_type=WaypointType.NAVIGATION,
                estimated_arrival_time=segment.get('estimated_time'),
                estimated_battery_level=segment.get('battery_level_at_arrival'),
                charging_station_id=None,
                estimated_charging_time=None,
                distance_to_next=segment.get('distance_km', 0)
            )
            waypoints.append(waypoint)
            
            # Check if there's a charging stop near this segment
            if (charging_stop_index < len(charging_stops) and 
                self._is_charging_stop_near_segment(charging_stops[charging_stop_index], segment)):
                
                stop = charging_stops[charging_stop_index]
                charging_waypoint = Waypoint(
                    latitude=stop.location[0],
                    longitude=stop.location[1],
                    waypoint_type=WaypointType.CHARGING,
                    charging_station_id=stop.station_id,
                    estimated_charging_time=stop.estimated_charging_time_minutes,
                    estimated_battery_level=stop.battery_level_after,
                    estimated_arrival_time=None,
                    distance_to_next=0
                )
                waypoints.append(charging_waypoint)
                charging_stop_index += 1
        
        # Add final destination
        final_segment = base_route['segments'][-1]
        final_waypoint = Waypoint(
            latitude=final_segment['end'][0],
            longitude=final_segment['end'][1],
            waypoint_type=WaypointType.DESTINATION,
            charging_station_id=None,
            estimated_arrival_time=None,
            estimated_charging_time=None,
            estimated_battery_level=None,
            distance_to_next=0
        )
        waypoints.append(final_waypoint)
        
        return waypoints
    
    def _is_charging_stop_near_segment(self, charging_stop: ChargingStop, segment: Dict[str, Any]) -> bool:
        """Check if charging stop is near a route segment"""
        # Simple distance check - in real implementation, use proper routing
        stop_lat, stop_lon = charging_stop.location
        seg_lat, seg_lon = segment['start']
        
        distance = math.sqrt((stop_lat - seg_lat)**2 + (stop_lon - seg_lon)**2) * 111  # Rough km conversion
        return distance <= self.MAX_CHARGING_DETOUR_KM
    
    async def _calculate_route_metrics(
        self,
        waypoints: List[Waypoint],
        vehicle_specs: Dict[str, Any],  # Changed from VehicleSpecs to Dict
        initial_battery: float
    ) -> Dict[str, Any]:
        """Calculate final route metrics"""
        
        consumption_rate = vehicle_specs.get('energy_consumption_kwh_per_100km', 20)
        battery_capacity = vehicle_specs.get('battery_capacity_kwh', 60)
        
        total_distance = sum([w.distance_to_next or 0 for w in waypoints])
        total_time = sum([w.estimated_charging_time or 0 for w in waypoints if w.waypoint_type == "charging"])
        total_energy = total_distance * consumption_rate / 100
        
        final_battery = max(0, initial_battery - (total_energy / battery_capacity))
        
        # Efficiency score (0-100)
        efficiency_score = min(100, (total_distance / max(1, total_time / 60)) * 10)
        
        return {
            'total_distance': total_distance,
            'total_time': total_time + 120,  # Add base travel time
            'total_energy': total_energy,
            'final_battery': final_battery,
            'efficiency_score': efficiency_score
        }
    
    async def _get_route_insights(
        self,
        start: Tuple[float, float],
        destination: Tuple[float, float],
        charging_stops: List[ChargingStop],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Get AI-powered insights about the route"""
        
        try:
            query = f"""
            Analyze this EV route: from {start} to {destination}
            Distance: {metrics['total_distance']:.1f} km
            Charging stops: {len(charging_stops)}
            Final battery: {metrics['final_battery']:.1%}
            
            Provide 3 key insights about this route for an EV driver.
            """
            
            rag_result = await self.rag_system.rag_query(query, search_limit=3)
            
            # Extract insights from AI response
            insights = []
            if rag_result['response']:
                lines = rag_result['response'].split('\n')
                for line in lines:
                    if line.strip() and (line.startswith('-') or line.startswith('*') or '.' in line):
                        insights.append(line.strip())
            
            # Add fallback insights if AI didn't provide any
            if not insights:
                insights = [
                    f"Route requires {len(charging_stops)} charging stops for optimal efficiency",
                    f"Final battery level will be {metrics['final_battery']:.1%}",
                    f"Total travel time including charging: {metrics['total_time']//60}h {metrics['total_time']%60}m"
                ]
            
            return insights[:3]  # Return top 3 insights
            
        except Exception as e:
            logger.error(f"Failed to generate route insights: {e}")
            return [
                "Route optimization completed successfully",
                f"Planning {len(charging_stops)} strategic charging stops",
                f"Estimated efficiency score: {metrics['efficiency_score']:.0f}/100"
            ]