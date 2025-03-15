/**
 * Types for PDF upload and processing
 */

// Response from the upload endpoint
export interface UploadResponse {
  file_id: string;
  filename: string;
  status: string;
  message: string;
}

// Status of PDF processing
export interface ProcessingStatus {
  file_id: string;
  status: 'pending' | 'processing' | 'processed' | 'error';
  message?: string;
  error_message?: string;
  processing_details?: Record<string, any>;
  lab_name?: string;
  report_date?: string;
  parsing_confidence?: number;
}

// PDF file information
export interface PDFFile {
  id: number;
  file_id: string;
  original_filename: string;
  file_path: string;
  status: string;
  upload_date: string;
  processed_date?: string;
  report_date?: string;
  lab_name?: string;
  extracted_text?: string;
  error_message?: string;
  parsing_confidence?: number;
  processing_details?: Record<string, any>;
} 