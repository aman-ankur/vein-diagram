import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { Profile, ProfileListResponse } from '../types/Profile';
import { getProfile } from '../services/profileService';

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

  // Load active profile from localStorage on mount
  useEffect(() => {
    const storedProfileId = localStorage.getItem('activeProfileId');
    if (storedProfileId) {
      setActiveProfileById(storedProfileId).catch(err => {
        console.error('Failed to load stored profile:', err);
        // Clear invalid profile ID from storage
        localStorage.removeItem('activeProfileId');
      });
    }
  }, []);

  // Set active profile by ID
  const setActiveProfileById = async (profileId: string | null): Promise<void> => {
    if (!profileId) {
      setActiveProfile(null);
      localStorage.removeItem('activeProfileId');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const profile = await getProfile(profileId);
      setActiveProfile(profile);
      localStorage.setItem('activeProfileId', profileId);
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
      localStorage.removeItem('activeProfileId');
      
      // Attempt to fetch available profiles to select a new active profile
      try {
        const { getProfiles } = await import('../services/profileService');
        const profilesResponse = await getProfiles();
        if (profilesResponse.profiles && profilesResponse.profiles.length > 0) {
          console.log('Auto-selecting first available profile:', profilesResponse.profiles[0].id);
          // Set the first available profile as active
          setActiveProfile(profilesResponse.profiles[0]);
          localStorage.setItem('activeProfileId', profilesResponse.profiles[0].id);
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