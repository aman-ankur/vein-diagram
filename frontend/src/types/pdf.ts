/**
 * Type definitions for PDF uploads and processing
 */

/**
 * Response from the upload API
 */
export interface UploadResponse {
  /**
   * Unique identifier for the uploaded file
   */
  fileId: string;
  
  /**
   * Original filename of the uploaded file
   */
  filename: string;
  
  /**
   * Status of the upload process
   * - 'success': Upload was successful
   * - 'error': Upload failed
   */
  status: 'success' | 'error';
  
  /**
   * Error message if status is 'error'
   */
  error?: string;
  
  /**
   * Timestamp of the upload in ISO format
   */
  timestamp: string;
  
  /**
   * File size in bytes
   */
  fileSize: number;
  
  /**
   * MIME type of the file
   */
  mimeType: string;
}

/**
 * Status of PDF processing
 */
export interface ProcessingStatus {
  /**
   * Unique identifier for the file
   */
  fileId: string;
  
  /**
   * Original filename
   */
  filename: string;
  
  /**
   * Current status of processing
   * - 'pending': File is waiting to be processed
   * - 'processing': File is currently being processed
   * - 'processed' / 'completed': Processing is complete
   * - 'failed' / 'error': Processing failed
   */
  status: 'pending' | 'processing' | 'processed' | 'completed' | 'failed' | 'error';
  
  /**
   * Timestamp when the file was uploaded
   */
  uploadTimestamp: string;
  
  /**
   * Timestamp when processing was completed (if status is 'completed')
   */
  completedTimestamp?: string;
  
  /**
   * Error message if status is 'failed'
   */
  error?: string;
  
  /**
   * Progress percentage (0-100) if status is 'processing'
   */
  progress?: number;
  
  /**
   * Number of biomarkers extracted (if status is 'completed')
   */
  biomarkerCount?: number;
}

/**
 * Biomarker data extracted from PDF
 */
export interface Biomarker {
  /**
   * Name of the biomarker (e.g., "Glucose", "Cholesterol")
   */
  name: string;
  
  /**
   * Value of the biomarker
   */
  value: number;
  
  /**
   * Unit of measurement (e.g., "mg/dL", "mmol/L")
   */
  unit: string;
  
  /**
   * Reference range for normal values (e.g., "70-99")
   */
  referenceRange?: string;
  
  /**
   * Category of the biomarker (e.g., "Lipids", "Metabolic")
   */
  category?: string;
  
  /**
   * Flag indicating if the value is outside the reference range
   */
  isAbnormal?: boolean;
  
  /**
   * Date when the biomarker was measured
   */
  date?: string;
  
  /**
   * Source file ID
   */
  fileId?: string;
}

/**
 * Combined data for multiple biomarker measurements over time
 */
export interface BiomarkerTimeSeries {
  /**
   * Name of the biomarker
   */
  name: string;
  
  /**
   * Unit of measurement
   */
  unit: string;
  
  /**
   * Category of the biomarker
   */
  category?: string;
  
  /**
   * Data points for this biomarker across multiple measurements
   */
  dataPoints: Array<{
    /**
     * Date of measurement
     */
    date: string;
    
    /**
     * Measured value
     */
    value: number;
    
    /**
     * Source file ID
     */
    fileId: string;
    
    /**
     * Reference range at the time of measurement
     */
    referenceRange?: string;
    
    /**
     * Flag indicating if the value is outside the reference range
     */
    isAbnormal?: boolean;
  }>;
  
  /**
   * Average value across all measurements
   */
  average?: number;
  
  /**
   * Minimum value across all measurements
   */
  min?: number;
  
  /**
   * Maximum value across all measurements
   */
  max?: number;
  
  /**
   * Latest value
   */
  latest?: number;
  
  /**
   * Change percentage from the first to the latest measurement
   */
  changePercentage?: number;
}

/**
 * PDF document metadata
 */
export interface PDFMetadata {
  /**
   * File ID
   */
  fileId: string;
  
  /**
   * Original filename
   */
  filename: string;
  
  /**
   * Upload timestamp
   */
  uploadTimestamp: string;
  
  /**
   * Processing timestamp
   */
  processingTimestamp?: string;
  
  /**
   * Number of pages in the PDF
   */
  pageCount?: number;
  
  /**
   * Date of the lab report from the PDF content
   */
  reportDate?: string;
  
  /**
   * Laboratory name from the PDF content
   */
  labName?: string;
  
  /**
   * Patient information (if available)
   */
  patientInfo?: {
    /**
     * Patient ID or MRN
     */
    id?: string;
    
    /**
     * Patient age
     */
    age?: number;
    
    /**
     * Patient gender
     */
    gender?: string;
  };
}

/**
 * Visualization settings for biomarker charts
 */
export interface VisualizationSettings {
  /**
   * Chart type (e.g., "line", "bar", "scatter")
   */
  chartType: 'line' | 'bar' | 'scatter' | 'radar';
  
  /**
   * Show reference ranges on charts
   */
  showReferenceRanges: boolean;
  
  /**
   * Show markers on data points
   */
  showMarkers: boolean;
  
  /**
   * Include abnormal indicators
   */
  showAbnormalIndicators: boolean;
  
  /**
   * Fill area under line charts
   */
  fillArea: boolean;
  
  /**
   * Show grid lines
   */
  showGrid: boolean;
  
  /**
   * Animation duration in milliseconds
   */
  animationDuration: number;
  
  /**
   * Color scheme for charts
   */
  colorScheme: 'default' | 'colorblind' | 'monochrome' | 'pastel';
} 