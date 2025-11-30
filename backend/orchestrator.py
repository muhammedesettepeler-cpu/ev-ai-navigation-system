"""
EV Navigation System - Main Orchestrator.

Minimal orchestrator for service initialization and route registration.
"""

import logging
import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Path setup
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import after path setup
from src.exceptions.custom_exceptions import EVNavigationException
from src.middleware.error_handlers import (
    ev_navigation_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.services.database_service import DatabaseService
from src.services.redis_service import RedisService

# Initialize core services
database_service = DatabaseService()
redis_service = RedisService()
logger.info("Core services initialized")


# Route import helper
def import_route(route_name):
    """Import route with error handling."""
    try:
        module = __import__(f"routes.{route_name}", fromlist=[route_name])
        logger.info(f"✓ {route_name} loaded")
        return module.router, True
    except Exception as e:
        logger.warning(f"✗ {route_name} unavailable: {e}")
        return None, False


# Import routes
auth_router, AUTH_OK = import_route("auth")
favorites_router, FAV_OK = import_route("favorites")
vehicles_router, VEH_OK = import_route("vehicles")
charging_router, CHG_OK = import_route("charging")
navigation_router, NAV_OK = import_route("navigation")
status_router, STA_OK = import_route("status")

# Create app
app = FastAPI(
    title="EV Navigation API",
    version="2.0",
    description="Electric Vehicle Navigation System",
)

# CORS
origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(EVNavigationException, ev_navigation_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register routes
if AUTH_OK:
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
if FAV_OK:
    app.include_router(favorites_router, prefix="/api/favorites", tags=["Favorites"])
if VEH_OK:
    app.include_router(vehicles_router, prefix="/api/vehicles", tags=["Vehicles"])
if CHG_OK:
    app.include_router(charging_router, prefix="/api/charging", tags=["Charging"])
if NAV_OK:
    app.include_router(navigation_router, prefix="/api/navigation", tags=["Navigation"])
if STA_OK:
    app.include_router(status_router, prefix="/api", tags=["Status"])

logger.info("Routes registered")


@app.get("/")
def root():
    """API root."""
    return {
        "name": "EV Navigation API",
        "version": "2.0",
        "status": "active",
        "routes": {
            "auth": AUTH_OK,
            "favorites": FAV_OK,
            "vehicles": VEH_OK,
            "charging": CHG_OK,
            "navigation": NAV_OK,
            "status": STA_OK,
        },
    }


if __name__ == "__main__":
    uvicorn.run("orchestrator:app", host="0.0.0.0", port=8000, reload=False)
