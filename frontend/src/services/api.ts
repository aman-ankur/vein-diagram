import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { API_BASE_URL } from '../config';
import { Biomarker } from '../types/pdf';
import { BiomarkerExplanation, ApiError, FileMetadata, UserProfile, ProcessingStatus } from '../types/api';

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

// Create axios instance with enhanced configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: true // Set to true to send cookies with requests
});

// Add request interceptor for logging and enhancement
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config);
    
    // Add timestamp to prevent caching issues
    const url = config.url || '';
    config.url = url.includes('?') 
      ? `${url}&_t=${Date.now()}` 
      : `${url}?_t=${Date.now()}`;
    
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.data);
    return response;
  },
  async (error: AxiosError) => {
    console.error('API Response Error:', error);
    
    // Create standardized error object
    const apiError: ApiError = {
      message: error.message || 'Unknown error occurred',
      status: error.response?.status || 500,
      data: error.response?.data || null,
      isNetworkError: !error.response && error.message?.includes('Network Error')
    };
    
    // Check if it's a network error that might benefit from a retry
    if (apiError.isNetworkError) {
      console.log('Network error detected, may retry');
    }
    
    return Promise.reject(apiError);
  }
);

// Define response and error types
export interface ApiResponse<T> {
  data: T;
  status: number;
}

// Define retry parameters
const DEFAULT_RETRY_COUNT = 3;
const DEFAULT_RETRY_DELAY = 1000; // 1 second

// Utility to check if the device is offline
const isOffline = (): boolean => {
  return typeof navigator !== 'undefined' && !navigator.onLine;
};

// Enhanced retry function with better error handling and offline detection
const withRetry = async <T>(
  apiCall: () => Promise<T>, 
  retries = 3, 
  delay = 1000,
  exponentialBackoff = true
): Promise<T> => {
  let lastError: any;
  let retryCount = 0;
  
  // Check for offline status immediately
  if (isOffline()) {
    const offlineError: ApiError = {
      message: 'You are currently offline. Please check your internet connection.',
      status: 0,
      isNetworkError: true,
      isOffline: true
    };
    throw offlineError;
  }

  while (retryCount <= retries) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error;
      
      // Check if device went offline during retry attempt
      if (isOffline()) {
        const offlineError: ApiError = {
          message: 'You are currently offline. Please check your internet connection.',
          status: 0,
          isNetworkError: true,
          isOffline: true
        };
        throw offlineError;
      }
      
      // Create standardized error object
      const apiError: ApiError = {
        message: axios.isAxiosError(error) ? error.message : 'Unknown error occurred',
        status: axios.isAxiosError(error) && error.response ? error.response.status : 500,
        data: axios.isAxiosError(error) && error.response ? error.response.data : null,
        isNetworkError: axios.isAxiosError(error) && !error.response && error.message?.includes('Network Error')
      };
      
      // Only retry on network errors or 5xx server errors
      const shouldRetry = apiError.isNetworkError || (apiError.status >= 500 && apiError.status < 600);
      
      if (!shouldRetry || retryCount >= retries) {
        throw apiError;
      }
      
      console.log('Network error detected, may retry');
      
      // Calculate delay with exponential backoff if enabled
      const retryDelay = exponentialBackoff ? delay * Math.pow(1.5, retryCount) : delay;
      
      console.log(`Retrying API call, ${retries - retryCount} attempts left. Waiting ${retryDelay}ms...`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
      retryCount++;
    }
  }
  
  // If we exhaust all retries
  throw lastError;
};

// Upload a PDF file with retry
export const uploadPDF = async (file: File): Promise<UploadResponse> => {
  return withRetry(async () => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await api.post('/api/pdf/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 100));
          console.log(`Upload progress: ${percentCompleted}%`);
        },
      });
      
      console.log('Raw backend response:', response.data);
      
      // Map snake_case to camelCase if needed
      return {
        fileId: response.data.file_id,
        filename: response.data.filename,
        status: response.data.status,
        message: response.data.message,
        timestamp: new Date().toISOString(), // Backend might not provide this
        fileSize: file.size,
        mimeType: file.type,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          throw {
            message: error.response.data?.detail || error.response.data?.message || 'Error uploading PDF',
            status: error.response.status,
          };
        } else {
          throw {
            message: 'Network error during upload. Please check your connection and try again.',
            status: 0,
            isNetworkError: true
          };
        }
      }
      throw error;
    }
  }, 2);
};

