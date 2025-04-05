/**
 * LocalStorage Service
 * Provides a robust API for working with localStorage including:
 * - Type-safe storage and retrieval
 * - Data expiration
 * - Serialization/deserialization
 * - Error handling
 */

import { STORAGE_KEYS } from '../config';
import { UploadResponse } from '../types/pdf';

// Re-export STORAGE_KEYS from config for convenience
export { STORAGE_KEYS };

// Define storage keys to prevent typos
export const STORAGE_KEYS_LOCAL = {
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
 * Enhanced localStorage service with type safety and error handling
 */
class LocalStorageService {
  /**
   * Get an item from localStorage with type safety
   * @param key The key to retrieve
   * @param defaultValue Default value if the key doesn't exist
   * @returns The parsed item or the default value
   */
  getItem<T>(key: string, defaultValue: T): T {
    try {
      const item = localStorage.getItem(key);
      
      // Return default if item doesn't exist
      if (item === null) {
        return defaultValue;
      }
      
      // Parse the JSON data
      return JSON.parse(item) as T;
    } catch (error) {
      console.error(`Failed to get item from localStorage with key "${key}":`, error);
      return defaultValue;
    }
  }
  
  /**
   * Set an item in localStorage
   * @param key The key to set
   * @param value The value to store (will be JSON stringified)
   * @returns true if successful, false otherwise
   */
  setItem<T>(key: string, value: T): boolean {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error(`Failed to set item in localStorage with key "${key}":`, error);
      return false;
    }
  }
  
  /**
   * Remove an item from localStorage
   * @param key The key to remove
   * @returns true if successful, false otherwise
   */
  removeItem(key: string): boolean {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error(`Failed to remove item from localStorage with key "${key}":`, error);
      return false;
    }
  }
  
  /**
   * Check if localStorage is available
   * @returns true if available, false otherwise
   */
  isAvailable(): boolean {
    try {
      const testKey = '__storage_test__';
      localStorage.setItem(testKey, testKey);
      localStorage.removeItem(testKey);
      return true;
    } catch (error) {
      return false;
    }
  }
  
  /**
   * Clear all localStorage items
   * @returns true if successful, false otherwise
   */
  clear(): boolean {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
      return false;
    }
  }
}

// Create singleton instance
const storageService = new LocalStorageService();

/**
 * Get all upload history from localStorage
 * @returns Array of upload history items
 */
export const getUploadHistory = (): UploadResponse[] => {
  try {
    const history = storageService.getItem<UploadResponse[]>(STORAGE_KEYS.UPLOADED_FILES, []);
    
    // Validate that history is actually an array
    if (!Array.isArray(history)) {
      console.error('Upload history data is corrupted (not an array)');
      return [];
    }
    
    // Ensure each item has required properties
    return history.filter(item => {
      const isValid = item && typeof item === 'object' && 'fileId' in item;
      if (!isValid) {
        console.warn('Filtered out invalid upload history item:', item);
      }
      return isValid;
    });
  } catch (error) {
    console.error('Error retrieving upload history:', error);
    return [];
  }
};

/**
 * Save upload history to localStorage
 * @param history Array of upload history items to save
 * @returns true if successful, false otherwise
 */
export const saveUploadHistory = (history: UploadResponse[]): boolean => {
  return storageService.setItem(STORAGE_KEYS.UPLOADED_FILES, history);
};

/**
 * Add a single upload to history
 * @param upload The upload response to add
 * @returns true if successful, false otherwise
 */
export const addUploadToHistory = (upload: UploadResponse): boolean => {
  const history = getUploadHistory();
  // Avoid duplicates
  const filteredHistory = history.filter(item => item.fileId !== upload.fileId);
  return saveUploadHistory([upload, ...filteredHistory].slice(0, 10)); // Keep only 10 most recent
};

/**
 * Remove an upload from history by fileId
 * @param fileId The file ID to remove
 * @returns true if successful, false otherwise
 */
export const removeUploadFromHistory = (fileId: string): boolean => {
  const history = getUploadHistory();
  const updatedHistory = history.filter(item => item.fileId !== fileId);
  return saveUploadHistory(updatedHistory);
};

/**
 * Save user preference to localStorage
 * @param key Preference key
 * @param value Preference value
 * @returns true if successful, false otherwise
 */
export const saveUserPreference = <T>(key: string, value: T): boolean => {
  const preferences = storageService.getItem<Record<string, any>>(STORAGE_KEYS.USER_PREFERENCES, {}); // Add type hint
  preferences[key] = value;
  return storageService.setItem(STORAGE_KEYS.USER_PREFERENCES, preferences);
};

/**
 * Get user preference from localStorage
 * @param key Preference key
 * @param defaultValue Default value if not found
 * @returns The preference value or default value
 */
export const getUserPreference = <T>(key: string, defaultValue: T): T => {
  const preferences = storageService.getItem<Record<string, any>>(STORAGE_KEYS.USER_PREFERENCES, {}); // Add type hint
  return (key in preferences) ? preferences[key] as T : defaultValue; // Add type assertion
};

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
    Object.values(STORAGE_KEYS_LOCAL).forEach(key => {
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
  KEYS: STORAGE_KEYS_LOCAL,
};
