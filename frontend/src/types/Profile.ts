/**
 * Interface representing a user profile in the system
 */
export interface Profile {
  id: string;
  name: string;
  date_of_birth?: string;
  gender?: string;
  patient_id?: string;
  created_at: string;
  last_modified: string;
  biomarker_count?: number;
  pdf_count?: number;
  favorite_biomarkers?: string[]; // Added optional list for favorites
  health_summary?: string; // LLM-generated health summary
  summary_last_updated?: string; // Timestamp of last summary generation
}

/**
 * Interface for profile creation
 */
export interface ProfileCreate {
  name: string;
  date_of_birth?: string;
  gender?: string;
  patient_id?: string;
  favorite_biomarkers?: string[]; // Added optional list for favorites
}

/**
 * Interface for profile update
 */
export interface ProfileUpdate {
  name?: string;
  date_of_birth?: string;
  gender?: string;
  patient_id?: string;
}

/**
 * Interface for profile list response
 */
export interface ProfileListResponse {
  profiles: Profile[];
  total: number;
}

/**
 * Interface for profile match with confidence score
 */
export interface ProfileMatch {
  profile: Profile;
  confidence: number;
}

/**
 * Interface for extracted profile metadata
 */
export interface ProfileMetadata {
  patient_name?: string;
  patient_dob?: string;
  patient_gender?: string;
  patient_id?: string;
  lab_name?: string;
  report_date?: string;
}

/**
 * Interface for profile matching response
 */
export interface ProfileMatchingResponse {
  matches: ProfileMatch[];
  metadata: ProfileMetadata;
}
