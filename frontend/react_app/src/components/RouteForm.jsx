import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { getCurrentPosition, GeolocationError, formatAccuracy } from '../utils/geolocation';
import './RouteForm.css';

const RouteForm = ({ vehicles, onPlanRoute, isPlanning }) => {
  const [startAddress, setStartAddress] = useState('');
  const [endAddress, setEndAddress] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [error, setError] = useState('');
  const [vehicleSearchQuery, setVehicleSearchQuery] = useState('');
  const [showVehicleDropdown, setShowVehicleDropdown] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowVehicleDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Get user's current location
  const handleUseMyLocation = async () => {
    setLoadingLocation(true);
    setError('Konumunuz alınıyor...');

    try {
      const position = await getCurrentPosition();

      // Store user location
      setUserLocation(position);

      // Reverse geocode to get address name
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.lat}&lon=${position.lon}&zoom=18&addressdetails=1`
        );
        const data = await response.json();

        const locationName = data.display_name || `${position.lat.toFixed(4)}, ${position.lon.toFixed(4)}`;
        setStartAddress(locationName);

        toast.success(
          `Konumunuz tespit edildi! ${formatAccuracy(position.accuracy)}`,
          { duration: 4000 }
        );
        setError('');
      } catch (geocodeError) {
        console.error('Reverse geocoding error:', geocodeError);
        // Even if reverse geocoding fails, use coordinates
        setStartAddress(`${position.lat.toFixed(6)}, ${position.lon.toFixed(6)}`);
        toast.success('Konumunuz tespit edildi!', { duration: 3000 });
        setError('');
      }
    } catch (err) {
      console.error('Geolocation error:', err);

      switch (err.type) {
        case GeolocationError.PERMISSION_DENIED:
          toast.error('Konum izni reddedildi', { duration: 5000 });
          setError('Konum izni reddedildi. Tarayıcı ayarlarından konum iznini açabilirsiniz.');
          break;
        case GeolocationError.POSITION_UNAVAILABLE:
          toast.error('Konum servisi kullanılamıyor', { duration: 4000 });
          setError('Konum bilgisi alınamadı. Lütfen GPS/konum servislerinizi kontrol edin.');
          break;
        case GeolocationError.TIMEOUT:
          toast.error('Konum tespiti zaman aşımına uğradı', { duration: 4000 });
          setError('Konum tespiti zaman aşımına uğradı. Lütfen tekrar deneyin.');
          break;
        case GeolocationError.NOT_SUPPORTED:
          toast.error('Tarayıcınız konum servislerini desteklemiyor', { duration: 5000 });
          setError('Tarayıcınız konum servislerini desteklemiyor.');
          break;
        default:
          toast.error('Konum alınamadı', { duration: 4000 });
          setError(err.message || 'Konum alınamadı. Lütfen manuel olarak adres girin.');
      }
    } finally {
      setLoadingLocation(false);
    }
  };

  // Geocoding function using Nominatim (OpenStreetMap)
  const geocodeAddress = async (address) => {
    try {
      // Add Turkey bias for better results
      const query = address.includes('Türkiye') || address.includes('Turkey')
        ? address
        : `${address}, Türkiye`;

      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=tr`
      );
      const data = await response.json();

      if (data && data.length > 0) {
        console.log('Geocoding sonuçları:', data);
        return {
          lat: parseFloat(data[0].lat),
          lon: parseFloat(data[0].lon),
          display_name: data[0].display_name
        };
      }
      return null;
    } catch (err) {
      console.error('Geocoding error:', err);
      return null;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!startAddress || !endAddress) {
      setError('Lütfen başlangıç ve varış adreslerini girin');
      return;
    }

    if (!selectedVehicleId) {
      setError('Lütfen bir araç seçin');
      return;
    }

    // Find selected vehicle
    const vehicle = vehicles.find(v => v.id === parseInt(selectedVehicleId));
    if (!vehicle) {
      setError('Seçilen araç bulunamadı');
      return;
    }

    // Geocode addresses
    setError('Başlangıç adresi aranıyor...');
    const startCoords = await geocodeAddress(startAddress);
    if (!startCoords) {
      setError(`"${startAddress}" adresi bulunamadı. Örnek: "Taksim, İstanbul" veya "Ankara" şeklinde deneyin.`);
      return;
    }

    setError('Varış adresi aranıyor...');
    const endCoords = await geocodeAddress(endAddress);
    if (!endCoords) {
      setError(`"${endAddress}" adresi bulunamadı. Örnek: "Erzurum" veya "Dadaşkent, Erzurum" şeklinde deneyin.`);
      return;
    }

    console.log('Adresler bulundu:', {
      start: startCoords.display_name,
      end: endCoords.display_name
    });

    setError('Rota hesaplanıyor...');

    // Call route planning
    onPlanRoute({
      start_lat: startCoords.lat,
      start_lon: startCoords.lon,
      end_lat: endCoords.lat,
      end_lon: endCoords.lon,
      vehicle_range_km: vehicle.range_km,
      battery_capacity_kwh: vehicle.battery_capacity_kwh,
      vehicle_id: vehicle.id,
      startAddress: startCoords.display_name,
      endAddress: endCoords.display_name
    });
  };

  const quickAddresses = {
    istanbul: 'İstanbul, Türkiye',
    ankara: 'Ankara, Türkiye',
    izmir: 'İzmir, Türkiye',
    antalya: 'Antalya, Türkiye',
    bursa: 'Bursa, Türkiye'
  };

  return (
    <div className="route-form-container">
      <h3>Rota Planlama</h3>

      <form onSubmit={handleSubmit} className="route-form">
        {/* Start Address */}
        <div className="form-group">
          <label htmlFor="start-address">Başlangıç Adresi</label>
          <div className="address-input-group">
            <input
              id="start-address"
              type="text"
              value={startAddress}
              onChange={(e) => setStartAddress(e.target.value)}
              placeholder="Örn: Taksim, İstanbul"
              className="address-input"
            />
            <button
              type="button"
              onClick={handleUseMyLocation}
              disabled={loadingLocation}
              className={`location-button ${loadingLocation ? 'loading' : ''}`}
              title="Mevcut konumumu kullan"
            >
              {loadingLocation ? '⏳' : '📍'}
            </button>
          </div>
        </div>

        {/* End Address */}
        <div className="form-group">
          <label htmlFor="end-address">Varış Adresi</label>
          <input
            id="end-address"
            type="text"
            value={endAddress}
            onChange={(e) => setEndAddress(e.target.value)}
            placeholder="Örn: Kızılay, Ankara"
            className="address-input"
          />
          <div className="quick-buttons">
            {Object.entries(quickAddresses).map(([key, value]) => (
              <button
                key={key}
                type="button"
                onClick={() => setEndAddress(value)}
                className="quick-btn"
              >
                {value.split(',')[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Vehicle Selection with Search */}
        <div className="form-group">
          <label htmlFor="vehicle-search">Araç Seçimi</label>
          <div className="vehicle-search-container" ref={dropdownRef}>
            <input
              id="vehicle-search"
              type="text"
              value={vehicleSearchQuery}
              onChange={(e) => {
                setVehicleSearchQuery(e.target.value);
                setShowVehicleDropdown(true);
              }}
              onFocus={() => setShowVehicleDropdown(true)}
              placeholder="Araç ara... (marka, model)"
              className="address-input"
            />
            {showVehicleDropdown && (
              <div className="vehicle-dropdown">{vehicles
                .filter(v => {
                  const query = vehicleSearchQuery.toLowerCase();
                  return (
                    (v.manufacturer || '').toLowerCase().includes(query) ||
                    (v.model || '').toLowerCase().includes(query) ||
                    (v.year || '').toString().includes(query)
                  );
                })
                .slice(0, 10)
                .map((v) => (
                  <div
                    key={v.id}
                    className={`vehicle-dropdown-item ${selectedVehicleId === v.id.toString() ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedVehicleId(v.id.toString());
                      setVehicleSearchQuery(`${v.manufacturer} ${v.model} (${v.range_km}km)`);
                      setShowVehicleDropdown(false);
                    }}
                  >
                    <div className="vehicle-dropdown-name">
                      {v.manufacturer} {v.model} ({v.year})
                    </div>
                    <div className="vehicle-dropdown-specs">
                      {v.range_km}km | {v.battery_capacity_kwh}kWh
                    </div>
                  </div>
                ))}
                {vehicleSearchQuery && vehicles.filter(v => {
                  const query = vehicleSearchQuery.toLowerCase();
                  return (
                    (v.manufacturer || '').toLowerCase().includes(query) ||
                    (v.model || '').toLowerCase().includes(query)
                  );
                }).length === 0 && (
                    <div className="vehicle-dropdown-empty">
                      Araç bulunamadı
                    </div>
                  )}
              </div>
            )}
          </div>
        </div>

        {/* Error Message */}
        {
          error && (
            <div className={`message ${error.includes('...') ? 'info' : 'error'}`}>
              {error}
            </div>
          )
        }

        {/* Submit Button */}
        <button
          type="submit"
          className="plan-route-btn"
          disabled={isPlanning}
        >
          {isPlanning ? 'Hesaplanıyor...' : 'Rota Hesapla'}
        </button>
      </form >

      <div className="route-info">
        <p><strong>İpucu:</strong> Şehir adı, semt veya tam adres girebilirsiniz.</p>
        <p>Örnek: "Taksim, İstanbul" veya "Kızılay, Ankara"</p>
      </div>
    </div >
  );
};

export default RouteForm;
