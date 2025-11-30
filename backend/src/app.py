"""
EV Navigation System - Basic Starter Version
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="EV Navigation System API",
    description="Intelligent navigation system for electric vehicles with charging station optimization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ev-navigation-api"}

# Basic navigation endpoint
@app.get("/api/v1/navigation/info")
async def navigation_info():
    """Get navigation system information"""
    return {
        "message": "EV Navigation System is running!",
        "version": "1.0.0",
        "features": [
            "Route optimization for electric vehicles",
            "Charging station recommendations", 
            "AI-powered route insights",
            "Multi-model vehicle support"
        ]
    }

# Basic vehicle models endpoint
@app.get("/api/v1/vehicles")
async def get_vehicle_models():
    """Get supported vehicle models"""
    return {
        "vehicles": [
            {"manufacturer": "Tesla", "models": ["Model S", "Model 3", "Model Y", "Model X"]},
            {"manufacturer": "BMW", "models": ["iX", "i4", "i7"]},
            {"manufacturer": "Mercedes-Benz", "models": ["EQS", "EQC", "EQE"]},
            {"manufacturer": "Volkswagen", "models": ["ID.4", "ID.3", "ID.Buzz"]},
            {"manufacturer": "Hyundai", "models": ["IONIQ 5", "IONIQ 6"]},
            {"manufacturer": "Nissan", "models": ["Leaf", "Ariya"]}
        ]
    }

# Basic charging stations endpoint
@app.get("/api/v1/charging")
async def get_charging_info():
    """Get charging station information"""
    return {
        "message": "Charging station service is available",
        "supported_connectors": ["CCS1", "CCS2", "CHAdeMO", "Tesla", "Type2"],
        "features": [
            "Real-time availability",
            "Route-optimized placement",
            "Multi-network support",
            "Price comparison"
        ]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(" Starting EV Navigation System API...")
    logger.info(" EV Navigation System API started successfully!")

if __name__ == "__main__":
    # Run the application
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )