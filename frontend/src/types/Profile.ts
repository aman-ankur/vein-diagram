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
}

/**
 * Interface for profile creation
 */
export interface ProfileCreate {
  name: string;
  date_of_birth?: string;
  gender?: string;
  patient_id?: string;
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