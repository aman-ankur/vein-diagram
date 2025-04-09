import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { Profile } from '../types/Profile';
import { getProfile, getProfiles } from '../services/profileService';
import { useAuth } from './AuthContext'; // Import auth context to get current user

interface ProfileContextType {
  activeProfile: Profile | null;
  setActiveProfile: (profile: Profile | null) => void;
  setActiveProfileById: (profileId: string | null) => Promise<void>;
  loading: boolean;
  error: string | null;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

interface ProfileProviderProps {
  children: ReactNode;
}

export const ProfileProvider: React.FC<ProfileProviderProps> = ({ children }) => {
  const [activeProfile, setActiveProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth(); // Get the current authenticated user

  // Helper to get user-specific localStorage key
  const getProfileStorageKey = () => {
    return user?.id ? `activeProfileId_${user.id}` : null;
  };

  // Load active profile from localStorage on mount or user change
  useEffect(() => {
    // Clear active profile when user changes
    setActiveProfile(null);
    
    // Only try to load a profile if we have a user
    if (!user?.id) return;
    
    const storageKey = getProfileStorageKey();
    if (!storageKey) return;
    
    const storedProfileId = localStorage.getItem(storageKey);
    if (storedProfileId) {
      setActiveProfileById(storedProfileId).catch(err => {
        console.error('Failed to load stored profile:', err);
        // Clear invalid profile ID from storage
        localStorage.removeItem(storageKey);
      });
    }
  }, [user?.id]); // Re-run when user ID changes

  // Set active profile by ID
  const setActiveProfileById = async (profileId: string | null): Promise<void> => {
    const storageKey = getProfileStorageKey();
    
    if (!profileId) {
      setActiveProfile(null);
      if (storageKey) localStorage.removeItem(storageKey);
      return;
    }

    // Don't proceed if no user is logged in
    if (!storageKey) {
      setError('You must be logged in to select a profile');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const profile = await getProfile(profileId);
      setActiveProfile(profile);
      localStorage.setItem(storageKey, profileId);
    } catch (err: unknown) {
      console.error(`Error fetching profile ${profileId}:`, err);
      
      // Check if it's a 404 error (profile might have been deleted or merged)
      const errorMessage = String(err).toLowerCase();
      if (errorMessage.includes('404') || errorMessage.includes('not found')) {
        console.warn(`Profile ${profileId} not found. It may have been deleted or merged into another profile.`);
        setError('The selected profile is no longer available. It may have been deleted or merged into another profile.');
      } else {
        setError('Failed to load profile. Please try again.');
      }
      
      // Always clear invalid profile ID from storage
      setActiveProfile(null);
      if (storageKey) localStorage.removeItem(storageKey);
      
      // Attempt to fetch available profiles to select a new active profile
      try {
        // Import directly from the service, not using dynamic import
        const profilesResponse = await getProfiles();
        if (profilesResponse.profiles && profilesResponse.profiles.length > 0) {
          const firstProfile = profilesResponse.profiles[0];
          setActiveProfile(firstProfile);
          // Store the selected profile ID
          localStorage.setItem(storageKey, firstProfile.id);
        } else {
          // No profiles available, set activeProfile to null
          setActiveProfile(null);
        }
      } catch (fetchError) {
        console.error('Failed to auto-select a profile:', fetchError);
      }
    } finally {
      setLoading(false);
    }
  };

  const value = {
    activeProfile,
    setActiveProfile,
    setActiveProfileById,
    loading,
    error
  };

  return (
    <ProfileContext.Provider value={value}>
      {children}
    </ProfileContext.Provider>
  );
};

// Custom hook to use the profile context
export const useProfile = (): ProfileContextType => {
  const context = useContext(ProfileContext);
  if (context === undefined) {
    throw new Error('useProfile must be used within a ProfileProvider');
  }
  return context;
}; 