// Get PDF processing status with retry
export const getPDFStatus = async (fileId: string): Promise<ProcessingStatus> => {
  if (!fileId || fileId === 'undefined') {
    throw new Error('Invalid fileId provided to getPDFStatus');
  }
  
  return withRetry(async () => {
    try {
      const response = await api.get(`/api/pdf/status/${fileId}`);
      console.log('Raw status response:', response.data);
      
      // Map snake_case to camelCase
      return {
        fileId: response.data.file_id,
        filename: response.data.filename,
        status: response.data.status,
        uploadTimestamp: response.data.upload_date,
        completedTimestamp: response.data.processed_date,
        error: response.data.error_message,
        labName: response.data.lab_name,
        patientName: response.data.patient_name,
        patientId: response.data.patient_id,
        patientAge: response.data.patient_age,
        patientGender: response.data.patient_gender,
        reportDate: response.data.report_date,
        parsingConfidence: response.data.parsing_confidence
      };
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data?.detail || error.response.data?.message || 'Error getting PDF status',
          status: error.response.status,
        };
      }
      throw error;
    }
  });
};

// Get biomarkers for a specific PDF with retry
export const getBiomarkersByFileId = async (fileId: string): Promise<Biomarker[]> => {
  if (!fileId || fileId === 'undefined') {
    throw new Error('Invalid fileId provided to getBiomarkersByFileId');
  }
  
  return withRetry(async () => {
    try {
      // Use the correct API endpoint format: /api/pdf/{fileId}/biomarkers
      const response = await api.get(`/api/pdf/${fileId}/biomarkers`);
      
      // Map the backend response to the frontend Biomarker model
      return response.data.map((item: any) => ({
        id: item.id,
        name: item.name,
        value: item.value,
        unit: item.unit || '',
        referenceRange: item.reference_range_text || 
                       (item.reference_range_low !== null && item.reference_range_high !== null ? 
                        `${item.reference_range_low}-${item.reference_range_high}` : undefined),
        category: item.category || 'Other',
        isAbnormal: item.is_abnormal || false,
        fileId,
        date: new Date().toISOString() // Use current date as fallback
      }));
    } catch (error) {
      console.error(`Failed to get biomarkers for file ${fileId}:`, error);
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data?.detail || error.response.data?.message || `Error getting biomarkers for file ${fileId}`,
          status: error.response.status,
        };
      }
      throw error;
    }
  });
};

// Get all biomarkers with optional filtering and retry
export const getAllBiomarkers = async (params?: {
  category?: string;
  limit?: number;
  offset?: number;
}): Promise<Biomarker[]> => {
  return withRetry(async () => {
    try {
      const response = await api.get('/api/biomarkers', { params });
      
      // Map the backend response to the frontend Biomarker model
      return response.data.map((item: any) => ({
        id: item.id,
        name: item.name,
        value: item.value,
        unit: item.unit || '',
        referenceRange: item.reference_range_text || 
                       (item.reference_range_low !== null && item.reference_range_high !== null ? 
                        `${item.reference_range_low}-${item.reference_range_high}` : undefined),
        category: item.category || 'Other',
        isAbnormal: item.is_abnormal || false,
        fileId: item.pdf ? item.pdf.file_id : undefined,
        date: new Date().toISOString() // Use current date as fallback
      }));
    } catch (error) {
      console.error('Failed to get all biomarkers:', error);
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data?.detail || error.response.data?.message || 'Error getting biomarkers',
          status: error.response.status,
        };
      }
      throw error;
    }
  });
};

