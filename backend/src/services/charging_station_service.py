"""
Charging Station Service
Handles charging station data loading and queries
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ChargingStationService:
    """Service for managing charging station data"""
    
    def __init__(self):
        self.stations_df: Optional[pd.DataFrame] = None
        self.data_path = Path(__file__).parent.parent.parent.parent / "data" / "charging_stations" / "charging_stations_map.csv"
        self.load_stations()
    
    def load_stations(self) -> None:
        """Load charging stations from CSV file"""
        try:
            if not self.data_path.exists():
                logger.error(f"Charging stations file not found: {self.data_path}")
                self.stations_df = pd.DataFrame()
                return
            
            self.stations_df = pd.read_csv(self.data_path, encoding='utf-8')
            logger.info(f"Loaded {len(self.stations_df)} charging stations")
            
            # Rename Turkish column names to English
            column_mapping = {
                'Şarj İstasyonu': 'name',
                'Şehir': 'city',
                'Latitude': 'latitude',
                'Longitude': 'longitude',
                'last_updated': 'last_updated',
                'next_update': 'next_update',
                'estimated_current_kW': 'power_kw',
                'cluster': 'cluster'
            }
            self.stations_df = self.stations_df.rename(columns=column_mapping)
            
        except Exception as e:
            logger.error(f"Error loading charging stations: {str(e)}")
            self.stations_df = pd.DataFrame()
    
    def get_all_stations(self) -> List[Dict]:
        """Get all charging stations"""
        if self.stations_df is None or self.stations_df.empty:
            return []
        
        stations = self.stations_df.to_dict('records')
        
        # Add additional metadata
        for station in stations:
            # Determine connector type based on power
            power = station.get('power_kw', 50)
            if power >= 150:
                station['connector_type'] = 'DC Fast Charge (CCS/CHAdeMO)'
                station['charging_speed'] = 'Ultra Fast'
            elif power >= 50:
                station['connector_type'] = 'DC Fast Charge (CCS)'
                station['charging_speed'] = 'Fast'
            else:
                station['connector_type'] = 'AC Type 2'
                station['charging_speed'] = 'Normal'
            
            # Estimate price per kWh based on power
            if power >= 150:
                station['price_per_kwh'] = 0.45
            elif power >= 50:
                station['price_per_kwh'] = 0.35
            else:
                station['price_per_kwh'] = 0.25
            
            # Add availability (random for demo)
            station['availability'] = 'Available'
            station['total_ports'] = 2 if power >= 50 else 4
            station['available_ports'] = 1 if power >= 50 else 2
            
        return stations
    
    def get_stations_by_city(self, city: str) -> List[Dict]:
        """Get charging stations in a specific city"""
        if self.stations_df is None or self.stations_df.empty:
            return []
        
        city_upper = city.upper()
        filtered_df = self.stations_df[self.stations_df['city'].str.upper() == city_upper]
        return filtered_df.to_dict('records')
    
    def get_stations_by_power(self, min_power: float = 0, max_power: float = 1000) -> List[Dict]:
        """Get charging stations within power range"""
        if self.stations_df is None or self.stations_df.empty:
            return []
        
        filtered_df = self.stations_df[
            (self.stations_df['power_kw'] >= min_power) & 
            (self.stations_df['power_kw'] <= max_power)
        ]
        stations = filtered_df.to_dict('records')
        return self.get_all_stations()  # Return with metadata
    
    def get_stations_in_radius(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 50
    ) -> List[Dict]:
        """Get charging stations within radius of a location"""
        if self.stations_df is None or self.stations_df.empty:
            return []
        
        # Simple distance calculation (Haversine approximation)
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lat1, lon1, lat2, lon2):
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            km = 6371 * c
            return km
        
        stations = self.get_all_stations()
        nearby_stations = []
        
        for station in stations:
            try:
                distance = haversine(
                    latitude, longitude,
                    float(station['latitude']), float(station['longitude'])
                )
                if distance <= radius_km:
                    station['distance_km'] = round(distance, 2)
                    nearby_stations.append(station)
            except Exception as e:
                logger.warning(f"Error calculating distance for station: {str(e)}")
                continue
        
        # Sort by distance
        nearby_stations.sort(key=lambda x: x.get('distance_km', float('inf')))
        return nearby_stations

# Global instance
charging_station_service = ChargingStationService()
