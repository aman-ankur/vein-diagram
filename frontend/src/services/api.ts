import axios from 'axios';

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

// Create an axios instance with default config
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
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