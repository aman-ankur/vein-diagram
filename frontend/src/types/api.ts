import { Biomarker } from './pdf';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  status?: number;
}

export interface BiomarkerExplanation {
  biomarker_id?: number;
  name: string;
  general_explanation: string;
  specific_explanation: string;
  created_at?: string;
  from_cache?: boolean;
}

export interface UploadResponse {
  fileId: string;
  filename: string;
  status: string;
  message?: string;
}

export interface ProcessingStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  fileId?: string;
}

export interface FileMetadata {
  id: string;
  filename: string;
  upload_date: string;
  lab_name?: string;
  report_date?: string;
  patient_name?: string;
  doctor_name?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  dateOfBirth?: string;
  sex?: 'male' | 'female' | 'other';
  height?: number;
  weight?: number;
  created_at: string;
  updated_at: string;
} 