"""
Geographic Agent - Address processing and mapping with OpenRouter integration
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import httpx
import json
import re
import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class LocationInfo:
    """Location information with coordinates"""
    address: str
    latitude: float
    longitude: float
    city: str
    country: str
    confidence: float
    place_type: str  # 'city', 'address', 'poi', etc.

@dataclass
class RouteMap:
    """Route mapping data for frontend display"""
    route_polyline: str  # Encoded polyline for map display
    bounds: Dict[str, float]  # Map bounds (north, south, east, west)
    zoom_level: int
    markers: List[Dict[str, Any]]  # Waypoints and charging stations
    elevation_profile: Optional[List[Dict[str, float]]] = None

class GeographicAgent:
    """
    Agent for processing addresses, geocoding, and map generation
    Uses OpenRouter for intelligent address processing
    """
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="ev-navigation-system")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        
        # Debug: Check if API key is loaded
        if self.openrouter_api_key:
            logger.info(f"OpenRouter API key loaded successfully (length: {len(self.openrouter_api_key)})")
        else:
            logger.warning("OpenRouter API key not found in environment variables")
            logger.info(f"Available env vars: {list(os.environ.keys())}")
        
    async def process_address_input(self, user_input: str) -> LocationInfo:
        """
        Process user address input using AI to understand intent
        
        Args:
            user_input: Raw user input (could be partial address, city, landmark, etc.)
            
        Returns:
            Processed location information
        """
        try:
            logger.info(f"Processing address input: {user_input}")
            
            # 1. Use OpenRouter to understand and enhance the address
            enhanced_address = await self._enhance_address_with_ai(user_input)
            
            # 2. Geocode the enhanced address
            location_info = await self._geocode_address(enhanced_address)
            
            # 3. Validate and refine if needed
            if location_info.confidence < 0.7:
                # Try alternative interpretations
                alternatives = await self._get_address_alternatives(user_input)
                for alt_address in alternatives:
                    alt_location = await self._geocode_address(alt_address)
                    if alt_location.confidence > location_info.confidence:
                        location_info = alt_location
                        break
            
            logger.info(f"Location resolved: {location_info.address} ({location_info.confidence:.2f})")
            return location_info
            
        except Exception as e:
            logger.error(f"Address processing failed: {e}")
            raise
    
    async def _enhance_address_with_ai(self, user_input: str) -> str:
        """Use OpenRouter to enhance and clarify address input"""
        
        if not self.openrouter_api_key:
            logger.warning("OpenRouter API key not configured, using input as-is")
            return user_input
        
        try:
            prompt = f"""
            You are a geographic assistant. The user entered this location: "{user_input}"
            
            Your task:
            1. If it's a clear address, return it as-is
            2. If it's partial/unclear, enhance it with likely missing information
            3. If it's a landmark/business, provide the full name and location
            4. Always return just the enhanced address, nothing else
            
            Examples:
            Input: "Taksim" → Output: "Taksim Square, Istanbul, Turkey"
            Input: "Berlin merkez" → Output: "Berlin Mitte, Berlin, Germany"
            Input: "Atatürk Havalimanı" → Output: "Istanbul Atatürk Airport, Istanbul, Turkey"
            
            Enhanced address:
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 100,
                        "temperature": 0.3
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    enhanced = result['choices'][0]['message']['content'].strip()
                    
                    # Clean up the response
                    enhanced = re.sub(r'^Enhanced address:\s*', '', enhanced, flags=re.IGNORECASE)
                    enhanced = re.sub(r'^Output:\s*', '', enhanced, flags=re.IGNORECASE)
                    enhanced = enhanced.strip('"\'')
                    
                    logger.info(f"AI enhanced address: '{user_input}' → '{enhanced}'")
                    return enhanced
                else:
                    logger.warning(f"OpenRouter API failed: {response.status_code}")
                    return user_input
                    
        except Exception as e:
            logger.error(f"AI address enhancement failed: {e}")
            return user_input
    
    async def _geocode_address(self, address: str) -> LocationInfo:
        """Geocode address to coordinates"""
        
        try:
            # Use asyncio to run synchronous geocoding
            location = await asyncio.get_event_loop().run_in_executor(
                None, self.geocoder.geocode, address
            )
            
            if not location:
                raise ValueError(f"Address not found: {address}")
            
            # Extract location details (type: ignore for geopy Location object)
            raw_data = location.raw  # type: ignore
            
            # Determine place type and confidence
            place_type = self._determine_place_type(raw_data)
            confidence = self._calculate_confidence(raw_data, address)
            
            # Extract city and country
            address_components = raw_data.get('display_name', '').split(', ')
            city = self._extract_city(address_components, raw_data)
            country = address_components[-1] if address_components else "Unknown"
            
            return LocationInfo(
                address=location.address,  # type: ignore
                latitude=location.latitude,  # type: ignore
                longitude=location.longitude,  # type: ignore
                city=city,
                country=country,
                confidence=confidence,
                place_type=place_type
            )
            
        except Exception as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
            raise
    
    def _determine_place_type(self, raw_data: Dict[str, Any]) -> str:
        """Determine the type of place from geocoding data"""
        
        osm_type = raw_data.get('osm_type', '').lower()
        category = raw_data.get('category', '').lower()
        osm_key = raw_data.get('type', '').lower()
        
        if 'airport' in category or 'aeroway' in osm_key:
            return 'airport'
        elif 'highway' in category or 'road' in osm_key:
            return 'address'
        elif osm_type == 'node' and category in ['amenity', 'shop', 'tourism']:
            return 'poi'
        elif osm_type in ['way', 'relation'] and 'boundary' in category:
            return 'city'
        else:
            return 'address'
    
    def _calculate_confidence(self, raw_data: Dict[str, Any], original_query: str) -> float:
        """Calculate confidence score for geocoding result"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on match quality
        display_name = raw_data.get('display_name', '').lower()
        query_lower = original_query.lower()
        
        # Exact match boost
        if query_lower in display_name:
            confidence += 0.3
        
        # Word overlap boost
        query_words = set(query_lower.split())
        display_words = set(display_name.split())
        overlap_ratio = len(query_words & display_words) / len(query_words) if query_words else 0
        confidence += overlap_ratio * 0.2
        
        # Place type boost (more specific = higher confidence)
        place_type = self._determine_place_type(raw_data)
        if place_type == 'address':
            confidence += 0.2
        elif place_type == 'poi':
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_city(self, address_components: List[str], raw_data: Dict[str, Any]) -> str:
        """Extract city name from address components"""
        
        # Look for common city indicators
        for component in address_components:
            component_lower = component.strip().lower()
            
            # Skip obvious non-city components
            if any(skip in component_lower for skip in ['postal', 'zip', 'country', 'state']):
                continue
            
            # Look for city-like components (usually 2-4 words, not too long)
            words = component.split()
            if 1 <= len(words) <= 4 and len(component) < 50:
                return component.strip()
        
        # Fallback to second-to-last component (often the city)
        if len(address_components) >= 2:
            return address_components[-2].strip()
        
        return "Unknown City"
    
    async def _get_address_alternatives(self, user_input: str) -> List[str]:
        """Generate alternative interpretations of user input"""
        
        alternatives = []
        
        # Add common variations
        variations = [
            f"{user_input} Turkey",
            f"{user_input} Istanbul",
            f"{user_input} Ankara",
            f"{user_input} city center",
            f"{user_input} merkez"
        ]
        
        alternatives.extend(variations)
        
        # Use AI to generate more alternatives if available
        if self.openrouter_api_key:
            try:
                ai_alternatives = await self._generate_ai_alternatives(user_input)
                alternatives.extend(ai_alternatives)
            except Exception as e:
                logger.warning(f"Failed to generate AI alternatives: {e}")
        
        return alternatives[:5]  # Limit to top 5 alternatives
    
    async def _generate_ai_alternatives(self, user_input: str) -> List[str]:
        """Use AI to generate alternative address interpretations"""
        
        prompt = f"""
        The user searched for: "{user_input}"
        
        Generate 3 alternative interpretations of this location, considering:
        - Different spellings
        - Adding missing context (city, country)
        - Famous landmarks or businesses with similar names
        
        Return only the alternative addresses, one per line:
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                        "temperature": 0.5
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    alternatives_text = result['choices'][0]['message']['content'].strip()
                    
                    # Parse alternatives
                    alternatives = []
                    for line in alternatives_text.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('Alternative'):
                            # Clean up numbering and formatting
                            line = re.sub(r'^\d+\.\s*', '', line)
                            line = re.sub(r'^-\s*', '', line)
                            alternatives.append(line)
                    
                    return alternatives
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"AI alternatives generation failed: {e}")
            return []
    
    async def generate_route_map(
        self,
        waypoints: List[Tuple[float, float]],
        charging_stops: Optional[List[Dict[str, Any]]] = None
    ) -> RouteMap:
        """
        Generate map data for route visualization
        
        Args:
            waypoints: List of (lat, lon) coordinates
            charging_stops: Optional charging station information
            
        Returns:
            Map data for frontend display
        """
        try:
            if not waypoints:
                raise ValueError("No waypoints provided for map generation")
            
            # Calculate route bounds
            lats = [point[0] for point in waypoints]
            lons = [point[1] for point in waypoints]
            
            bounds = {
                'north': max(lats),
                'south': min(lats),
                'east': max(lons),
                'west': min(lons)
            }
            
            # Calculate appropriate zoom level
            lat_range = bounds['north'] - bounds['south']
            lon_range = bounds['east'] - bounds['west']
            max_range = max(lat_range, lon_range)
            
            # Zoom level calculation (simplified)
            if max_range > 10:
                zoom_level = 6
            elif max_range > 5:
                zoom_level = 8
            elif max_range > 1:
                zoom_level = 10
            else:
                zoom_level = 12
            
            # Create markers
            markers = []
            
            # Start point
            if waypoints:
                markers.append({
                    'type': 'start',
                    'lat': waypoints[0][0],
                    'lon': waypoints[0][1],
                    'title': 'Başlangıç',
                    'icon': 'start'
                })
            
            # End point
            if len(waypoints) > 1:
                markers.append({
                    'type': 'destination',
                    'lat': waypoints[-1][0],
                    'lon': waypoints[-1][1],
                    'title': 'Hedef',
                    'icon': 'destination'
                })
            
            # Charging stations
            if charging_stops:
                for i, stop in enumerate(charging_stops):
                    markers.append({
                        'type': 'charging',
                        'lat': stop['location'][0],
                        'lon': stop['location'][1],
                        'title': f"Şarj İstasyonu {i+1}: {stop.get('name', 'Bilinmeyen')}",
                        'icon': 'charging',
                        'info': {
                            'power': stop.get('power_kw', 'N/A'),
                            'connector': stop.get('connector_type', 'N/A'),
                            'duration': stop.get('charging_time', 'N/A')
                        }
                    })
            
            # Generate simplified polyline (for now, just connect points)
            # In a real implementation, you'd use a routing service
            route_polyline = self._encode_polyline(waypoints)
            
            route_map = RouteMap(
                route_polyline=route_polyline,
                bounds=bounds,
                zoom_level=zoom_level,
                markers=markers
            )
            
            logger.info(f"Generated route map with {len(markers)} markers")
            return route_map
            
        except Exception as e:
            logger.error(f"Route map generation failed: {e}")
            raise
    
    def _encode_polyline(self, coordinates: List[Tuple[float, float]]) -> str:
        """
        Simple polyline encoding for route display
        (Simplified version - in production, use proper polyline encoding)
        """
        try:
            # Convert coordinates to string format for simple transmission
            # In production, use proper Google Polyline Algorithm
            encoded_points = []
            for lat, lon in coordinates:
                encoded_points.append(f"{lat:.6f},{lon:.6f}")
            
            return "|".join(encoded_points)
        except Exception as e:
            logger.error(f"Polyline encoding failed: {e}")
            return ""
    
    async def calculate_distance_between_points(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> Dict[str, float]:
        """Calculate distance and bearing between two points"""
        
        try:
            # Calculate distance using geodesic
            distance = geodesic(point1, point2).kilometers
            
            # Calculate bearing (simplified)
            lat1, lon1 = point1
            lat2, lon2 = point2
            
            import math
            dlon = math.radians(lon2 - lon1)
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            
            bearing_rad = math.atan2(
                math.sin(dlon) * math.cos(lat2_rad),
                math.cos(lat1_rad) * math.sin(lat2_rad) - 
                math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
            )
            
            bearing_deg = (math.degrees(bearing_rad) + 360) % 360
            
            return {
                'distance_km': distance,
                'bearing_degrees': bearing_deg,
                'straight_line': True
            }
            
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            return {'distance_km': 0, 'bearing_degrees': 0, 'straight_line': True}