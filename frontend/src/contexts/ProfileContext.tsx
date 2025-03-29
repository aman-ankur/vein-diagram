import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { Profile } from '../types/Profile';
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
    } catch (err) {
      console.error(`Error fetching profile ${profileId}:`, err);
      setError('Failed to load profile. Please try again.');
      setActiveProfile(null);
      localStorage.removeItem('activeProfileId');
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