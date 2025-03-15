import axios from 'axios';
import { API_BASE_URL } from '../config';
import { ProcessingStatus, UploadResponse } from '../types/pdf';
import { Biomarker } from '../components/BiomarkerTable';

// Define types for API responses
export interface PDFResponse {
  file_id: string;
  filename: string;
  status: string;
  message?: string;
}

export interface PDFStatusResponse {
  file_id: string;
  filename: string;
  status: string;
  upload_date: string;
  processed_date?: string;
  error_message?: string;
}

export interface PDFListResponse {
  total: number;
  pdfs: PDFStatusResponse[];
}

export interface PDFContentResponse {
  file_id: string;
  filename: string;
  status: string;
  extracted_text?: string;
}

export interface BiomarkerData {
  name: string;
  value: number;
  unit: string;
  reference_range?: string;
  category?: string;
}

export interface ParsedPDFResponse {
  file_id: string;
  filename: string;
  date?: string;
  biomarkers: BiomarkerData[];
}

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Define response and error types
export interface ApiResponse<T> {
  data: T;
  status: number;
}

export interface ApiError {
  message: string;
  status: number;
}

// Upload a PDF file
export const uploadPDF = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/pdf/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// Get PDF processing status
export const getPDFStatus = async (fileId: string): Promise<ProcessingStatus> => {
  const response = await api.get(`/api/pdf/${fileId}/status`);
  return response.data;
};

// Get biomarkers for a specific PDF
export const getBiomarkersByFileId = async (fileId: string): Promise<Biomarker[]> => {
  const response = await api.get(`/api/pdf/${fileId}/biomarkers`);
  return response.data;
};

// Get all biomarkers with optional filtering
export const getAllBiomarkers = async (params?: {
  category?: string;
  limit?: number;
  offset?: number;
}): Promise<Biomarker[]> => {
  const response = await api.get('/api/biomarkers', { params });
  return response.data;
};

// Get all unique biomarker categories
export const getBiomarkerCategories = async (): Promise<string[]> => {
  const response = await api.get('/api/biomarkers/categories');
  return response.data;
};

// Search for biomarkers by name
export const searchBiomarkers = async (query: string, limit = 100): Promise<Biomarker[]> => {
  const response = await api.get('/api/biomarkers/search', {
    params: { query, limit },
  });
  return response.data;
};

// Get a specific biomarker by ID
export const getBiomarkerById = async (biomarkerId: number): Promise<Biomarker> => {
  const response = await api.get(`/api/biomarkers/${biomarkerId}`);
  return response.data;
};

// PDF upload service
export const pdfService = {
  /**
   * Upload a PDF file to the server
   * @param file The PDF file to upload
   * @returns Promise with the response data
   */
  uploadPdf: async (file: File): Promise<ApiResponse<PDFResponse>> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post<PDFResponse>('/pdf/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data.detail || 'Error uploading PDF',
          status: error.response.status,
        };
      }
      throw {
        message: 'Network error',
        status: 500,
      };
    }
  },
  
  /**
   * Get the status of a PDF file
   * @param fileId The ID of the file to check
   * @returns Promise with the response data
   */
  getPdfStatus: async (fileId: string): Promise<ApiResponse<PDFStatusResponse>> => {
    try {
      const response = await api.get<PDFStatusResponse>(`/pdf/status/${fileId}`);
      
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data.detail || 'Error getting PDF status',
          status: error.response.status,
        };
      }
      throw {
        message: 'Network error',
        status: 500,
      };
    }
  },

  /**
   * List all PDF files
   * @param skip Number of records to skip (for pagination)
   * @param limit Number of records to return (for pagination)
   * @returns Promise with the response data
   */
  listPdfs: async (skip = 0, limit = 10): Promise<ApiResponse<PDFListResponse>> => {
    try {
      const response = await api.get<PDFListResponse>(`/pdf/list?skip=${skip}&limit=${limit}`);
      
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data.detail || 'Error listing PDFs',
          status: error.response.status,
        };
      }
      throw {
        message: 'Network error',
        status: 500,
      };
    }
  },

  /**
   * Delete a PDF file
   * @param fileId The ID of the file to delete
   * @returns Promise with the response data
   */
  deletePdf: async (fileId: string): Promise<ApiResponse<{ message: string }>> => {
    try {
      const response = await api.delete<{ message: string }>(`/pdf/${fileId}`);
      
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data.detail || 'Error deleting PDF',
          status: error.response.status,
        };
      }
      throw {
        message: 'Network error',
        status: 500,
      };
    }
  },
};

export default api; 