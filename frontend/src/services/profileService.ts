import axios from 'axios';
import { Profile, ProfileCreate, ProfileUpdate, ProfileListResponse } from '../types/Profile';
import { API_BASE_URL } from '../config';

const API_URL = `${API_BASE_URL}/profiles/`;

/**
 * Fetch all profiles with optional search and pagination
 */
export const getProfiles = async (
  search?: string,
  page: number = 1,
  limit: number = 10
): Promise<ProfileListResponse> => {
  const skip = (page - 1) * limit;
  const params = { skip, limit, search };
  
  try {
    const response = await axios.get<ProfileListResponse>(API_URL, { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching profiles:', error);
    throw error;
  }
};

/**
 * Fetch a single profile by ID
 */
export const getProfile = async (id: string): Promise<Profile> => {
  try {
    const response = await axios.get<Profile>(`${API_URL}/${id}`);
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
    const response = await axios.post<Profile>(API_URL, profile);
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
    const response = await axios.put<Profile>(`${API_URL}/${id}`, profile);
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
    await axios.delete(`${API_URL}/${id}`);
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
    const response = await axios.post<Profile[]>(`${API_URL}/extract/${pdfId}`);
    return response.data;
  } catch (error) {
    console.error(`Error extracting profile from PDF ${pdfId}:`, error);
    throw error;
  }
}; 