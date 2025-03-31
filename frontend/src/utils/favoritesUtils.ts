import {
  DEFAULT_FAVORITE_BIOMARKERS,
  FAVORITES_STORAGE_PREFIX,
  MAX_FAVORITE_BIOMARKERS,
} from '../config';

/**
 * Generates the localStorage key for a given profile ID.
 * @param profileId - The ID of the profile.
 * @returns The localStorage key string.
 */
const getFavoritesStorageKey = (profileId: string): string => {
  return `${FAVORITES_STORAGE_PREFIX}${profileId}`;
};

/**
 * Retrieves the list of favorite biomarker names for a profile from localStorage.
 * Falls back to the default list if none are found or if there's an error.
 * @param profileId - The ID of the profile.
 * @returns An array of favorite biomarker names.
 */
export const getFavoritesForProfile = (profileId: string): string[] => {
  if (!profileId) {
    console.warn('Cannot get favorites: profileId is missing.');
    return [...DEFAULT_FAVORITE_BIOMARKERS]; // Return a copy
  }
  const key = getFavoritesStorageKey(profileId);
  try {
    const storedFavorites = localStorage.getItem(key);
    if (storedFavorites) {
      const parsedFavorites = JSON.parse(storedFavorites);
      // Basic validation to ensure it's an array of strings
      if (
        Array.isArray(parsedFavorites) &&
        parsedFavorites.every((item) => typeof item === 'string')
      ) {
        return parsedFavorites;
      } else {
        console.warn(
          `Invalid favorites format found in localStorage for key ${key}. Falling back to defaults.`
        );
        // Overwrite invalid data with defaults
        localStorage.setItem(key, JSON.stringify(DEFAULT_FAVORITE_BIOMARKERS));
        return [...DEFAULT_FAVORITE_BIOMARKERS];
      }
    } else {
      // No favorites stored yet, store and return defaults
      console.log(
        `No favorites found for key ${key}. Initializing with defaults.`
      );
      localStorage.setItem(key, JSON.stringify(DEFAULT_FAVORITE_BIOMARKERS));
      return [...DEFAULT_FAVORITE_BIOMARKERS];
    }
  } catch (error) {
    console.error('Error reading favorites from localStorage:', error);
    // Fallback to defaults in case of any error
    return [...DEFAULT_FAVORITE_BIOMARKERS];
  }
};

/**
 * Saves the list of favorite biomarker names for a profile to localStorage.
 * @param profileId - The ID of the profile.
 * @param favorites - An array of favorite biomarker names.
 */
export const saveFavoritesForProfile = (
  profileId: string,
  favorites: string[]
): void => {
  if (!profileId) {
    console.warn('Cannot save favorites: profileId is missing.');
    return;
  }
  if (!Array.isArray(favorites)) {
     console.error('Cannot save favorites: Input is not an array.');
     return;
  }
   // Ensure we don't exceed the max limit when saving
  const limitedFavorites = favorites.slice(0, MAX_FAVORITE_BIOMARKERS);
  const key = getFavoritesStorageKey(profileId);
  try {
    localStorage.setItem(key, JSON.stringify(limitedFavorites));
  } catch (error) {
    console.error('Error saving favorites to localStorage:', error);
  }
};

/**
 * Adds a biomarker to the favorites list for a profile.
 * Does nothing if the biomarker is already favorited or if the max limit is reached.
 * @param profileId - The ID of the profile.
 * @param biomarkerName - The name of the biomarker to add.
 * @returns The updated list of favorites.
 */
export const addFavorite = (
  profileId: string,
  biomarkerName: string
): string[] => {
  const currentFavorites = getFavoritesForProfile(profileId);
  if (
    !currentFavorites.includes(biomarkerName) &&
    currentFavorites.length < MAX_FAVORITE_BIOMARKERS
  ) {
    const updatedFavorites = [...currentFavorites, biomarkerName];
    saveFavoritesForProfile(profileId, updatedFavorites);
    return updatedFavorites;
  }
  return currentFavorites; // Return unchanged list if already present or limit reached
};

/**
 * Removes a biomarker from the favorites list for a profile.
 * @param profileId - The ID of the profile.
 * @param biomarkerName - The name of the biomarker to remove.
 * @returns The updated list of favorites.
 */
export const removeFavorite = (
  profileId: string,
  biomarkerName: string
): string[] => {
  const currentFavorites = getFavoritesForProfile(profileId);
  const updatedFavorites = currentFavorites.filter(
    (name) => name !== biomarkerName
  );
  // Only save if the list actually changed
  if (updatedFavorites.length !== currentFavorites.length) {
    saveFavoritesForProfile(profileId, updatedFavorites);
    return updatedFavorites;
  }
  return currentFavorites; // Return unchanged list if not found
};

/**
 * Checks if a biomarker is currently favorited for a profile.
 * @param profileId - The ID of the profile.
 * @param biomarkerName - The name of the biomarker to check.
 * @returns True if the biomarker is favorited, false otherwise.
 */
export const isFavorite = (
  profileId: string,
  biomarkerName: string
): boolean => {
  const currentFavorites = getFavoritesForProfile(profileId);
  return currentFavorites.includes(biomarkerName);
};
