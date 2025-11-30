/**
 * Geolocation Utility Module
 * Provides browser geolocation functionality with error handling
 */

// Error types for better error handling
export const GeolocationError = {
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  POSITION_UNAVAILABLE: 'POSITION_UNAVAILABLE',
  TIMEOUT: 'TIMEOUT',
  NOT_SUPPORTED: 'NOT_SUPPORTED'
};

/**
 * Get user's current position
 * @param {Object} options - Geolocation options
 * @returns {Promise<{lat: number, lon: number, accuracy: number}>}
 */
export const getCurrentPosition = (options = {}) => {
  return new Promise((resolve, reject) => {
    // Check if geolocation is supported
    if (!navigator.geolocation) {
      reject({
        type: GeolocationError.NOT_SUPPORTED,
        message: 'Tarayıcınız konum servislerini desteklemiyor'
      });
      return;
    }

    const defaultOptions = {
      enableHighAccuracy: true,
      timeout: 10000, // 10 seconds
      maximumAge: 0 // Don't use cached position
    };

    const geoOptions = { ...defaultOptions, ...options };

    navigator.geolocation.getCurrentPosition(
      // Success callback
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        });
      },
      // Error callback
      (error) => {
        let errorType;
        let errorMessage;

        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorType = GeolocationError.PERMISSION_DENIED;
            errorMessage = 'Konum izni reddedildi. Lütfen tarayıcı ayarlarından konum iznini açın.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorType = GeolocationError.POSITION_UNAVAILABLE;
            errorMessage = 'Konum bilgisi alınamadı. Lütfen GPS/konum servislerinizi kontrol edin.';
            break;
          case error.TIMEOUT:
            errorType = GeolocationError.TIMEOUT;
            errorMessage = 'Konum tespiti zaman aşımına uğradı. Lütfen tekrar deneyin.';
            break;
          default:
            errorType = GeolocationError.POSITION_UNAVAILABLE;
            errorMessage = 'Bilinmeyen bir hata oluştu.';
        }

        reject({
          type: errorType,
          message: errorMessage,
          code: error.code
        });
      },
      geoOptions
    );
  });
};

/**
 * Watch user's position for continuous tracking
 * @param {Function} callback - Called when position updates
 * @param {Function} errorCallback - Called on error
 * @param {Object} options - Geolocation options
 * @returns {number} - Watch ID to use for clearWatch
 */
export const watchPosition = (callback, errorCallback, options = {}) => {
  if (!navigator.geolocation) {
    errorCallback({
      type: GeolocationError.NOT_SUPPORTED,
      message: 'Tarayıcınız konum servislerini desteklemiyor'
    });
    return null;
  }

  const defaultOptions = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 5000 // Accept 5 second old position
  };

  const geoOptions = { ...defaultOptions, ...options };

  const watchId = navigator.geolocation.watchPosition(
    (position) => {
      callback({
        lat: position.coords.latitude,
        lon: position.coords.longitude,
        accuracy: position.coords.accuracy,
        timestamp: position.timestamp
      });
    },
    (error) => {
      let errorType;
      let errorMessage;

      switch (error.code) {
        case error.PERMISSION_DENIED:
          errorType = GeolocationError.PERMISSION_DENIED;
          errorMessage = 'Konum izni reddedildi';
          break;
        case error.POSITION_UNAVAILABLE:
          errorType = GeolocationError.POSITION_UNAVAILABLE;
          errorMessage = 'Konum bilgisi alınamadı';
          break;
        case error.TIMEOUT:
          errorType = GeolocationError.TIMEOUT;
          errorMessage = 'Konum tespiti zaman aşımına uğradı';
          break;
        default:
          errorType = GeolocationError.POSITION_UNAVAILABLE;
          errorMessage = 'Bilinmeyen bir hata oluştu';
      }

      errorCallback({
        type: errorType,
        message: errorMessage,
        code: error.code
      });
    },
    geoOptions
  );

  return watchId;
};

/**
 * Stop watching position
 * @param {number} watchId - Watch ID from watchPosition
 */
export const clearWatch = (watchId) => {
  if (navigator.geolocation && watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
  }
};

/**
 * Check if geolocation is supported
 * @returns {boolean}
 */
export const isGeolocationSupported = () => {
  return 'geolocation' in navigator;
};

/**
 * Get accuracy in human-readable format
 * @param {number} accuracy - Accuracy in meters
 * @returns {string}
 */
export const formatAccuracy = (accuracy) => {
  if (accuracy < 50) {
    return 'Çok iyi (~' + Math.round(accuracy) + 'm)';
  } else if (accuracy < 100) {
    return 'İyi (~' + Math.round(accuracy) + 'm)';
  } else if (accuracy < 500) {
    return 'Orta (~' + Math.round(accuracy) + 'm)';
  } else {
    return 'Düşük (~' + Math.round(accuracy) + 'm)';
  }
};
