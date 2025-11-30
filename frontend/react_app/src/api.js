import axios from 'axios'

const base = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function getVehicles(){
  const res = await axios.get(`${base}/api/vehicles/`)
  // Direct array response from CSV
  return Array.isArray(res.data) ? res.data : (res.data?.vehicles || res.data?.items || [])
}

export async function aiChat(prompt){
  try{
    const res = await axios.post(`${base}/api/ai-chat`, {message: prompt})
    return res.data
  }catch(err){
    console.error('aiChat err', err?.response?.data || err.message)
    return { error: true, message: err?.response?.data || err.message }
  }
}

export async function getChargingStations(filters = {}) {
  try {
    const params = new URLSearchParams()
    
    if (filters.lat && filters.lon) {
      params.append('lat', filters.lat)
      params.append('lon', filters.lon)
    }
    if (filters.radius) params.append('radius', filters.radius)
    if (filters.city) params.append('city', filters.city)
    if (filters.min_power) params.append('min_power', filters.min_power)
    if (filters.max_power) params.append('max_power', filters.max_power)
    
    const response = await axios.get(`${base}/api/charging/stations?${params.toString()}`)
    return response.data
  } catch (error) {
    console.error('Charging stations error:', error)
    throw error
  }
}

export async function planRoute(routeData) {
  try {
    const params = new URLSearchParams()
    params.append('start_lat', routeData.start_lat)
    params.append('start_lon', routeData.start_lon)
    params.append('end_lat', routeData.end_lat)
    params.append('end_lon', routeData.end_lon)
    params.append('vehicle_range_km', routeData.vehicle_range_km)
    params.append('battery_capacity_kwh', routeData.battery_capacity_kwh)
    if (routeData.current_battery_percent) params.append('current_battery_percent', routeData.current_battery_percent)
    if (routeData.min_charge_percent) params.append('min_charge_percent', routeData.min_charge_percent)
    if (routeData.preferred_charge_percent) params.append('preferred_charge_percent', routeData.preferred_charge_percent)
    
    const response = await axios.post(`${base}/api/navigation/simple-route?${params.toString()}`)
    return response.data
  } catch (error) {
    console.error('Route planning error:', error)
    throw error
  }
}
