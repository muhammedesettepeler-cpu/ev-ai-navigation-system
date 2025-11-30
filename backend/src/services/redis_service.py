"""
Redis Service - Caching and session management orchestration
"""
import redis
import json
import logging
import os
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RedisService:
    """Redis caching and session service"""
    
    def __init__(self):
        """Initialize Redis connections with cloud and local fallback"""
        self.redis_client = None
        self.is_cloud_connected = False
        self.is_local_connected = False
        
        # Redis Cloud configuration
        self.cloud_config = {
            'host': os.getenv("REDIS_CLOUD_HOST"),
            'port': int(os.getenv("REDIS_CLOUD_PORT", 6379)),
            'password': os.getenv("REDIS_CLOUD_PASSWORD"),
            'ssl': True,
            'ssl_cert_reqs': None,
            'socket_connect_timeout': 10,
            'socket_timeout': 10
        }
        
        # Local Redis configuration
        self.local_config = {
            'host': os.getenv("REDIS_HOST", "localhost"),
            'port': int(os.getenv("REDIS_PORT", 6379)),
            'decode_responses': True
        }
        
        # Initialize connection
        self.connect()
    
    def connect(self):
        """Try Redis Cloud first, fallback to local Redis"""
        
        # Skip Redis Cloud - use local only
        try:
            local_client = redis.Redis(**self.local_config)
            local_client.ping()
            self.redis_client = local_client
            self.is_local_connected = True
            logger.info("Local Redis connected")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self.redis_client is not None
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        try:
            if self.redis_client:
                info = await self.redis_client.info()
                return {
                    "connected": True,
                    "type": "Redis Cloud" if self.is_cloud_connected else "Local Redis",
                    "version": info.get("redis_version", "unknown"),
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "host": self.cloud_config['host'] if self.is_cloud_connected else self.local_config['host']
                }
            else:
                return {
                    "connected": False,
                    "type": "None",
                    "error": "No Redis connection available"
                }
        except Exception as e:
            return {
                "connected": False,
                "type": "Error", 
                "error": str(e)
            }
    
    async def set_cache(self, key: str, value: Union[str, dict], expire_seconds: int = 3600) -> bool:
        """Set cache with expiration"""
        if not self.redis_client:
            logger.warning("Redis not available - cache operation skipped")
            return False
        
        try:
            if isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            
            result = await self.redis_client.setex(key, expire_seconds, value)
            logger.info(f"Cache set: {key} (expires in {expire_seconds}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Union[str, dict]]:
        """Get cache value"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete cache key"""
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            logger.info(f"Cache deleted: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def set_session(self, session_id: str, data: dict, expire_hours: int = 24) -> bool:
        """Set user session data"""
        session_key = f"session:{session_id}"
        expire_seconds = expire_hours * 3600
        return await self.set_cache(session_key, data, expire_seconds)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session data"""
        session_key = f"session:{session_id}"
        result = await self.get_cache(session_key)
        return result if isinstance(result, dict) else None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        session_key = f"session:{session_id}"
        return self.delete_cache(session_key)
    
    async def cache_vehicles(self, vehicles_data: dict, expire_minutes: int = 30) -> bool:
        """Cache vehicles data"""
        return await self.set_cache("vehicles:all", vehicles_data, expire_minutes * 60)
    
    async def get_cached_vehicles(self) -> Optional[dict]:
        """Get cached vehicles data"""
        result = await self.get_cache("vehicles:all")
        return result if isinstance(result, dict) else None
    
    async def cache_route(self, route_key: str, route_data: dict, expire_minutes: int = 60) -> bool:
        """Cache route planning result"""
        cache_key = f"route:{route_key}"
        return await self.set_cache(cache_key, route_data, expire_minutes * 60)
    
    async def get_cached_route(self, route_key: str) -> Optional[dict]:
        """Get cached route data"""
        cache_key = f"route:{route_key}"
        result = await self.get_cache(cache_key)
        return result if isinstance(result, dict) else None
    
    async def cache_ai_response(self, query_hash: str, response: dict, expire_hours: int = 6) -> bool:
        """Cache AI chatbot responses"""
        cache_key = f"ai_response:{query_hash}"
        return await self.set_cache(cache_key, response, expire_hours * 3600)
    
    async def get_cached_ai_response(self, query_hash: str) -> Optional[dict]:
        """Get cached AI response"""
        cache_key = f"ai_response:{query_hash}"
        result = await self.get_cache(cache_key)
        return result if isinstance(result, dict) else None
    
    def clear_all_cache(self) -> bool:
        """Clear all cache (development only)"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("All cache cleared!")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"error": "Redis not connected"}
        
        try:
            info = await self.redis_client.info()
            
            # Count keys by pattern
            session_keys_list = await self.redis_client.keys("session:*")
            vehicle_keys_list = await self.redis_client.keys("vehicles:*")
            route_keys_list = await self.redis_client.keys("route:*")
            ai_keys_list = await self.redis_client.keys("ai_response:*")
            
            return {
                "total_keys": info.get("db0", {}).get("keys", 0),
                "memory_used": info.get("used_memory_human", "0B"),
                "sessions": len(session_keys_list),
                "vehicles_cache": len(vehicle_keys_list),
                "routes_cache": len(route_keys_list),
                "ai_responses": len(ai_keys_list),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"error": str(e)}