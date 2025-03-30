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
  withCredentials: true, // Set to true to send cookies with requests
  // Enforce consistency in query parameters
  paramsSerializer: params => {
    // Use URLSearchParams to properly format and encode parameters
    const searchParams = new URLSearchParams();
    for (const key in params) {
      if (params[key] !== undefined && params[key] !== null) {
        searchParams.append(key, params[key]);
      }
    }
    const serialized = searchParams.toString();
    console.log('🔍 Serialized params:', serialized);
    return serialized;
  }
});

// Add request interceptor for logging and enhancement
api.interceptors.request.use(
  (config) => {
    const fullUrl = config.baseURL && config.url ? config.baseURL + config.url : config.url || '';
    console.log(`🔶 API Request: ${config.method?.toUpperCase()} ${fullUrl}`, {
      params: config.params ? JSON.stringify(config.params) : 'none',
      headers: config.headers,
      data: config.data,
      withCredentials: config.withCredentials
    });
    
    // Enable this log for detailed debugging of query params
    console.log('🔍 Request configuration:', {
      baseURL: config.baseURL,
      url: config.url,
      params: config.params,
      paramsSerializer: config.paramsSerializer ? 'custom serializer present' : 'no serializer'
    });
    
    // Don't modify URL with timestamp - this was causing issues
    // Just preserve the original URL and let Axios handle params normally
    console.log(`🚨 NOT adding timestamp to URL: ${config.url}`);
    
    // Extra debug log to ensure params are included after URL modification
    if (config.params) {
      console.log('🔧 Final params that will be sent:', config.params);
    }
    
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
export const uploadPDF = async (file: File): Promise<PDFResponse> => {
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
export const getBiomarkersByFileId = async (fileId: string, profile_id?: string): Promise<Biomarker[]> => {
  if (!fileId || fileId === 'undefined') {
    throw new Error('Invalid fileId provided to getBiomarkersByFileId');
  }
  
  return withRetry(async () => {
    try {
      // Directly build the URL with the query parameter
      let url = `/api/pdf/${fileId}/biomarkers`;
      
      // Add profile_id directly to the URL if provided
      if (profile_id) {
        url += `?profile_id=${encodeURIComponent(profile_id)}`;
        console.log(`🌟 Explicitly adding profile_id=${profile_id} to URL: ${url}`);
      }
      
      console.log(`Making API request to ${url} with profile_id=${profile_id || 'undefined'}`);
      // Don't pass params object since we're adding params directly to URL
      const response = await api.get(url);
      console.log(`API response received for ${url} with ${response.data.length} biomarkers`);
      
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
        date: item.created_at || new Date().toISOString(),
        // Use the report date from the PDF file if available
        reportDate: item.pdf?.report_date || item.pdf?.uploaded_date || item.created_at || new Date().toISOString()
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
  profile_id?: string;
}): Promise<Biomarker[]> => {
  return withRetry(async () => {
    try {
      // Start with base URL
      let url = '/api/biomarkers';
      
      // Manually build query string for better visibility and control
      if (params) {
        const queryParams: string[] = [];
        
        if (params.profile_id) {
          queryParams.push(`profile_id=${encodeURIComponent(params.profile_id)}`);
          console.log(`🌟 Explicitly adding profile_id=${params.profile_id} to URL`);
        }
        
        if (params.category) {
          queryParams.push(`category=${encodeURIComponent(params.category)}`);
        }
        
        if (params.limit) {
          queryParams.push(`limit=${params.limit}`);
        }
        
        if (params.offset) {
          queryParams.push(`offset=${params.offset}`);
        }
        
        // Add query parameters to URL if there are any
        if (queryParams.length > 0) {
          url += `?${queryParams.join('&')}`;
        }
      }
      
      console.log(`Making API request to ${url} with params:`, params);
      const response = await api.get(url);
      console.log(`API response received for ${url} with ${response.data.length} biomarkers`);
      
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
        date: item.created_at || new Date().toISOString(),
        // Use the report date from the PDF file if available
        reportDate: item.pdf?.report_date || item.pdf?.uploaded_date || item.created_at || new Date().toISOString()
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

  // Define the payload once
  const payload = {
    name: biomarkerName,
    value,
    unit,
    reference_range: referenceRange,
    is_abnormal: isAbnormal
  };

  try {
    let response: AxiosResponse<BiomarkerExplanation>; // Use AxiosResponse type for clarity

    // Check if we have a valid biomarkerId
    if (biomarkerId) {
      console.log(`Making API call to /api/biomarkers/${biomarkerId}/explain using configured 'api' instance`);
      try {
        // Use the 'api' instance with the correct baseURL
        response = await api.post<BiomarkerExplanation>(`/api/biomarkers/${biomarkerId}/explain`, payload);
        console.log('API response status:', response.status);
        console.log('API response data:', response.data);
        // If successful, return the data
        return response.data;
      } catch (error) {
        // Handle 404 errors specifically if falling back is desired
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          console.warn(`Biomarker ID ${biomarkerId} not found or specific endpoint unavailable, falling back to generic endpoint`);
          // Proceed to the generic endpoint call below
        } else {
          // For other errors, log and rethrow to be handled by the outer catch block
          console.error(`Error calling specific endpoint /api/biomarkers/${biomarkerId}/explain:`, error);
          throw error; // Rethrow to be caught by the main catch block
        }
      }
    }

    // If we don't have a biomarkerId OR the specific endpoint call resulted in a 404 (and didn't throw other errors)
    console.log("Making API call to generic /api/biomarkers/explain endpoint using configured 'api' instance");
    // Use the 'api' instance with the correct baseURL
    response = await api.post<BiomarkerExplanation>('/api/biomarkers/explain', payload);
    console.log('Generic API response status:', response.status);
    console.log('Generic API response data:', response.data);

    // Check status explicitly, although interceptor might handle some cases
    if (response.status !== 200) {
       console.error('Non-200 response from generic endpoint:', response.status, response.data);
       // Construct an error similar to what the interceptor would create
       throw {
         message: `Failed to get explanation (Status: ${response.status})`,
         status: response.status,
         data: response.data
       };
    }

    return response.data;

  } catch (error) {
    console.error('==== ERROR IN getBiomarkerExplanation ====');

    // The error might already be an ApiError if it went through the interceptor (from api.post)
    // Or it could be a raw AxiosError if the initial check failed differently, or a standard Error.
    if (axios.isAxiosError(error)) {
      console.error('Axios error details:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        configUrl: error.config?.url, // Log the URL that was actually called
      });

      // Create a standardized ApiError if it's not one already
      const apiError: ApiError = {
        message: error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to get biomarker explanation',
        status: error.response?.status || 500,
        data: error.response?.data || null,
        isNetworkError: !error.response && error.message?.includes('Network Error'),
      };

       // Provide more specific user-friendly messages
      if (apiError.status === 404) {
         apiError.message = 'The biomarker explanation service could not be found. Please contact support.';
       } else if (apiError.status >= 500) {
         apiError.message = 'The server encountered an error generating the explanation. Please try again later.';
       } else if (apiError.isNetworkError || apiError.status === 0) {
         apiError.message = 'Network error. Could not reach the explanation service. Please check your connection.';
       }

       throw apiError; // Throw the standardized error

    } else if (error instanceof Error) {
        console.error('Non-Axios error:', error.message);
        // Throw a generic ApiError structure
        throw { message: error.message, status: 500, data: null } as ApiError;
    } else {
       console.error('Unknown error object:', error);
       throw { message: 'An unknown error occurred.', status: 500, data: null } as ApiError;
    }
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