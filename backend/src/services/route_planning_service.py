"""
Route Planning Service
Calculates optimal EV routes with charging stops using TomTom Routing API
"""
import logging
import os
import requests
from typing import List, Dict, Optional, Tuple
from math import radians, cos, sin, asin, sqrt
from pathlib import Path
import sys

# Add services to path
services_path = Path(__file__).parent
sys.path.insert(0, str(services_path))

from charging_station_service import charging_station_service

logger = logging.getLogger(__name__)

# TomTom API Configuration
TOMTOM_API_KEY = "w9xr4Dka9SWOvK8QhPy5tSTvAS9lj3Cq"
TOMTOM_ROUTING_API = "https://api.tomtom.com/routing/1/calculateRoute/"

class RoutePlanningService:
    """Service for EV route planning with charging optimization"""
    
    def __init__(self):
        self.charging_service = charging_station_service
    
    def get_tomtom_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        waypoints: Optional[List[Tuple[float, float]]] = None
    ) -> Optional[Dict]:
        """
        Get route from TomTom Routing API with real-time traffic
        
        Args:
            start_lat, start_lon: Starting coordinates
            end_lat, end_lon: Destination coordinates
            waypoints: Optional list of (lat, lon) waypoints for charging stops
        
        Returns:
            Dict with route data including coordinates, distance, time with traffic
        """
        try:
            # Build waypoints string: start:end or start:wp1:wp2:end
            locations = f"{start_lat},{start_lon}"
            
            if waypoints:
                for wp_lat, wp_lon in waypoints:
                    locations += f":{wp_lat},{wp_lon}"
            
            locations += f":{end_lat},{end_lon}"
            
            # TomTom Routing API request
            url = f"{TOMTOM_ROUTING_API}{locations}/json"
            
            params = {
                "key": TOMTOM_API_KEY,
                "traffic": "true",  # Include real-time traffic
                "routeType": "fastest",  # Optimize for time (considers traffic)
                "travelMode": "car",
                "vehicleEngineType": "electric",
                "constantSpeedConsumptionInkWhPerKm": "0.15",  # Avg EV consumption
            }
            
            logger.info(f"Requesting TomTom route: {locations}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "routes" in data and len(data["routes"]) > 0:
                    route = data["routes"][0]
                    summary = route.get("summary", {})
                    
                    # Extract coordinates from route legs
                    coordinates = []
                    for leg in route.get("legs", []):
                        for point in leg.get("points", []):
                            coordinates.append([point["latitude"], point["longitude"]])
                    
                    return {
                        "coordinates": coordinates,
                        "distance_km": summary.get("lengthInMeters", 0) / 1000,
                        "time_minutes": summary.get("travelTimeInSeconds", 0) / 60,
                        "traffic_delay_minutes": summary.get("trafficDelayInSeconds", 0) / 60,
                        "arrival_time": summary.get("arrivalTime"),
                        "departure_time": summary.get("departureTime"),
                    }
                else:
                    logger.warning("No routes found in TomTom response")
            else:
                logger.error(f"TomTom API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting TomTom route: {e}")
        
        return None
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth's radius in km
        radius = 6371
        return radius * c
    
    def calculate_charging_stops(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        vehicle_range_km: float,
        battery_capacity_kwh: float,
        current_battery_percent: float = 80.0,
        min_charge_percent: float = 20.0,
        preferred_charge_percent: float = 80.0
    ) -> Dict:
        """
        Calculate optimal charging stops along a route
        
        Args:
            start_lat, start_lon: Starting coordinates
            end_lat, end_lon: Destination coordinates
            vehicle_range_km: Vehicle's maximum range in km
            battery_capacity_kwh: Battery capacity in kWh
            current_battery_percent: Current battery level (default 80%)
            min_charge_percent: Minimum battery before charging (default 20%)
            preferred_charge_percent: Target charge level at stations (default 80%)
        
        Returns:
            Dict with route info, charging stops, and timeline
        """
        try:
            # Calculate total distance (straight line)
            total_distance = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)
            
            # Calculate usable range (between min and current charge)
            usable_range = (vehicle_range_km * (current_battery_percent - min_charge_percent) / 100)
            
            logger.info(f"Route planning: {total_distance:.1f}km, Range: {vehicle_range_km}km, Usable: {usable_range:.1f}km")
            
            # Get all charging stations
            all_stations = self.charging_service.get_all_stations()
            
            if not all_stations:
                logger.warning("No charging stations available")
                tomtom_data = self.get_tomtom_route(start_lat, start_lon, end_lat, end_lon)
                return self._create_route_response(
                    start_lat, start_lon, end_lat, end_lon,
                    total_distance, vehicle_range_km, [], 
                    "No charging stations available", tomtom_data
                )
            
            # If trip is within usable range, no charging needed
            if total_distance <= usable_range:
                logger.info("Trip within range, no charging stops needed")
                tomtom_data = self.get_tomtom_route(start_lat, start_lon, end_lat, end_lon)
                return self._create_route_response(
                    start_lat, start_lon, end_lat, end_lon,
                    total_distance, vehicle_range_km, [], 
                    "No charging stops needed - route calculated with real-time traffic", 
                    tomtom_data
                )
            
            # Find charging stops along the route
            charging_stops = self._find_optimal_stops(
                start_lat, start_lon, end_lat, end_lon,
                all_stations, vehicle_range_km, battery_capacity_kwh,
                current_battery_percent, min_charge_percent, preferred_charge_percent
            )
            
            # Get TomTom route with waypoints for charging stops
            waypoints = [(stop['latitude'], stop['longitude']) for stop in charging_stops]
            tomtom_data = self.get_tomtom_route(start_lat, start_lon, end_lat, end_lon, waypoints)
            
            return self._create_route_response(
                start_lat, start_lon, end_lat, end_lon,
                total_distance, vehicle_range_km, charging_stops,
                None, tomtom_data
            )
            
        except Exception as e:
            logger.error(f"Route planning error: {str(e)}")
            raise
    
    def _find_optimal_stops(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        stations: List[Dict],
        vehicle_range_km: float,
        battery_capacity_kwh: float,
        current_battery_percent: float,
        min_charge_percent: float,
        preferred_charge_percent: float
    ) -> List[Dict]:
        """Find optimal charging stops along the route"""
        
        stops = []
        current_lat, current_lon = start_lat, start_lon
        current_battery = current_battery_percent
        segment_number = 0
        
        while True:
            segment_number += 1
            distance_to_end = self.haversine_distance(current_lat, current_lon, end_lat, end_lon)
            
            # Calculate remaining range with current battery
            remaining_range = (vehicle_range_km * (current_battery - min_charge_percent) / 100)
            
            # If we can reach destination with current battery, we're done
            if distance_to_end <= remaining_range:
                logger.info(f"Segment {segment_number}: Can reach destination ({distance_to_end:.1f}km < {remaining_range:.1f}km)")
                break
            
            # Safety check: prevent infinite loops
            if segment_number > 10:
                logger.warning("Too many segments, breaking loop")
                break
            
            # Find stations along the route within our range
            candidate_stations = []
            for station in stations:
                # Calculate distance from current position
                dist_from_current = self.haversine_distance(
                    current_lat, current_lon,
                    station['latitude'], station['longitude']
                )
                
                # Skip if station is too close (< 100km) - no need to charge yet
                if dist_from_current < 100:
                    continue
                
                # Skip if too far (beyond 80% of usable range for safety)
                if dist_from_current > remaining_range * 0.80:
                    continue
                
                # Calculate distance from station to destination
                dist_to_destination = self.haversine_distance(
                    station['latitude'], station['longitude'],
                    end_lat, end_lon
                )
                
                # Calculate detour (how much extra distance we'd travel)
                direct_distance = self.haversine_distance(current_lat, current_lon, end_lat, end_lon)
                detour = (dist_from_current + dist_to_destination) - direct_distance
                
                # Only consider stations with minimal detour (< 30km)
                if detour > 30:
                    continue
                
                # Check if this station actually helps us reach the destination
                # After charging at this station, can we reach the end?
                range_after_charge = vehicle_range_km * (preferred_charge_percent - min_charge_percent) / 100
                if dist_to_destination > range_after_charge * 1.2:  # Still too far even after charging
                    # This is a necessary intermediate stop
                    pass
                
                # Score: maximize distance traveled while minimizing detour
                # We want to go as far as safely possible with minimal route deviation
                score = (dist_from_current * 10) - (detour * 50)
                
                candidate_stations.append({
                    **station,
                    'distance_from_current': dist_from_current,
                    'distance_to_destination': dist_to_destination,
                    'detour': detour,
                    'progress_score': score
                })
            
            if not candidate_stations:
                logger.warning(f"No reachable charging stations found at segment {segment_number}")
                break
            
            # Select best station (maximize progress, minimize detour)
            best_station = max(candidate_stations, key=lambda s: s['progress_score'])
            
            # Calculate charging details
            kwh_needed = battery_capacity_kwh * (preferred_charge_percent - current_battery) / 100
            charging_power = best_station.get('power_kw', 50)
            charging_time_minutes = (kwh_needed / charging_power) * 60
            
            # Battery depletion to reach this station
            km_to_station = best_station['distance_from_current']
            battery_used = (km_to_station / vehicle_range_km) * 100
            battery_on_arrival = current_battery - battery_used
            
            stop_info = {
                'segment': segment_number,
                'station_name': best_station['name'],
                'city': best_station['city'],
                'latitude': best_station['latitude'],
                'longitude': best_station['longitude'],
                'distance_from_start': sum(s['distance_traveled'] for s in stops) + km_to_station,
                'distance_traveled': km_to_station,
                'distance_to_destination': best_station['distance_to_destination'],
                'battery_on_arrival': max(battery_on_arrival, min_charge_percent),
                'battery_after_charge': preferred_charge_percent,
                'kwh_charged': kwh_needed,
                'charging_power_kw': charging_power,
                'charging_time_minutes': charging_time_minutes,
                'connector_type': best_station.get('connector_type', 'CCS'),
                'price_per_kwh': best_station.get('price_per_kwh', 0.35),
                'estimated_cost': kwh_needed * best_station.get('price_per_kwh', 0.35)
            }
            
            stops.append(stop_info)
            
            # Update position and battery for next segment
            current_lat = best_station['latitude']
            current_lon = best_station['longitude']
            current_battery = preferred_charge_percent
            
            # Safety check: max 10 stops
            if len(stops) >= 10:
                logger.warning("Max charging stops reached (10)")
                break
        
        return stops
    
    def _create_route_response(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        total_distance: float,
        vehicle_range_km: float,
        charging_stops: List[Dict],
        message: Optional[str] = None,
        tomtom_data: Optional[Dict] = None
    ) -> Dict:
        """Create standardized route response with TomTom traffic data"""
        
        # Use TomTom data if available, otherwise calculate estimates
        if tomtom_data:
            driving_time_minutes = tomtom_data.get("time_minutes", 0)
            traffic_delay = tomtom_data.get("traffic_delay_minutes", 0)
            route_coordinates = tomtom_data.get("coordinates", [])
            actual_distance = tomtom_data.get("distance_km", total_distance)
        else:
            # Fallback calculations
            avg_speed_kmh = 80
            driving_time_hours = total_distance / avg_speed_kmh
            driving_time_minutes = driving_time_hours * 60
            traffic_delay = 0
            route_coordinates = [[start_lat, start_lon], [end_lat, end_lon]]
            actual_distance = total_distance
        
        # Calculate total time with charging
        total_charging_minutes = sum(stop['charging_time_minutes'] for stop in charging_stops)
        total_time_minutes = driving_time_minutes + total_charging_minutes
        
        # Calculate total cost
        total_charging_cost = sum(stop['estimated_cost'] for stop in charging_stops)
        
        # Use TomTom coordinates if available, otherwise create simplified path
        if not route_coordinates or len(route_coordinates) == 0:
            route_coordinates = [[start_lat, start_lon]]
            for stop in charging_stops:
                route_coordinates.append([stop['latitude'], stop['longitude']])
            route_coordinates.append([end_lat, end_lon])
        
        return {
            'success': True,
            'message': message or 'Route calculated successfully with real-time traffic',
            'route_summary': {
                'total_distance_km': round(actual_distance, 1),
                'driving_time_minutes': round(driving_time_minutes, 1),
                'traffic_delay_minutes': round(traffic_delay, 1),
                'total_time_minutes': round(total_time_minutes, 1),
                'num_charging_stops': len(charging_stops),
                'charging_time_minutes': round(total_charging_minutes, 1),
                'estimated_cost_tl': round(total_charging_cost * 30, 2),  # Convert to TL
                'energy_needed_kwh': round(sum(stop['kwh_charged'] for stop in charging_stops), 2),
                'vehicle_range_km': vehicle_range_km,
                'with_traffic': tomtom_data is not None
            },
            'route_coordinates': route_coordinates,
            'charging_stops': charging_stops,
            'waypoints': [
                {'type': 'start', 'latitude': start_lat, 'longitude': start_lon, 'name': 'Start'},
                *[{
                    'type': 'charging',
                    'latitude': stop['latitude'],
                    'longitude': stop['longitude'],
                    'name': stop['station_name'],
                    'segment': stop['segment']
                } for stop in charging_stops],
                {'type': 'end', 'latitude': end_lat, 'longitude': end_lon, 'name': 'Destination'}
            ]
        }

# Global instance
route_planning_service = RoutePlanningService()
