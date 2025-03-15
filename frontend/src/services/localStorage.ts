/**
 * LocalStorage Service
 * Provides a robust API for working with localStorage including:
 * - Type-safe storage and retrieval
 * - Data expiration
 * - Serialization/deserialization
 * - Error handling
 */

// Define storage keys to prevent typos
export const STORAGE_KEYS = {
  UPLOADED_FILES: 'vein-diagram:uploaded-files',
  USER_PREFERENCES: 'vein-diagram:user-preferences',
  VISUALIZATION_SETTINGS: 'vein-diagram:visualization-settings',
  LAST_VIEWED_CHART: 'vein-diagram:last-viewed-chart',
  AUTH_TOKEN: 'vein-diagram:auth-token',
  RECENT_SEARCHES: 'vein-diagram:recent-searches',
};

// Interface for stored objects with expiration
interface StorageItem<T> {
  value: T;
  expiry?: number; // Optional timestamp for expiration
  version: number; // For data migration if schema changes
}

/**
 * Checks if localStorage is available
 * @returns {boolean} True if localStorage is available
 */
const isStorageAvailable = (): boolean => {
  try {
    const testKey = '__storage_test__';
    localStorage.setItem(testKey, testKey);
    localStorage.removeItem(testKey);
    return true;
  } catch (e) {
    console.warn('LocalStorage is not available:', e);
    return false;
  }
};

/**
 * Sets an item in localStorage with optional expiration
 * @param {string} key - The storage key
 * @param {T} value - The value to store
 * @param {number} [expiryHours] - Optional expiration time in hours
 * @param {number} [version=1] - Data schema version
 * @returns {boolean} Success status
 */
export const setStorageItem = <T>(
  key: string,
  value: T,
  expiryHours?: number,
  version: number = 1
): boolean => {
  if (!isStorageAvailable()) return false;

  try {
    const item: StorageItem<T> = {
      value,
      version,
    };

    // Add expiration if specified
    if (expiryHours) {
      const now = new Date();
      item.expiry = now.setHours(now.getHours() + expiryHours);
    }

    localStorage.setItem(key, JSON.stringify(item));
    return true;
  } catch (error) {
    console.error('Error saving to localStorage:', error);
    return false;
  }
};

/**
 * Gets an item from localStorage
 * @param {string} key - The storage key
 * @param {T} defaultValue - Default value if item doesn't exist
 * @returns {T} The stored value or default value
 */
export const getStorageItem = <T>(key: string, defaultValue: T): T => {
  if (!isStorageAvailable()) return defaultValue;

  try {
    const itemStr = localStorage.getItem(key);
    
    // Return default if no item found
    if (!itemStr) return defaultValue;
    
    // Parse stored JSON
    const item: StorageItem<T> = JSON.parse(itemStr);
    
    // Check if the item has expired
    if (item.expiry && new Date().getTime() > item.expiry) {
      localStorage.removeItem(key);
      return defaultValue;
    }
    
    return item.value;
  } catch (error) {
    console.error('Error retrieving from localStorage:', error);
    return defaultValue;
  }
};

/**
 * Removes an item from localStorage
 * @param {string} key - The storage key
 * @returns {boolean} Success status
 */
export const removeStorageItem = (key: string): boolean => {
  if (!isStorageAvailable()) return false;
  
  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.error('Error removing from localStorage:', error);
    return false;
  }
};

/**
 * Clears all app-specific items from localStorage
 * @returns {boolean} Success status
 */
export const clearAppStorage = (): boolean => {
  if (!isStorageAvailable()) return false;
  
  try {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    return true;
  } catch (error) {
    console.error('Error clearing localStorage:', error);
    return false;
  }
};

/**
 * Updates a specific field in a stored object
 * @param {string} key - The storage key
 * @param {Partial<T>} updates - Partial object with updates
 * @returns {boolean} Success status
 */
export const updateStorageItem = <T extends object>(
  key: string,
  updates: Partial<T>
): boolean => {
  if (!isStorageAvailable()) return false;
  
  try {
    const currentValue = getStorageItem<T>(key, {} as T);
    const updatedValue = { ...currentValue, ...updates };
    
    // Preserve the original expiry and version
    const itemStr = localStorage.getItem(key);
    if (itemStr) {
      const item: StorageItem<T> = JSON.parse(itemStr);
      return setStorageItem(key, updatedValue, 
        item.expiry ? (item.expiry - new Date().getTime()) / (1000 * 60 * 60) : undefined,
        item.version);
    }
    
    return setStorageItem(key, updatedValue);
  } catch (error) {
    console.error('Error updating localStorage item:', error);
    return false;
  }
};

// Export a default object with all methods
export default {
  setItem: setStorageItem,
  getItem: getStorageItem,
  removeItem: removeStorageItem,
  clearAppStorage,
  updateItem: updateStorageItem,
  KEYS: STORAGE_KEYS,
}; 