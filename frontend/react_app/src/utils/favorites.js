/**
 * LocalStorage utilities for managing favorite vehicles
 */

const FAVORITES_KEY = 'ev_nav_favorites'

/**
 * Get all favorite vehicle IDs from localStorage
 * @returns {number[]} Array of vehicle IDs
 */
export function getFavorites() {
  try {
    const stored = localStorage.getItem(FAVORITES_KEY)
    return stored ? JSON.parse(stored) : []
  } catch (error) {
    console.error('Error reading favorites:', error)
    return []
  }
}

/**
 * Check if a vehicle is in favorites
 * @param {number} vehicleId - Vehicle ID to check
 * @returns {boolean}
 */
export function isFavorite(vehicleId) {
  const favorites = getFavorites()
  return favorites.includes(vehicleId)
}

/**
 * Add a vehicle to favorites
 * @param {number} vehicleId - Vehicle ID to add
 * @returns {boolean} Success status
 */
export function addFavorite(vehicleId) {
  try {
    const favorites = getFavorites()
    if (!favorites.includes(vehicleId)) {
      favorites.push(vehicleId)
      localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites))
      return true
    }
    return false
  } catch (error) {
    console.error('Error adding favorite:', error)
    return false
  }
}

/**
 * Remove a vehicle from favorites
 * @param {number} vehicleId - Vehicle ID to remove
 * @returns {boolean} Success status
 */
export function removeFavorite(vehicleId) {
  try {
    const favorites = getFavorites()
    const filtered = favorites.filter(id => id !== vehicleId)
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(filtered))
    return true
  } catch (error) {
    console.error('Error removing favorite:', error)
    return false
  }
}

/**
 * Toggle favorite status of a vehicle
 * @param {number} vehicleId - Vehicle ID to toggle
 * @returns {boolean} New favorite status (true if now favorite, false if removed)
 */
export function toggleFavorite(vehicleId) {
  if (isFavorite(vehicleId)) {
    removeFavorite(vehicleId)
    return false
  } else {
    addFavorite(vehicleId)
    return true
  }
}

/**
 * Clear all favorites
 * @returns {boolean} Success status
 */
export function clearFavorites() {
  try {
    localStorage.removeItem(FAVORITES_KEY)
    return true
  } catch (error) {
    console.error('Error clearing favorites:', error)
    return false
  }
}

/**
 * Get count of favorites
 * @returns {number}
 */
export function getFavoritesCount() {
  return getFavorites().length
}
