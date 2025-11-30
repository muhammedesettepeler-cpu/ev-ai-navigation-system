import React, { useEffect, useState } from 'react'
import { getVehicles, aiChat, getChargingStations, planRoute } from './api'
import MapView from './components/MapView'
import RouteForm from './components/RouteForm'
import { getFavorites, toggleFavorite, isFavorite } from './utils/favorites'
import toast, { Toaster } from 'react-hot-toast'
import './modern-styles.css'

export default function App() {
  const [vehicles, setVehicles] = useState([])
  const [filteredVehicles, setFilteredVehicles] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [chatMessages, setChatMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [selectedVehicle, setSelectedVehicle] = useState(null)
  const [viewMode, setViewMode] = useState('map') // 'map', 'list', 'route', 'favorites'
  const [chargingStations, setChargingStations] = useState([])
  const [stationsLoading, setStationsLoading] = useState(false)
  const [powerFilter, setPowerFilter] = useState('all') // 'all', 'fast', 'normal'
  const [favorites, setFavorites] = useState([])
  const [showFavoritesModal, setShowFavoritesModal] = useState(false)

  // Route planning state
  const [routeForm, setRouteForm] = useState({
    start_lat: '',
    start_lon: '',
    end_lat: '',
    end_lon: '',
    selected_vehicle_id: null
  })
  const [routeResult, setRouteResult] = useState(null)
  const [routePlanning, setRoutePlanning] = useState(false)

  // Load vehicles on mount
  useEffect(() => {
    console.log('App mounted, fetching vehicles...')
    setLoading(true)
    getVehicles()
      .then(v => {
        console.log('Vehicles received:', v)
        setVehicles(v || [])
        setFilteredVehicles(v || [])
        setLoading(false)
        // Load favorites
        setFavorites(getFavorites())
      })
      .catch(err => {
        console.error('Vehicle fetch error:', err)
        setLoading(false)
      })
  }, [])

  // Load charging stations on mount
  useEffect(() => {
    console.log('Loading charging stations...')
    setStationsLoading(true)
    getChargingStations()
      .then(data => {
        console.log('Charging stations received:', data)
        setChargingStations(data?.stations || [])
        setStationsLoading(false)
      })
      .catch(err => {
        console.error('Charging stations fetch error:', err)
        setStationsLoading(false)
      })
  }, [])

  // Filter vehicles based on search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredVehicles(vehicles)
      return
    }
    const query = searchQuery.toLowerCase()
    const filtered = vehicles.filter(v =>
      (v.manufacturer || v.make || '').toLowerCase().includes(query) ||
      (v.model || '').toLowerCase().includes(query) ||
      (v.year || '').toString().includes(query)
    )
    setFilteredVehicles(filtered)
  }, [searchQuery, vehicles])

  // Filter charging stations by power
  const getFilteredStations = () => {
    if (powerFilter === 'all') return chargingStations
    if (powerFilter === 'fast') {
      return chargingStations.filter(s => s.power_kw >= 50)
    }
    if (powerFilter === 'normal') {
      return chargingStations.filter(s => s.power_kw < 50)
    }
    return chargingStations
  }

  // Handle AI chat
  const handleSendMessage = async () => {
    if (!currentMessage.trim()) return

    const userMsg = { role: 'user', content: currentMessage }
    setChatMessages(prev => [...prev, userMsg])
    setCurrentMessage('')

    const aiMsg = { role: 'assistant', content: 'Thinking...' }
    setChatMessages(prev => [...prev, aiMsg])

    const res = await aiChat(currentMessage)
    setChatMessages(prev => {
      const newMsgs = [...prev]
      newMsgs[newMsgs.length - 1] = {
        role: 'assistant',
        content: res?.ai_response || 'Sorry, I could not process that.',
        model: res?.model_used || 'unknown'
      }
      return newMsgs
    })
  }

  // Handle route planning
  const handlePlanRoute = async (routeData) => {
    // If called from RouteForm (with address), routeData will have coords
    // If called from old form (route view), use routeForm state
    const data = routeData || routeForm;

    if (!data.start_lat || !data.start_lon || !data.end_lat || !data.end_lon) {
      toast.error('Lütfen başlangıç ve varış noktalarını belirtin')
      return
    }

    // Handle vehicle selection from both sources
    const vehicleId = data.vehicle_id || data.selected_vehicle_id;
    if (!vehicleId && !routeData) {
      toast.error('Lütfen bir araç seçin')
      return
    }

    const vehicle = vehicles.find(v => v.id === vehicleId || v.id === routeForm.selected_vehicle_id);
    if (!vehicle && !data.vehicle_range_km) {
      toast.error('Araç bulunamadı')
      return
    }

    setRoutePlanning(true)
    setRouteResult(null)

    // Show loading toast
    const loadingToast = toast.loading('Rota hesaplanıyor...')

    try {
      const result = await planRoute({
        start_lat: parseFloat(data.start_lat),
        start_lon: parseFloat(data.start_lon),
        end_lat: parseFloat(data.end_lat),
        end_lon: parseFloat(data.end_lon),
        vehicle_range_km: data.vehicle_range_km || vehicle.electric_range_km || vehicle.range_km || 300,
        battery_capacity_kwh: data.battery_capacity_kwh || vehicle.battery_capacity_kwh || 75,
        current_battery_percent: 80,
        min_charge_percent: 20,
        preferred_charge_percent: 80
      })

      console.log('Route result:', result)
      setRouteResult(result)

      // Dismiss loading and show success
      toast.dismiss(loadingToast)

      if (result.success) {
        const numStops = result.route_summary?.number_of_stops || result.charging_stops?.length || 0
        const distance = result.route_summary?.total_distance_km || 0
        toast.success(`Rota hazır! ${distance.toFixed(0)} km - ${numStops} şarj durağı`, {
          duration: 5000,
        })
        setViewMode('map')
      } else {
        toast.error('Rota hesaplanamadı: ' + (result.message || 'Bilinmeyen hata'))
      }
    } catch (error) {
      console.error('Route planning failed:', error)
      toast.dismiss(loadingToast)
      toast.error('Rota planlaması başarısız: ' + (error.message || 'Bilinmeyen hata'))
    } finally {
      setRoutePlanning(false)
    }
  }

  // Handle favorite toggle
  const handleToggleFavorite = (vehicleId) => {
    const newStatus = toggleFavorite(vehicleId)
    setFavorites(getFavorites())

    // Show toast notification
    const vehicle = vehicles.find(v => v.id === vehicleId)
    const vehicleName = vehicle ? `${vehicle.manufacturer} ${vehicle.model}` : 'Araç'

    if (newStatus) {
      toast.success(`${vehicleName} favorilere eklendi!`, {
        duration: 3000,
      })
    } else {
      toast(`${vehicleName} favorilerden çıkarıldı`, {
        icon: '♥',
        duration: 3000,
      })
    }

    return newStatus
  }

  // Get favorite vehicles
  const getFavoriteVehicles = () => {
    return vehicles.filter(v => favorites.includes(v.id))
  }

  return (
    <div className="app-container">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#333',
            padding: '16px',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />

      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <video
            src="/logo.mp4"
            className="app-logo"
            autoPlay
            loop
            muted
            playsInline
            onClick={() => {
              setViewMode('map')
              setSelectedVehicle(null)
              setSearchQuery('')
              setCurrentMessage('')
              setPowerFilter('all')
              toast.success('Ana sayfaya döndünüz')
            }}
            style={{ cursor: 'pointer' }}
          />
          <div className="status-indicators">
            <span className="status-dot green"></span>
            <span className="status-text">Backend Connected</span>
            <span className="status-dot" style={{ backgroundColor: loading ? '#ffc107' : '#28a745' }}></span>
            <span className="status-text">{vehicles.length} Vehicles</span>
          </div>
        </div>
        <div className="header-right">
          <button
            className={`favorites-btn ${showFavoritesModal ? 'active' : ''}`}
            onClick={() => setShowFavoritesModal(!showFavoritesModal)}
            title="Favorilerim"
          >
            Favoriler
            {favorites.length > 0 && (
              <span className="favorites-badge">{favorites.length}</span>
            )}
          </button>
          <button
            className={viewMode === 'map' ? 'active' : ''}
            onClick={() => setViewMode('map')}
          >
            Map
          </button>
          <button
            className={viewMode === 'list' ? 'active' : ''}
            onClick={() => setViewMode('list')}
          >
            List
          </button>
          <button
            className={viewMode === 'route' ? 'active' : ''}
            onClick={() => setViewMode('route')}
          >
            Route
          </button>
        </div>
      </header>

      <div className="app-body">
        {/* Main Content - Map/List/Route View */}
        <main className="main-content full-width">
          {viewMode === 'map' && (
            <div className="map-view-container">
              {/* Left sidebar with chat and route form */}
              <div className="map-sidebar">
                {/* AI Chat Section */}
                <div className="chat-section-compact">
                  <h4>EV Asistan</h4>
                  <div className="chat-messages-compact">
                    {chatMessages.length === 0 ? (
                      <div className="chat-welcome">
                        Merhaba! Size elektrikli araç seçiminde yardımcı olabilirim.
                      </div>
                    ) : (
                      chatMessages.map((msg, i) => (
                        <div key={i} className={`chat-msg ${msg.role}`}>
                          <strong>{msg.role === 'user' ? 'Siz' : 'Asistan'}:</strong>
                          <p>{msg.content}</p>
                        </div>
                      ))
                    )}
                  </div>
                  <div className="chat-input-compact">
                    <input
                      type="text"
                      placeholder="Soru sorun..."
                      value={currentMessage}
                      onChange={(e) => setCurrentMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    />
                    <button onClick={handleSendMessage}>Send</button>
                  </div>
                </div>

                {/* Route Planning Form */}
                <RouteForm
                  vehicles={vehicles}
                  onPlanRoute={handlePlanRoute}
                  isPlanning={routePlanning}
                />

                {/* Charging station filter */}
                <div className="station-filter-card">
                  <h4>Şarj İstasyonları</h4>
                  <select
                    value={powerFilter}
                    onChange={(e) => setPowerFilter(e.target.value)}
                    className="filter-select"
                  >
                    <option value="all">Tümü ({chargingStations.length})</option>
                    <option value="fast">Hızlı Şarj (≥50kW) ({chargingStations.filter(s => s.power_kw >= 50).length})</option>
                    <option value="normal">Normal Şarj (&lt;50kW) ({chargingStations.filter(s => s.power_kw < 50).length})</option>
                  </select>
                  {stationsLoading && <span className="loading-indicator">Yükleniyor...</span>}
                </div>
              </div>

              {/* Map */}
              <div className="map-main">
                <MapView
                  vehicles={filteredVehicles}
                  selectedVehicle={selectedVehicle}
                  chargingStations={getFilteredStations()}
                  route={routeResult}
                  onMarkerClick={(data) => {
                    if (data.type === 'vehicle') {
                      setSelectedVehicle(data.data)
                    } else if (data.type === 'station') {
                      console.log('Charging station clicked:', data.data)
                    }
                  }}
                />
                {selectedVehicle && (
                  <div className="selected-vehicle-overlay">
                    <button
                      className="close-btn"
                      onClick={() => setSelectedVehicle(null)}
                    >
                      ×
                    </button>
                    <h3>Selected Vehicle</h3>
                    <p><strong>{selectedVehicle.manufacturer || selectedVehicle.make} {selectedVehicle.model}</strong></p>
                    <p>Year: {selectedVehicle.year}</p>
                    <p>Range: {selectedVehicle.range_km}km</p>
                    <p>Battery: {selectedVehicle.battery_capacity_kwh}kWh</p>
                    <p>Price: ${selectedVehicle.price_usd?.toLocaleString()}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {viewMode === 'list' && (
            <div className="list-view">
              <h2>Vehicle Database</h2>

              {/* Arama Çubuğu */}
              <div className="vehicle-search-bar">
                <input
                  type="text"
                  placeholder="Araç ara... (marka, model, yıl)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
                {searchQuery && (
                  <button
                    className="clear-search-btn"
                    onClick={() => setSearchQuery('')}
                  >
                    ✕
                  </button>
                )}
              </div>

              <table className="vehicle-table">
                <thead>
                  <tr>
                    <th>Brand</th>
                    <th>Model</th>
                    <th>Year</th>
                    <th>Range (km)</th>
                    <th>Battery (kWh)</th>
                    <th>Price (€)</th>
                    <th>Favorite</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVehicles.map((v, i) => (
                    <tr key={i} onClick={() => setSelectedVehicle(v)}>
                      <td>{v.manufacturer || v.make}</td>
                      <td>{v.model}</td>
                      <td>{v.year}</td>
                      <td>{v.range_km}</td>
                      <td>{v.battery_capacity_kwh}</td>
                      <td>€{v.price_usd?.toLocaleString()}</td>
                      <td className="vehicle-actions">
                        <button
                          className={`fav-btn ${isFavorite(v.id) ? 'active' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleFavorite(v.id);
                          }}
                          title={isFavorite(v.id) ? "Favorilerden Çıkar" : "Favorilere Ekle"}
                        >
                          ♥
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {viewMode === 'route' && (
            <div className="route-view">
              <h2>Rota Planlama</h2>

              <div className="route-form">
                <div className="form-section">
                  <h3>Başlangıç Noktası</h3>
                  <div className="form-row">
                    <input
                      type="number"
                      step="0.000001"
                      placeholder="Enlem (Latitude)"
                      value={routeForm.start_lat}
                      onChange={(e) => setRouteForm({ ...routeForm, start_lat: e.target.value })}
                      className="route-input"
                    />
                    <input
                      type="number"
                      step="0.000001"
                      placeholder="Boylam (Longitude)"
                      value={routeForm.start_lon}
                      onChange={(e) => setRouteForm({ ...routeForm, start_lon: e.target.value })}
                      className="route-input"
                    />
                  </div>
                  <div className="quick-locations">
                    <button onClick={() => setRouteForm({ ...routeForm, start_lat: '41.0082', start_lon: '28.9784' })}>
                      İstanbul
                    </button>
                    <button onClick={() => setRouteForm({ ...routeForm, start_lat: '39.9334', start_lon: '32.8597' })}>
                      Ankara
                    </button>
                    <button onClick={() => setRouteForm({ ...routeForm, start_lat: '38.4237', start_lon: '27.1428' })}>
                      İzmir
                    </button>
                  </div>
                </div>

                <div className="form-section">
                  <h3>Varış Noktası</h3>
                  <div className="form-row">
                    <input
                      type="number"
                      step="0.000001"
                      placeholder="Enlem (Latitude)"
                      value={routeForm.end_lat}
                      onChange={(e) => setRouteForm({ ...routeForm, end_lat: e.target.value })}
                      className="route-input"
                    />
                    <input
                      type="number"
                      step="0.000001"
                      placeholder="Boylam (Longitude)"
                      value={routeForm.end_lon}
                      onChange={(e) => setRouteForm({ ...routeForm, end_lon: e.target.value })}
                      className="route-input"
                    />
                  </div>
                  <div className="quick-locations">
                    <button onClick={() => setRouteForm({ ...routeForm, end_lat: '41.0082', end_lon: '28.9784' })}>
                      İstanbul
                    </button>
                    <button onClick={() => setRouteForm({ ...routeForm, end_lat: '39.9334', end_lon: '32.8597' })}>
                      Ankara
                    </button>
                    <button onClick={() => setRouteForm({ ...routeForm, end_lat: '38.4237', end_lon: '27.1428' })}>
                      İzmir
                    </button>
                  </div>
                </div>

                <div className="form-section">
                  <h3>Araç Seçimi</h3>
                  <select
                    value={routeForm.selected_vehicle_id || ''}
                    onChange={(e) => setRouteForm({ ...routeForm, selected_vehicle_id: parseInt(e.target.value) })}
                    className="vehicle-select"
                  >
                    <option value="">Bir araç seçin...</option>
                    {vehicles.map((v, i) => (
                      <option key={v.id || i} value={v.id}>
                        {v.manufacturer || v.make} {v.model} ({v.year}) - {v.range_km}km
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  className="plan-route-btn"
                  onClick={handlePlanRoute}
                  disabled={routePlanning}
                >
                  {routePlanning ? 'Planlanıyor...' : 'Rotayı Planla'}
                </button>
              </div>

              {routeResult && (
                <div className="route-result">
                  <h3>Rota Sonuçları</h3>
                  {routeResult.success ? (
                    <>
                      <div className="route-summary">
                        <div className="summary-item">
                          <span className="label">Toplam Mesafe:</span>
                          <span className="value">{routeResult.route_summary.total_distance_km} km</span>
                        </div>
                        <div className="summary-item">
                          <span className="label">Sürüş Süresi:</span>
                          <span className="value">{routeResult.route_summary.driving_time_hours.toFixed(1)} saat</span>
                        </div>
                        <div className="summary-item">
                          <span className="label">Toplam Süre (Şarjla):</span>
                          <span className="value">{routeResult.route_summary.total_time_hours.toFixed(1)} saat</span>
                        </div>
                        <div className="summary-item">
                          <span className="label">Şarj Durakları:</span>
                          <span className="value">{routeResult.route_summary.number_of_stops}</span>
                        </div>
                        <div className="summary-item">
                          <span className="label">Toplam Şarj Süresi:</span>
                          <span className="value">{routeResult.route_summary.total_charging_time_minutes.toFixed(0)} dakika</span>
                        </div>
                        <div className="summary-item">
                          <span className="label">Tahmini Maliyet:</span>
                          <span className="value">${routeResult.route_summary.total_charging_cost_usd.toFixed(2)}</span>
                        </div>
                      </div>

                      {routeResult.charging_stops && routeResult.charging_stops.length > 0 && (
                        <div className="charging-stops-list">
                          <h4>Şarj Durakları ({routeResult.charging_stops.length})</h4>
                          {routeResult.charging_stops.map((stop, i) => (
                            <div key={i} className="stop-card">
                              <div className="stop-header">
                                <span className="stop-number">Durak {stop.segment}</span>
                                <span className="stop-name">{stop.station_name}</span>
                              </div>
                              <div className="stop-details">
                                <div className="detail-row">
                                  <span>{stop.city}</span>
                                  <span>Power: {stop.charging_power_kw}kW</span>
                                </div>
                                <div className="detail-row">
                                  <span>Varış: %{stop.battery_on_arrival.toFixed(0)}</span>
                                  <span>Ayrılış: %{stop.battery_after_charge}</span>
                                </div>
                                <div className="detail-row">
                                  <span>{stop.charging_time_minutes.toFixed(0)} dakika</span>
                                  <span>Cost: ${stop.estimated_cost.toFixed(2)}</span>
                                </div>
                                <div className="detail-row">
                                  <span>{stop.distance_from_start.toFixed(0)}km (toplam)</span>
                                  <span>{stop.distance_to_destination.toFixed(0)}km (kalan)</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      <button
                        className="view-on-map-btn"
                        onClick={() => setViewMode('map')}
                      >
                        Haritada Göster
                      </button>
                    </>
                  ) : (
                    <div className="no-route">
                      <p>{routeResult.message || 'Rota bulunamadı'}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Favorites Modal */}
      {showFavoritesModal && (
        <div className="favorites-modal-overlay" onClick={() => setShowFavoritesModal(false)}>
          <div className="favorites-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Favori Araçlarım</h2>
              <button className="close-modal-btn" onClick={() => setShowFavoritesModal(false)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              {favorites.length === 0 ? (
                <div className="empty-favorites">
                  <p>Henüz favori araç eklemediniz</p>
                  <p className="hint">Araç kartlarındaki ikon tıklayarak favorilere ekleyebilirsiniz</p>
                </div>
              ) : (
                <div className="favorites-grid">
                  {getFavoriteVehicles().map((v, i) => (
                    <div key={i} className="favorite-card">
                      <button
                        className="remove-favorite-btn"
                        onClick={() => handleToggleFavorite(v.id)}
                        title="Favorilerden çıkar"
                      >
                        ×
                      </button>
                      <div className="favorite-card-content" onClick={() => {
                        setSelectedVehicle(v)
                        setShowFavoritesModal(false)
                        setViewMode('map')
                      }}>
                        <h3>{v.manufacturer || v.make} {v.model}</h3>
                        <div className="favorite-specs">
                          <span>{v.year}</span>
                          <span>Range: {v.range_km}km</span>
                          <span>Battery: {v.battery_capacity_kwh}kWh</span>
                          <span>€{v.price_usd?.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
