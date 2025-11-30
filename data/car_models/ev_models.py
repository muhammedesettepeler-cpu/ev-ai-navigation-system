"""
Electric Vehicle Models Data
Loads vehicle data from CSV file
"""
import csv
from pathlib import Path

def load_vehicles_from_csv():
    """Load all vehicles from the CSV file"""
    vehicles = []
    csv_path = Path(__file__).parent / "electric_vehicles_spec_2025.csv"
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, 1):
                try:
                    # Parse numeric fields with fallbacks
                    battery_kwh = float(row.get('battery_capacity_kWh', 0) or 0)
                    range_km = int(float(row.get('range_km', 0) or 0))
                    efficiency = float(row.get('efficiency_Wh_km', 0) or 0)
                    
                    # Calculate energy consumption (convert Wh/km to kWh/100km)
                    energy_consumption = (efficiency / 10) if efficiency > 0 else 15.0
                    
                    # Get brand
                    brand = row.get('brand', 'Unknown')
                    
                    # Estimate price based on brand and battery
                    if brand.lower() in ['tesla', 'porsche', 'mercedes-benz', 'audi', 'bmw']:
                        base_price = 50000
                    elif brand.lower() in ['volkswagen', 'ford', 'hyundai', 'kia']:
                        base_price = 35000
                    else:
                        base_price = 30000
                    price_usd = int(base_price + (battery_kwh * 400))
                    
                    # Determine connectors
                    port = row.get('fast_charge_port', 'CCS').strip()
                    if 'CCS' in port:
                        connectors = ['CCS1', 'CCS2']
                    elif 'Tesla' in port:
                        connectors = ['Tesla', 'CCS1']
                    elif 'CHAdeMO' in port:
                        connectors = ['CHAdeMO', 'CCS1']
                    else:
                        connectors = ['CCS1']
                    
                    vehicle = {
                        "id": idx,
                        "model": row.get('model', f'Model {idx}'),
                        "manufacturer": brand,
                        "year": int(row.get('year', 2024) or 2024),
                        "category": row.get('category', 'Electric'),
                        "battery_capacity_kwh": battery_kwh,
                        "range_km": range_km,
                        "energy_consumption_kwh_per_100km": energy_consumption,
                        "fast_charge_power_kw": int(float(row.get('fast_charge_power_kW', 0) or 0)) if row.get('fast_charge_power_kW') else None,
                        "fast_charge_time_min": int(float(row.get('fast_charge_time_min', 0) or 0)) if row.get('fast_charge_time_min') else None,
                        "acceleration_0_100_kmh": float(row.get('acceleration_0_100_s', 0) or 0) if row.get('acceleration_0_100_s') else None,
                        "supported_connectors": connectors,
                        "top_speed_kmh": int(float(row.get('top_speed_kmh', 0) or 0)) if row.get('top_speed_kmh') else None,
                        "price_usd": price_usd,
                        "drivetrain": row.get('drivetrain', 'FWD'),
                        "body_type": row.get('car_body_type', 'Sedan'),
                        "seats": int(row.get('seats', 5) or 5),
                        "cargo_volume_l": int(row.get('cargo_volume_l', 0) or 0),
                        "source_url": row.get('source_url', '')
                    }
                    vehicles.append(vehicle)
                except (ValueError, TypeError) as e:
                    print(f"Error parsing vehicle row {idx}: {e}")
                    continue
        
        print(f"Loaded {len(vehicles)} vehicles from CSV")
        return vehicles
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

# Load all vehicles from CSV
ALL_VEHICLES_FROM_CSV = load_vehicles_from_csv()

# Create flat list for API
FLAT_CAR_MODELS = ALL_VEHICLES_FROM_CSV

# Group vehicles by manufacturer
ALL_CAR_MODELS = {}
for vehicle in ALL_VEHICLES_FROM_CSV:
    manufacturer = vehicle['manufacturer']
    if manufacturer not in ALL_CAR_MODELS:
        ALL_CAR_MODELS[manufacturer] = []
    ALL_CAR_MODELS[manufacturer].append(vehicle)

# Helper functions
def get_car_by_id(car_id):
    """Get a car by its ID"""
    for car in FLAT_CAR_MODELS:
        if car['id'] == car_id:
            return car
    return None

def get_cars_by_manufacturer(manufacturer):
    """Get all cars from a specific manufacturer"""
    return ALL_CAR_MODELS.get(manufacturer, [])

def get_cars_by_category(category):
    """Get all cars in a specific category"""
    return [car for car in FLAT_CAR_MODELS if car['category'] == category]

# Print summary
print(f"EV Models loaded: {len(FLAT_CAR_MODELS)} vehicles from {len(ALL_CAR_MODELS)} manufacturers")
