import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import toast from 'react-hot-toast';
import { getCurrentPosition, GeolocationError } from '../utils/geolocation';
import 'leaflet/dist/leaflet.css';

const { BaseLayer, Overlay } = LayersControl;

// Fix default icon issue with Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom marker icons
const createCustomIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 30px;
        height: 30px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 3px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      ">
        <div style="
          width: 10px;
          height: 10px;
          background-color: white;
          border-radius: 50%;
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        "></div>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30],
  });
};

// Map control component to handle map updates
const MapController = ({ center, zoom }) => {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.setView(center, zoom || map.getZoom());
    }
  }, [center, zoom, map]);

  return null;
};

const MapView = ({
  vehicles = [],
  selectedVehicle = null,
  chargingStations = [],
  route = null,
  onMarkerClick = () => { },
  center = [41.0082, 28.9784], // Istanbul default
  zoom = 6
}) => {
  const [mapCenter, setMapCenter] = useState(center)
  const [mapZoom, setMapZoom] = useState(zoom)
  const [showTraffic, setShowTraffic] = useState(true)
  const [userLocation, setUserLocation] = useState(null)
  const [loadingUserLocation, setLoadingUserLocation] = useState(false)

  useEffect(() => {
    if (selectedVehicle && selectedVehicle.location) {
      setMapCenter(selectedVehicle.location)
      setMapZoom(12)
    }
  }, [selectedVehicle])

  // Update map when route changes
  useEffect(() => {
    if (route && route.route_coordinates && route.route_coordinates.length > 0) {
      // Calculate bounds to fit the route
      const coords = route.route_coordinates
      if (coords.length >= 2) {
        setMapCenter([coords[0][0], coords[0][1]])
        setMapZoom(7)
      }
    }
  }, [route])

  // Handle user location detection
  const handleShowMyLocation = async () => {
    setLoadingUserLocation(true);
    const loadingToast = toast.loading('Konumunuz alınıyor...');

    try {
      const position = await getCurrentPosition();
      setUserLocation(position);
      setMapCenter([position.lat, position.lon]);
      setMapZoom(13);

      toast.dismiss(loadingToast);
      toast.success('Konumunuz tespit edildi!', { duration: 3000 });
    } catch (err) {
      console.error('Geolocation error:', err);
      toast.dismiss(loadingToast);

      switch (err.type) {
        case GeolocationError.PERMISSION_DENIED:
          toast.error('Konum izni reddedildi', { duration: 5000 });
          break;
        case GeolocationError.POSITION_UNAVAILABLE:
          toast.error('Konum servisi kullanılamıyor', { duration: 4000 });
          break;
        case GeolocationError.TIMEOUT:
          toast.error('Konum tespiti zaman aşımına uğradı', { duration: 4000 });
          break;
        case GeolocationError.NOT_SUPPORTED:
          toast.error('Tarayıcınız konum servislerini desteklemiyor', { duration: 5000 });
          break;
        default:
          toast.error('Konum alınamadı', { duration: 4000 });
      }
    } finally {
      setLoadingUserLocation(false);
    }
  };

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      {/* Button Container */}
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        zIndex: 1001,
        display: 'flex',
        gap: '12px'
      }}>
        {/* User Location Button */}
        <button
          onClick={handleShowMyLocation}
          disabled={loadingUserLocation}
          style={{
            backgroundColor: userLocation ? '#3b82f6' : 'rgba(15, 23, 42, 0.85)',
            color: userLocation ? 'white' : '#e2e8f0',
            border: '2px solid',
            borderColor: userLocation ? '#3b82f6' : 'rgba(59, 130, 246, 0.3)',
            padding: '12px 24px',
            borderRadius: '12px',
            fontSize: '14px',
            fontWeight: '700',
            cursor: loadingUserLocation ? 'not-allowed' : 'pointer',
            boxShadow: userLocation
              ? '0 8px 24px rgba(59, 130, 246, 0.4)'
              : '0 4px 16px rgba(0, 0, 0, 0.3)',
            backdropFilter: 'blur(10px)',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            opacity: loadingUserLocation ? 0.6 : 1
          }}
          onMouseEnter={(e) => {
            if (!loadingUserLocation) {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = userLocation
                ? '0 12px 32px rgba(59, 130, 246, 0.5)'
                : '0 8px 24px rgba(0, 0, 0, 0.4)';
            }
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = userLocation
              ? '0 8px 24px rgba(59, 130, 246, 0.4)'
              : '0 4px 16px rgba(0, 0, 0, 0.3)';
          }}
        >
          <span style={{ fontSize: '18px' }}>{loadingUserLocation ? 'Loading...' : 'Location'}</span>
          <span>{userLocation ? 'Konumum' : 'Konumumu Göster'}</span>
        </button>

        {/* Traffic Toggle Button */}
        <button
          onClick={() => setShowTraffic(!showTraffic)}
          style={{
            backgroundColor: showTraffic ? '#00d4ff' : 'rgba(15, 23, 42, 0.85)',
            color: showTraffic ? '#0f172a' : '#e2e8f0',
            border: '2px solid',
            borderColor: showTraffic ? '#00d4ff' : 'rgba(0, 212, 255, 0.3)',
            padding: '12px 24px',
            borderRadius: '12px',
            fontSize: '14px',
            fontWeight: '700',
            cursor: 'pointer',
            boxShadow: showTraffic
              ? '0 8px 24px rgba(0, 212, 255, 0.4)'
              : '0 4px 16px rgba(0, 0, 0, 0.3)',
            backdropFilter: 'blur(10px)',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = showTraffic
              ? '0 12px 32px rgba(0, 212, 255, 0.5)'
              : '0 8px 24px rgba(0, 0, 0, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = showTraffic
              ? '0 8px 24px rgba(0, 212, 255, 0.4)'
              : '0 4px 16px rgba(0, 0, 0, 0.3)';
          }}
        >
          <span style={{ fontSize: '18px' }}>{showTraffic ? 'Traffic' : 'Traffic'}</span>
          <span>{showTraffic ? 'Trafik Aktif' : 'Trafiği Göster'}</span>
        </button>
      </div>

      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        <MapController center={mapCenter} zoom={mapZoom} />

        {/* Base map layer - OpenStreetMap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Traffic Layer - OpenStreetMap with traffic simulation overlay */}
        {showTraffic && (
          <TileLayer
            url="https://{s}.api.tomtom.com/traffic/map/4/tile/flow/relative/{z}/{x}/{y}.png?key=w9xr4Dka9SWOvK8QhPy5tSTvAS9lj3Cq"
            attribution='Traffic data &copy; <a href="https://www.tomtom.com">TomTom</a>'
            opacity={0.6}
            zIndex={1000}
          />
        )}

        {/* User Location Marker */}
        {userLocation && (
          <>
            <Circle
              center={[userLocation.lat, userLocation.lon]}
              radius={userLocation.accuracy}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.1,
                weight: 2
              }}
            />
            <Marker
              position={[userLocation.lat, userLocation.lon]}
              icon={createCustomIcon('#3b82f6')} // Blue for user location
            >
              <Popup>
                <div style={{ minWidth: '200px' }}>
                  <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: 'bold' }}>
                    Mevcut Konumunuz
                  </h3>
                  <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Konum:</strong> {userLocation.lat.toFixed(5)}, {userLocation.lon.toFixed(5)}
                    </p>
                    <p style={{ margin: '5px 0' }}>
                      <strong>Doğruluk:</strong> ±{Math.round(userLocation.accuracy)}m
                    </p>
                  </div>
                </div>
              </Popup>
            </Marker>
          </>
        )}

        {/* Charging stations markers */}
        {chargingStations.map((station, index) => (
          <Marker
            key={`station-${index}`}
            position={[station.latitude, station.longitude]}
            icon={createCustomIcon('#10b981')} // Green for charging stations
            eventHandlers={{
              click: () => onMarkerClick({ type: 'station', data: station })
            }}
          >
            <Popup>
              <div style={{ minWidth: '200px' }}>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: 'bold' }}>
                  {station.name || 'Charging Station'}
                </h3>
                <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Power:</strong> {station.power_kw || 'N/A'} kW
                  </p>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Type:</strong> {station.connector_type || 'Universal'}
                  </p>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Price:</strong> ${station.price_per_kwh || '0.30'}/kWh
                  </p>
                  {station.availability && (
                    <p style={{ margin: '5px 0' }}>
                      <strong>Available:</strong> {station.availability} ports
                    </p>
                  )}
                  {station.address && (
                    <p style={{ margin: '5px 0', color: '#666' }}>
                      {station.address}
                    </p>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Vehicle location markers (if vehicles have location data) */}
        {vehicles.filter(v => v.location).map((vehicle, index) => (
          <Marker
            key={`vehicle-${index}`}
            position={vehicle.location}
            icon={createCustomIcon('#667eea')} // Purple for vehicles
            eventHandlers={{
              click: () => onMarkerClick({ type: 'vehicle', data: vehicle })
            }}
          >
            <Popup>
              <div style={{ minWidth: '200px' }}>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: 'bold' }}>
                  {vehicle.make} {vehicle.model}
                </h3>
                <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Range:</strong> {vehicle.electric_range_km} km
                  </p>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Battery:</strong> {vehicle.battery_capacity_kwh} kWh
                  </p>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Price:</strong> ${vehicle.base_msrp_usd?.toLocaleString()}
                  </p>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Route polyline (if route data exists) */}
        {route && route.route_coordinates && route.route_coordinates.length > 1 && (
          <Polyline
            positions={route.route_coordinates}
            color="#667eea"
            weight={5}
            opacity={0.8}
          />
        )}

        {/* Route waypoints (charging stops) */}
        {route && route.charging_stops && route.charging_stops.map((stop, index) => (
          <Marker
            key={`route-stop-${index}`}
            position={[stop.latitude || 0, stop.longitude || 0]}
            icon={createCustomIcon('#ff6b6b')} // Red for route stops
          >
            <Popup>
              <div style={{ minWidth: '250px' }}>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: 'bold', color: '#667eea' }}>
                  Şarj Durağı {index + 1}: {stop.name || 'Şarj İstasyonu'}
                </h3>
                <div style={{ fontSize: '14px', lineHeight: '1.8' }}>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Güç:</strong> {stop.power_kw || 50} kW
                  </p>
                  <p style={{ margin: '5px 0' }}>
                    <strong>Şarj Süresi:</strong> {stop.charging_time_minutes || 30} dakika
                  </p>
                  {stop.station_id && (
                    <p style={{ margin: '5px 0', fontSize: '12px', color: '#666' }}>
                      ID: {stop.station_id}
                    </p>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Start and end markers for route */}
        {route && route.waypoints && route.waypoints.length > 0 && (
          <>
            {route.waypoints.filter(w => w.type === 'start').map((wp, i) => (
              <Marker
                key={`start-${i}`}
                position={[wp.latitude, wp.longitude]}
                icon={createCustomIcon('#4caf50')} // Green for start
              >
                <Popup>
                  <div><strong>Başlangıç</strong></div>
                </Popup>
              </Marker>
            ))}
            {route.waypoints.filter(w => w.type === 'end').map((wp, i) => (
              <Marker
                key={`end-${i}`}
                position={[wp.latitude, wp.longitude]}
                icon={createCustomIcon('#f44336')} // Red for end
              >
                <Popup>
                  <div><strong>Varış</strong></div>
                </Popup>
              </Marker>
            ))}
          </>
        )}
      </MapContainer>

      {/* Map legend */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        right: '20px',
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(10px)',
        padding: '18px',
        borderRadius: '12px',
        border: '1px solid rgba(0, 212, 255, 0.2)',
        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
        zIndex: 1000,
        fontSize: '13px',
        color: '#e2e8f0',
        minWidth: '180px'
      }}>
        <div style={{
          fontWeight: 'bold',
          marginBottom: '12px',
          fontSize: '15px',
          color: '#00d4ff',
          letterSpacing: '0.5px'
        }}>Legend</div>

        {showTraffic && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '8px',
            padding: '6px',
            background: 'rgba(0, 212, 255, 0.1)',
            borderRadius: '6px',
            border: '1px solid rgba(0, 212, 255, 0.2)'
          }}>
            <span style={{ marginRight: '8px', fontSize: '16px' }}>Traffic</span>
            <span style={{ color: '#00ff88', fontWeight: '600' }}>Trafik Katmanı Aktif</span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: '#10b981',
            borderRadius: '50%',
            marginRight: '10px',
            border: '2px solid white'
          }}></div>
          <span>Charging Stations</span>
        </div>
        {route && route.charging_stops && route.charging_stops.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              backgroundColor: '#ff6b6b',
              borderRadius: '50%',
              marginRight: '10px',
              border: '2px solid white'
            }}></div>
            <span>Route Stops ({route.charging_stops.length})</span>
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: '20px',
            height: '20px',
            backgroundColor: '#667eea',
            borderRadius: '50%',
            marginRight: '10px',
            border: '2px solid white'
          }}></div>
          <span>Vehicle Locations</span>
        </div>
      </div>

      {/* Route summary overlay */}
      {route && route.route_summary && (
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 212, 255, 0.3)',
          padding: '20px 24px',
          borderRadius: '16px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          zIndex: 1000,
          minWidth: '320px'
        }}>
          <div style={{
            fontWeight: 'bold',
            fontSize: '18px',
            marginBottom: '16px',
            color: '#00d4ff',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span>Location</span>
            <span>Rota Özeti</span>
            {route.route_summary?.with_traffic && (
              <span style={{
                fontSize: '12px',
                background: 'linear-gradient(135deg, #00ff88 0%, #00d4ff 100%)',
                padding: '4px 10px',
                borderRadius: '12px',
                color: '#0f172a',
                fontWeight: '700',
                marginLeft: 'auto'
              }}>
                Canlı Trafik
              </span>
            )}
          </div>
          <div style={{ fontSize: '14px', lineHeight: '2', color: '#e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span>Mesafe:</span>
              <strong style={{ color: '#00d4ff' }}>{route.route_summary?.total_distance_km || 0} km</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span>Sürüş Süresi:</span>
              <strong style={{ color: '#f1f5f9' }}>{Math.floor((route.route_summary?.driving_time_minutes || 0) / 60)}s {Math.round((route.route_summary?.driving_time_minutes || 0) % 60)}dk</strong>
            </div>
            {route.route_summary?.traffic_delay_minutes > 0 && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '6px',
                padding: '6px',
                background: 'rgba(255, 68, 68, 0.15)',
                borderRadius: '8px',
                border: '1px solid rgba(255, 68, 68, 0.3)'
              }}>
                <span style={{ color: '#ff6b6b' }}>Trafik Gecikmesi:</span>
                <strong style={{ color: '#ff4444' }}>+{Math.round(route.route_summary?.traffic_delay_minutes)} dk</strong>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span>Şarj Süreleri:</span>
              <strong style={{ color: '#f1f5f9' }}>{route.route_summary?.charging_time_minutes || 0} dk</strong>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '12px',
              paddingTop: '8px',
              borderTop: '1px solid rgba(0, 212, 255, 0.2)'
            }}>
              <span style={{ fontWeight: '600' }}>Toplam Süre:</span>
              <strong style={{ color: '#00ff88', fontSize: '15px' }}>
                {Math.floor((route.route_summary?.total_time_minutes || 0) / 60)}s {Math.round((route.route_summary?.total_time_minutes || 0) % 60)}dk
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span>Şarj Durakları:</span>
              <strong>{route.route_summary?.num_charging_stops || 0} adet</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span>Şarj Süresi:</span>
              <strong>{route.route_summary?.charging_time_minutes || 0} dk</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span>Enerji:</span>
              <strong>{route.route_summary?.energy_needed_kwh || 0} kWh</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #e0e0e0' }}>
              <span style={{ color: '#28a745', fontWeight: '600' }}>Toplam Maliyet:</span>
              <strong style={{ color: '#28a745' }}>{route.route_summary?.estimated_cost_tl?.toFixed(2) || '0.00'} ₺</strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapView;