// Get all unique biomarker categories with retry
export const getBiomarkerCategories = async (): Promise<string[]> => {
  return withRetry(async () => {
    try {
      const response = await api.get('/api/biomarkers/categories');
      return response.data;
    } catch (error) {
      console.error('Failed to get biomarker categories:', error);
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data?.detail || error.response.data?.message || 'Error getting biomarker categories',
          status: error.response.status,
        };
      }
      throw error;
    }
  });
};

// Search for biomarkers by name with retry
export const searchBiomarkers = async (query: string, limit = 100): Promise<Biomarker[]> => {
  return withRetry(async () => {
    try {
      const response = await api.get('/api/biomarkers/search', {
        params: { query, limit },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to search biomarkers:', error);
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data?.detail || error.response.data?.message || 'Error searching biomarkers',
          status: error.response.status,
        };
      }
      throw error;
    }
  });
};

// Get a specific biomarker by ID with retry
export const getBiomarkerById = async (biomarkerId: number): Promise<Biomarker> => {
  return withRetry(async () => {
    try {
      const response = await api.get(`/api/biomarkers/${biomarkerId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to get biomarker ${biomarkerId}:`, error);
      if (axios.isAxiosError(error) && error.response) {
        throw {
          message: error.response.data?.detail || error.response.data?.message || `Error getting biomarker ${biomarkerId}`,
          status: error.response.status,
        };
      }
      throw error;
    }
  });
};

/**
 * Get an AI-generated explanation for a biomarker
 */
export const getBiomarkerExplanation = async (
  biomarkerId?: string | number,
  biomarkerName?: string,
  value?: number | string,
  unit?: string,
  referenceRange?: string,
  isAbnormal?: boolean
): Promise<BiomarkerExplanation> => {
  console.log('==== API REQUEST: getBiomarkerExplanation ====');
  console.log('Parameters:', { biomarkerId, biomarkerName, value, unit, referenceRange, isAbnormal });
  
  try {
    let response;
    
    // Check if we have a valid biomarkerId
    if (biomarkerId) {
      console.log(`Making API call to /api/biomarkers/${biomarkerId}/explain`);
      try {
        response = await axios.post(`/api/biomarkers/${biomarkerId}/explain`, {
          name: biomarkerName,
          value,
          unit,
          reference_range: referenceRange,
          is_abnormal: isAbnormal
        });
        console.log('API response status:', response.status);
        console.log('API response data:', response.data);
      } catch (error) {
        // Handle 404 errors specifically
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          console.warn(`Biomarker ID ${biomarkerId} not found, falling back to generic endpoint`);
          // Fall back to the generic endpoint
          throw new Error(`Biomarker ID ${biomarkerId} not found`);
        } else {
          // For other errors, just rethrow
          console.error('Error in specific biomarker endpoint:', error);
          throw error;
        }
      }
    } 
    
    // If we don't have a biomarkerId or the specific endpoint failed with 404,
    // use the generic endpoint
    if (!biomarkerId || !response) {
      console.log('Making API call to generic /api/biomarkers/explain endpoint');
      response = await axios.post('/api/biomarkers/explain', {
        name: biomarkerName,
        value,
        unit,
        reference_range: referenceRange,
        is_abnormal: isAbnormal
      });
      console.log('Generic API response status:', response.status);
      console.log('Generic API response data:', response.data);
    }

    if (response.status !== 200) {
      console.error('Non-200 response:', response.status, response.data);
      throw new Error(`Failed to get explanation: ${response.statusText}`);
    }

    return response.data;
  } catch (error) {
    console.error('==== ERROR IN getBiomarkerExplanation ====');
    
    if (axios.isAxiosError(error)) {
      console.error('Axios error details:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          headers: error.config?.headers,
          data: error.config?.data
        }
      });
      
      // Provide more specific error messages based on status code
      if (error.response?.status === 404) {
        throw new Error('The API endpoint for biomarker explanations was not found. Please check your server configuration.');
      } else if (error.response?.status === 500) {
        throw new Error('The server encountered an error while generating the explanation. Please try again later.');
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('The request timed out. Please check your internet connection and try again.');
      } else if (!error.response && error.request) {
        // The request was made but no response was received
        throw new Error('No response received from server. Please check your internet connection.');
      }
    }
    
    // Re-throw the error to be handled by the caller
    throw error;
  }
};

