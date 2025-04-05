// axios removed - unused
import {
  Profile,
  ProfileCreate,
  ProfileUpdate, 
  ProfileListResponse,
  ProfileMatchingResponse,
  ProfileMetadata
} from '../types/Profile';
// API_BASE_URL removed - unused
import api from './api';

// API_URL removed - unused
const API_PATH = '/api/profiles'; // Use relative path with api instance

/**
 * Fetch all profiles with optional search and pagination
 */
export const getProfiles = async (
  search?: string,
  page: number = 1,
  limit: number = 10
): Promise<ProfileListResponse> => {
  const skip = (page - 1) * limit;
  // Use axios params config for cleaner query string generation
  const config = {
    params: {
      skip: skip,
      limit: limit,
      // Only include search param if it's provided and not empty
      ...(search && { search: search }) 
    }
  };
  
  try {
    // Pass the config object to axios.get
    const response = await api.get(API_PATH, config); 
    return response.data;
  } catch (error) {
    console.error('Error fetching profiles:', error);
    throw error;
  }
};

/**
 * Add a favorite biomarker to a profile
 */
export const addFavoriteBiomarker = async (profileId: string, biomarkerName: string): Promise<Profile> => {
  try {
    const response = await api.post<Profile>(`${API_PATH}/${profileId}/favorites`, {
      biomarker_name: biomarkerName,
    });
    return response.data;
  } catch (error) {
    console.error(`Error adding favorite ${biomarkerName} for profile ${profileId}:`, error);
    throw error;
  }
};

/**
 * Remove a favorite biomarker from a profile
 */
export const removeFavoriteBiomarker = async (profileId: string, biomarkerName: string): Promise<Profile> => {
  try {
    // Note: Axios delete method doesn't typically send a body, 
    // the biomarker name is part of the URL path as defined in the backend route.
    const response = await api.delete<Profile>(`${API_PATH}/${profileId}/favorites/${encodeURIComponent(biomarkerName)}`);
    return response.data;
  } catch (error) {
    console.error(`Error removing favorite ${biomarkerName} for profile ${profileId}:`, error);
    throw error;
  }
};

/**
 * Update the order of favorite biomarkers for a profile
 */
export const updateFavoriteOrder = async (profileId: string, orderedFavorites: string[]): Promise<Profile> => {
  try {
    const response = await api.put<Profile>(`${API_PATH}/${profileId}/favorites/order`, {
      ordered_favorites: orderedFavorites,
    });
    return response.data;
  } catch (error) {
    console.error(`Error updating favorite order for profile ${profileId}:`, error);
    throw error;
  }
};

/**
 * Fetch a single profile by ID
 */
export const getProfile = async (id: string): Promise<Profile> => {
  try {
    const response = await api.get<Profile>(`${API_PATH}/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching profile ${id}:`, error);
    throw error;
  }
};

/**
 * Create a new profile
 */
export const createProfile = async (profile: ProfileCreate): Promise<Profile> => {
  try {
    const response = await api.post<Profile>(API_PATH, profile);
    return response.data;
  } catch (error) {
    console.error('Error creating profile:', error);
    throw error;
  }
};

/**
 * Update an existing profile
 */
export const updateProfile = async (id: string, profile: ProfileUpdate): Promise<Profile> => {
  try {
    const response = await api.put<Profile>(`${API_PATH}/${id}`, profile);
    return response.data;
  } catch (error) {
    console.error(`Error updating profile ${id}:`, error);
    throw error;
  }
};

/**
 * Delete a profile
 */
export const deleteProfile = async (id: string): Promise<void> => {
  try {
    await api.delete(`${API_PATH}/${id}`);
  } catch (error) {
    console.error(`Error deleting profile ${id}:`, error);
    throw error;
  }
};

/**
 * Extract profile information from a PDF
 */
export const extractProfileFromPDF = async (pdfId: number): Promise<Profile[]> => {
  try {
    const response = await api.post<Profile[]>(`${API_PATH}/extract/${pdfId}`);
    return response.data;
  } catch (error) {
    console.error(`Error extracting profile from PDF ${pdfId}:`, error);
    throw error;
  }
};

/**
 * Find matching profiles for a PDF
 */
export const findMatchingProfiles = async (pdfId: string): Promise<ProfileMatchingResponse> => {
  try {
    const response = await api.post<ProfileMatchingResponse>(`${API_PATH}/match`, { pdf_id: pdfId });
    return response.data;
  } catch (error) {
    console.error(`Error finding matching profiles for PDF ${pdfId}:`, error);
    throw error;
  }
};

/**
 * Associate a PDF with a profile
 */
export const associatePdfWithProfile = async (pdfId: string, profileId: string): Promise<Profile> => {
  try {
    const response = await api.post<Profile>(`${API_PATH}/associate`, {
      pdf_id: pdfId,
      profile_id: profileId,
      create_new_profile: false
    });
    return response.data;
  } catch (error) {
    console.error(`Error associating PDF ${pdfId} with profile ${profileId}:`, error);
    throw error;
  }
};

/**
 * Create a new profile from PDF metadata
 */
export const createProfileFromPdf = async (pdfId: string, metadata: ProfileMetadata): Promise<Profile> => {
  try {
    const response = await api.post<Profile>(`${API_PATH}/associate`, {
      pdf_id: pdfId,
      create_new_profile: true,
      metadata_updates: metadata
    });
    return response.data;
  } catch (error) {
    console.error(`Error creating profile from PDF ${pdfId}:`, error);
    throw error;
  }
};

/**
 * Merge source profiles into a target profile
 */
export const mergeProfiles = async (payload: { source_profile_ids: string[]; target_profile_id: string }): Promise<{ message: string }> => {
  try {
    const response = await api.post<{ message: string }>(`${API_PATH}/merge`, payload);
    return response.data;
  } catch (error) {
    console.error(`Error merging profiles:`, error);
    throw error;
  }
};

/**
 * Generate health summary for a profile
 */
export const generateHealthSummary = async (profileId: string): Promise<Profile> => {
  try {
    const response = await api.post<Profile>(`${API_PATH}/${profileId}/generate-summary`);
    return response.data;
  } catch (error) {
    console.error(`Error generating health summary for profile ${profileId}:`, error);
    throw error;
  }
};

/**
 * Migrate all unassigned profiles to the current authenticated user
 */
export const migrateProfilesToCurrentUser = async (): Promise<{ 
  success: boolean; 
  message: string; 
  migrated_count: number;
  total_profiles: number;
}> => {
  try {
    const response = await api.post(`${API_PATH}/migrate`);
    return response.data;
  } catch (error) {
    console.error('Error migrating profiles:', error);
    throw error;
  }
};
