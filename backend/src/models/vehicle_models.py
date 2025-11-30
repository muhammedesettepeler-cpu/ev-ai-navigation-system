"""
Vehicle Models and Specifications
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class ConnectorType(str, Enum):
    CCS1 = "CCS1"
    CCS2 = "CCS2"
    CHADEMO = "CHAdeMO"
    TESLA = "Tesla"
    TYPE2 = "Type2"
    TYPE1 = "Type1"

class VehicleCategory(str, Enum):
    SEDAN = "sedan"
    SUV = "suv"
    HATCHBACK = "hatchback"
    TRUCK = "truck"
    VAN = "van"
    SPORTS = "sports"

class VehicleSpecs(BaseModel):
    model: str = Field(..., description="Vehicle model name")
    manufacturer: str = Field(..., description="Vehicle manufacturer")
    year: int = Field(..., description="Model year")
    category: VehicleCategory = Field(..., description="Vehicle category")
    
    # Battery specifications
    battery_capacity_kwh: float = Field(..., description="Total battery capacity in kWh")
    usable_battery_capacity_kwh: float = Field(..., description="Usable battery capacity in kWh")
    
    # Range and efficiency
    epa_range_km: float = Field(..., description="EPA estimated range in km")
    wltp_range_km: Optional[float] = Field(None, description="WLTP estimated range in km")
    energy_consumption_kwh_per_100km: float = Field(..., description="Energy consumption per 100km")
    
    # Charging specifications
    max_charging_power_kw: float = Field(..., description="Maximum charging power in kW")
    charging_curve: Dict[str, float] = Field(default={}, description="Charging curve (SOC% -> Power kW)")
    supported_connectors: List[ConnectorType] = Field(..., description="Supported charging connectors")
    
    # Performance characteristics
    acceleration_0_100_kmh: Optional[float] = Field(None, description="0-100 km/h acceleration time")
    top_speed_kmh: Optional[int] = Field(None, description="Top speed in km/h")
    drag_coefficient: Optional[float] = Field(None, description="Aerodynamic drag coefficient")
    
    # Physical specifications
    weight_kg: int = Field(..., description="Vehicle weight in kg")
    length_mm: int = Field(..., description="Vehicle length in mm")
    width_mm: int = Field(..., description="Vehicle width in mm")
    height_mm: int = Field(..., description="Vehicle height in mm")
    
    # Additional features
    features: List[str] = Field(default=[], description="Special features")
    autonomous_level: int = Field(default=0, description="Autonomous driving level (0-5)")

class VehicleDatabase(BaseModel):
    """Collection of vehicle models"""
    vehicles: List[VehicleSpecs] = Field(default=[], description="List of vehicle specifications")
    
    def get_vehicle_by_model(self, model: str) -> Optional[VehicleSpecs]:
        """Get vehicle specs by model name"""
        for vehicle in self.vehicles:
            if vehicle.model.lower() == model.lower():
                return vehicle
        return None
    
    def get_vehicles_by_manufacturer(self, manufacturer: str) -> List[VehicleSpecs]:
        """Get vehicles by manufacturer"""
        return [v for v in self.vehicles if v.manufacturer.lower() == manufacturer.lower()]
    
    def get_vehicles_by_category(self, category: VehicleCategory) -> List[VehicleSpecs]:
        """Get vehicles by category"""
        return [v for v in self.vehicles if v.category == category]

# Pre-defined vehicle specifications
DEFAULT_VEHICLES = [
    VehicleSpecs(
        model="Model S",
        manufacturer="Tesla",
        year=2024,
        category=VehicleCategory.SEDAN,
        battery_capacity_kwh=100.0,
        usable_battery_capacity_kwh=95.0,
        epa_range_km=652,
        wltp_range_km=634,
        energy_consumption_kwh_per_100km=15.0,
        max_charging_power_kw=250,
        charging_curve={
            "10": 250, "20": 250, "30": 240, "40": 220, 
            "50": 200, "60": 180, "70": 150, "80": 120, "90": 80
        },
        supported_connectors=[ConnectorType.TESLA, ConnectorType.CCS1],
        acceleration_0_100_kmh=3.1,
        top_speed_kmh=250,
        drag_coefficient=0.208,
        weight_kg=2265,
        length_mm=5021,
        width_mm=1987,
        height_mm=1431,
        features=["Autopilot", "Over-the-air updates", "Supercharger network"],
        autonomous_level=3
    ),
    VehicleSpecs(
        model="iX",
        manufacturer="BMW",
        year=2024,
        category=VehicleCategory.SUV,
        battery_capacity_kwh=111.5,
        usable_battery_capacity_kwh=105.2,
        epa_range_km=610,
        wltp_range_km=630,
        energy_consumption_kwh_per_100km=17.2,
        max_charging_power_kw=195,
        charging_curve={
            "10": 195, "20": 190, "30": 185, "40": 175,
            "50": 165, "60": 150, "70": 130, "80": 100, "90": 65
        },
        supported_connectors=[ConnectorType.CCS2],
        acceleration_0_100_kmh=4.6,
        top_speed_kmh=200,
        drag_coefficient=0.25,
        weight_kg=2585,
        length_mm=4953,
        width_mm=1967,
        height_mm=1695,
        features=["xDrive AWD", "Curved display", "BMW Digital Key Plus"],
        autonomous_level=2
    ),
    VehicleSpecs(
        model="EQS",
        manufacturer="Mercedes-Benz",
        year=2024,
        category=VehicleCategory.SEDAN,
        battery_capacity_kwh=107.8,
        usable_battery_capacity_kwh=102.0,
        epa_range_km=770,
        wltp_range_km=780,
        energy_consumption_kwh_per_100km=13.2,
        max_charging_power_kw=200,
        charging_curve={
            "10": 200, "20": 200, "30": 195, "40": 185,
            "50": 170, "60": 155, "70": 140, "80": 115, "90": 70
        },
        supported_connectors=[ConnectorType.CCS2],
        acceleration_0_100_kmh=4.3,
        top_speed_kmh=250,
        drag_coefficient=0.20,
        weight_kg=2480,
        length_mm=5216,
        width_mm=1926,
        height_mm=1512,
        features=["MBUX Hyperscreen", "Air suspension", "Door handle sensors"],
        autonomous_level=3
    ),
    VehicleSpecs(
        model="ID.4",
        manufacturer="Volkswagen",
        year=2024,
        category=VehicleCategory.SUV,
        battery_capacity_kwh=82.0,
        usable_battery_capacity_kwh=77.0,
        epa_range_km=442,
        wltp_range_km=520,
        energy_consumption_kwh_per_100km=17.4,
        max_charging_power_kw=135,
        charging_curve={
            "10": 135, "20": 130, "30": 125, "40": 120,
            "50": 110, "60": 95, "70": 80, "80": 60, "90": 40
        },
        supported_connectors=[ConnectorType.CCS2],
        acceleration_0_100_kmh=8.5,
        top_speed_kmh=160,
        drag_coefficient=0.28,
        weight_kg=2124,
        length_mm=4584,
        width_mm=1852,
        height_mm=1612,
        features=["4MOTION AWD", "Travel Assist", "Wireless CarPlay"],
        autonomous_level=2
    ),
    VehicleSpecs(
        model="Leaf",
        manufacturer="Nissan",
        year=2024,
        category=VehicleCategory.HATCHBACK,
        battery_capacity_kwh=62.0,
        usable_battery_capacity_kwh=58.0,
        epa_range_km=364,
        wltp_range_km=385,
        energy_consumption_kwh_per_100km=15.9,
        max_charging_power_kw=100,
        charging_curve={
            "10": 100, "20": 95, "30": 90, "40": 85,
            "50": 75, "60": 65, "70": 55, "80": 40, "90": 25
        },
        supported_connectors=[ConnectorType.CHADEMO, ConnectorType.TYPE2],
        acceleration_0_100_kmh=7.9,
        top_speed_kmh=157,
        drag_coefficient=0.28,
        weight_kg=1748,
        length_mm=4490,
        width_mm=1788,
        height_mm=1530,
        features=["ProPILOT Assist", "e-Pedal", "Intelligent Key"],
        autonomous_level=2
    )
]