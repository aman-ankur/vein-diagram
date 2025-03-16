import axios from 'axios';
import { API_BASE_URL } from '../config';
import { Profile } from '../types/Profile';

const API_URL = `${API_BASE_URL}/pdf`;

/**
 * Upload a PDF file with optional profile ID
 */
export const uploadPDF = async (file: File, profileId?: string): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  
  if (profileId) {
    formData.append('profile_id', profileId);
  }
  
  try {
    const response = await axios.post(`${API_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading PDF:', error);
    throw error;
  }
};

/**
 * Get the status of a PDF file
 */
export const getPDFStatus = async (fileId: string): Promise<any> => {
  try {
    const response = await axios.get(`${API_URL}/status/${fileId}`);
    return response.data;
  } catch (error) {
    console.error(`Error getting PDF status for ${fileId}:`, error);
    throw error;
  }
};

/**
 * Get a list of all PDFs
 */
export const getAllPDFs = async (): Promise<any> => {
  try {
    const response = await axios.get(`${API_URL}/list`);
    return response.data;
  } catch (error) {
    console.error('Error getting PDF list:', error);
    throw error;
  }
};

/**
 * Delete a PDF file
 */
export const deletePDF = async (fileId: string): Promise<any> => {
  try {
    const response = await axios.delete(`${API_URL}/${fileId}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting PDF ${fileId}:`, error);
    throw error;
  }
};

/**
 * Extract profile information from a PDF
 */
export const extractProfileFromPDF = async (pdfId: number): Promise<Profile[]> => {
  try {
    const response = await axios.post<Profile[]>(`${API_BASE_URL}/profiles/extract/${pdfId}`);
    return response.data;
  } catch (error) {
    console.error(`Error extracting profile from PDF ${pdfId}:`, error);
    throw error;
  }
};

/**
 * Assign a PDF to a profile
 */
export const assignPDFToProfile = async (fileId: string, profileId: string): Promise<any> => {
  try {
    const response = await axios.put(`${API_URL}/${fileId}/profile`, { profile_id: profileId });
    return response.data;
  } catch (error) {
    console.error(`Error assigning PDF ${fileId} to profile ${profileId}:`, error);
    throw error;
  }
}; 