// PDF upload service
export const pdfService = {
  /**
   * Upload a PDF file to the server
   * @param file The PDF file to upload
   * @returns Promise with the response data
   */
  uploadPdf: async (file: File): Promise<ApiResponse<PDFResponse>> => {
    return withRetry(async () => {
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await api.post<PDFResponse>('/api/pdf/upload', formData, {
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
            message: error.response.data?.detail || 'Error uploading PDF',
            status: error.response.status,
          };
        }
        throw {
          message: 'Network error during upload',
          status: 0,
          isNetworkError: true
        };
      }
    });
  },
  
  /**
   * Get the status of a PDF file
   * @param fileId The ID of the file to check
   * @returns Promise with the response data
   */
  getPdfStatus: async (fileId: string): Promise<ApiResponse<PDFStatusResponse>> => {
    return withRetry(async () => {
      try {
        const response = await api.get<PDFStatusResponse>(`/api/pdf/status/${fileId}`);
        
        return {
          data: response.data,
          status: response.status,
        };
      } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
          throw {
            message: error.response.data?.detail || 'Error getting PDF status',
            status: error.response.status,
          };
        }
        throw {
          message: 'Network error checking PDF status',
          status: 0,
          isNetworkError: true
        };
      }
    });
  },

  /**
   * List all PDF files
   * @param skip Number of records to skip (for pagination)
   * @param limit Number of records to return (for pagination)
   * @returns Promise with the response data
   */
  listPdfs: async (skip = 0, limit = 10): Promise<ApiResponse<PDFListResponse>> => {
    return withRetry(async () => {
      try {
        const response = await api.get<PDFListResponse>(`/api/pdf/list?skip=${skip}&limit=${limit}`);
        
        return {
          data: response.data,
          status: response.status,
        };
      } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
          throw {
            message: error.response.data?.detail || 'Error listing PDFs',
            status: error.response.status,
          };
        }
        throw {
          message: 'Network error listing PDFs',
          status: 0,
          isNetworkError: true
        };
      }
    });
  },

  /**
   * Delete a PDF file
   * @param fileId The ID of the file to delete
   * @returns Promise with the response data
   */
  deletePdf: async (fileId: string): Promise<ApiResponse<{ message: string }>> => {
    return withRetry(async () => {
      try {
        const response = await api.delete<{ message: string }>(`/api/pdf/${fileId}`);
        
        return {
          data: response.data,
          status: response.status,
        };
      } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
          throw {
            message: error.response.data?.detail || 'Error deleting PDF',
            status: error.response.status,
          };
        }
        throw {
          message: 'Network error deleting PDF',
          status: 0,
          isNetworkError: true
        };
      }
    });
  },
};

// Function to check if the API is available
export const checkApiAvailability = async (): Promise<boolean> => {
  try {
    // Make a simple GET request to check if the API is available
    // Use a short timeout for quick response
    await axios.get(`${API_BASE_URL}/health`, { 
      timeout: 5000,
      headers: {
        'Cache-Control': 'no-cache',
        'Accept': 'application/json',
      },
      // Don't consider CORS errors as true errors in this context - we just want to know if server responds
      validateStatus: (status) => status >= 200 && status < 500
    });
    return true;
  } catch (error) {
    // Log the error but with more specific handling
    if (axios.isAxiosError(error)) {
      if (error.code === 'ERR_NETWORK') {
        console.error('API server is not reachable:', error.message);
      } else if (error.response) {
        console.error(`API returned error status ${error.response.status}:`, error.message);
      } else {
        console.error('API availability check failed:', error.message);
      }
    } else {
      console.error('Unexpected error during API availability check:', error);
    }
    return false;
  }
};

export default api; 