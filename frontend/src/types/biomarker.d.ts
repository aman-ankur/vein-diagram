/**
 * Biomarker type definitions
 */

export interface Biomarker {
  /**
   * Unique identifier for the biomarker
   */
  id: number;
  
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
   * Lower bound of reference range
   */
  reference_range_low?: number | null;
  
  /**
   * Upper bound of reference range
   */
  reference_range_high?: number | null;
  
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
   * Test date when the biomarker was measured (different format used in some components)
   */
  testDate?: string;
  
  /**
   * Source file ID
   */
  fileId?: string;
} 