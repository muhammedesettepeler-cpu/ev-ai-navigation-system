"""
Charging Service - Business logic for charging station management
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import math

logger = logging.getLogger(__name__)

class ChargingService:
    """
    Service for managing charging station data and recommendations
    """
    
    def __init__(self):
        # In a real implementation, this would connect to charging network APIs
        self.network_apis = {
            "Tesla": "https://api.tesla.com/superchargers",
            "Electrify America": "https://api.electrifyamerica.com/stations",
            "EVgo": "https://api.evgo.com/locations"
        }
    
    async def find_best_charging_station(
        self,
        location: Tuple[float, float],
        vehicle_specs: Dict[str, Any],
        max_detour_km: float = 10,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best charging station near a location
        
        Args:
            location: Target location (lat, lon)
            vehicle_specs: Vehicle specifications
            max_detour_km: Maximum acceptable detour
            preferences: User preferences for charging
            
        Returns:
            Best charging station or None
        """
        try:
            # Get compatible stations
            stations = await self._get_nearby_stations(location, max_detour_km)
            compatible_stations = self._filter_compatible_stations(stations, vehicle_specs)
            
            if not compatible_stations:
                logger.warning(f"No compatible charging stations found near {location}")
                return None
            
            # Score and rank stations
            scored_stations = []
            for station in compatible_stations:
                score = self._calculate_station_score(station, vehicle_specs, preferences)
                scored_stations.append((station, score))
            
            # Sort by score (highest first)
            scored_stations.sort(key=lambda x: x[1], reverse=True)
            
            best_station = scored_stations[0][0]
            logger.info(f"Selected best charging station: {best_station['name']}")
            
            return best_station
            
        except Exception as e:
            logger.error(f"Failed to find best charging station: {e}")
            return None
    
    async def _get_nearby_stations(
        self, 
        location: Tuple[float, float], 
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """
        Get charging stations within radius of location
        
        Args:
            location: Center location (lat, lon)
            radius_km: Search radius
            
        Returns:
            List of nearby stations
        """
        # Mock charging stations for demonstration
        mock_stations = [
            {
                "id": "tesla_sc_001",
                "name": "Tesla Supercharger - Mall",
                "network": "Tesla",
                "latitude": location[0] + 0.01,
                "longitude": location[1] + 0.01,
                "connector_types": ["Tesla", "CCS1"],
                "power_kw": 250,
                "stalls": 12,
                "available_stalls": 8,
                "cost_per_kwh": 0.28,
                "amenities": ["Shopping", "Restaurant", "WiFi"],
                "rating": 4.5,
                "wait_time_minutes": 0
            },
            {
                "id": "ea_001",
                "name": "Electrify America - Highway",
                "network": "Electrify America",
                "latitude": location[0] + 0.005,
                "longitude": location[1] - 0.005,
                "connector_types": ["CCS1", "CHAdeMO"],
                "power_kw": 350,
                "stalls": 8,
                "available_stalls": 6,
                "cost_per_kwh": 0.31,
                "amenities": ["Convenience Store", "WiFi"],
                "rating": 4.2,
                "wait_time_minutes": 5
            },
            {
                "id": "evgo_001",
                "name": "EVgo Fast Charge",
                "network": "EVgo",
                "latitude": location[0] - 0.008,
                "longitude": location[1] + 0.012,
                "connector_types": ["CCS1", "CHAdeMO"],
                "power_kw": 100,
                "stalls": 4,
                "available_stalls": 2,
                "cost_per_kwh": 0.25,
                "amenities": ["Grocery Store"],
                "rating": 3.8,
                "wait_time_minutes": 15
            }
        ]
        
        # Filter by distance
        nearby_stations = []
        for station in mock_stations:
            distance = self._calculate_distance(
                location[0], location[1],
                station["latitude"], station["longitude"]
            )
            if distance <= radius_km:
                station["distance_km"] = distance
                nearby_stations.append(station)
        
        return nearby_stations
    
    def _filter_compatible_stations(
        self, 
        stations: List[Dict[str, Any]], 
        vehicle_specs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter stations by connector compatibility
        
        Args:
            stations: List of charging stations
            vehicle_specs: Vehicle specifications
            
        Returns:
            List of compatible stations
        """
        compatible_stations = []
        vehicle_connectors = vehicle_specs.get("supported_connectors", [])
        
        for station in stations:
            station_connectors = station.get("connector_types", [])
            
            # Check if any connector is compatible
            if any(connector in vehicle_connectors for connector in station_connectors):
                compatible_stations.append(station)
        
        return compatible_stations
    
    def _calculate_station_score(
        self,
        station: Dict[str, Any],
        vehicle_specs: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate score for a charging station
        
        Args:
            station: Station information
            vehicle_specs: Vehicle specifications
            preferences: User preferences
            
        Returns:
            Station score (0-100)
        """
        score = 0.0
        
        # Base score from rating
        score += (station.get("rating", 3.0) / 5.0) * 20
        
        # Charging power score (prefer higher power up to vehicle max)
        vehicle_max_power = vehicle_specs.get("max_charging_power_kw", 150)
        station_power = station.get("power_kw", 50)
        effective_power = min(station_power, vehicle_max_power)
        power_score = (effective_power / 350) * 25  # Normalize to 350kW max
        score += power_score
        
        # Availability score
        total_stalls = station.get("stalls", 1)
        available_stalls = station.get("available_stalls", 1)
        availability_ratio = available_stalls / total_stalls
        score += availability_ratio * 20
        
        # Wait time score (lower is better)
        wait_time = station.get("wait_time_minutes", 0)
        wait_score = max(0, 15 - wait_time)  # 15 points max, decreases with wait time
        score += wait_score
        
        # Distance score (closer is better)
        distance = station.get("distance_km", 0)
        distance_score = max(0, 20 - distance * 2)  # Penalty for distance
        score += distance_score
        
        # Apply preferences
        if preferences:
            # Network preference
            preferred_networks = preferences.get("preferred_charging_networks", [])
            if preferred_networks and station.get("network") in preferred_networks:
                score += 10
            
            # Fast charging preference
            if preferences.get("prefer_fast_charging", True) and station_power >= 150:
                score += 5
            
            # Amenities preference
            preferred_amenities = preferences.get("preferred_amenities", [])
            station_amenities = station.get("amenities", [])
            amenity_matches = sum(1 for amenity in preferred_amenities if amenity in station_amenities)
            score += amenity_matches * 2
        
        return min(100.0, score)  # Cap at 100
    
    async def get_charging_time_estimate(
        self,
        vehicle_specs: Dict[str, Any],
        station_power_kw: float,
        current_soc: float,
        target_soc: float
    ) -> Dict[str, Any]:
        """
        Estimate charging time for given parameters
        
        Args:
            vehicle_specs: Vehicle specifications
            station_power_kw: Station charging power
            current_soc: Current state of charge (0-1)
            target_soc: Target state of charge (0-1)
            
        Returns:
            Charging time estimate with breakdown
        """
        try:
            battery_capacity = vehicle_specs.get("battery_capacity_kwh", 75)
            vehicle_max_power = vehicle_specs.get("max_charging_power_kw", 150)
            
            # Effective charging power (limited by vehicle or station)
            effective_power = min(station_power_kw, vehicle_max_power)
            
            # Energy to add
            energy_needed = (target_soc - current_soc) * battery_capacity
            
            # Simplified charging curve (real implementation would use detailed curves)
            if current_soc < 0.2:
                # Fast charging up to 20%
                avg_power = effective_power * 0.95
            elif current_soc < 0.5:
                # Good charging 20-50%
                avg_power = effective_power * 0.9
            elif current_soc < 0.8:
                # Moderate charging 50-80%
                avg_power = effective_power * 0.7
            else:
                # Slow charging 80%+
                avg_power = effective_power * 0.4
            
            # Calculate time
            charging_time_hours = energy_needed / avg_power
            charging_time_minutes = int(charging_time_hours * 60)
            
            # Cost estimate
            cost_per_kwh = 0.28  # Default cost
            estimated_cost = energy_needed * cost_per_kwh
            
            return {
                "charging_time_minutes": charging_time_minutes,
                "energy_added_kwh": round(energy_needed, 2),
                "estimated_cost": round(estimated_cost, 2),
                "effective_power_kw": effective_power,
                "average_power_kw": round(avg_power, 1)
            }
            
        except Exception as e:
            logger.error(f"Charging time estimate failed: {e}")
            raise
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
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
        return 6371 * c