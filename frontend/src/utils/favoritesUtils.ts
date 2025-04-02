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
  // This function might still be useful if other parts of the app use it,
  // but it's no longer used for the primary favorite storage mechanism.
  return `${FAVORITES_STORAGE_PREFIX}${profileId}`;
};

// NOTE: The following functions are removed as favorite management is now handled
// by the backend API via profileService.ts

// export const getFavoritesForProfile = (profileId: string): string[] => { ... };
// export const saveFavoritesForProfile = (profileId: string, favorites: string[]): void => { ... };
// export const addFavorite = (profileId: string, biomarkerName: string): string[] => { ... };
// export const removeFavorite = (profileId: string, biomarkerName: string): string[] => { ... };
// export const isFavorite = (profileId: string, biomarkerName: string): boolean => { ... };
