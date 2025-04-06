import React, { createContext, useState, useContext, useEffect, ReactNode, useCallback } from 'react';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import { supabase, User, Session } from '../services/supabaseClient';
import { AuthError, AuthResponse, OAuthResponse } from '@supabase/supabase-js';
import { getProfiles } from '../services/profileService'; // Import getProfiles function
import { logger } from '../utils/logger'; // Import logger

// Define the shape of our auth context
interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean; // Represents overall auth loading state
  checkingProfiles: boolean; // Specific loading state for profile check
  error: string | null;
  signUp: (email: string, password: string) => Promise<AuthResponse>;
  signIn: (email: string, password: string) => Promise<AuthResponse>;
  signInWithGoogle: () => Promise<OAuthResponse>;
  signOut: () => Promise<{ error: AuthError | null }>;
  resetPassword: (email: string) => Promise<{ data: {} | null; error: AuthError | null }>;
}

// Create the auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Props for the AuthProvider component
interface AuthProviderProps {
  children: ReactNode;
}

// Create the Auth Provider component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const navigate = useNavigate(); // Get navigate function
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState<boolean>(true); // Initial auth state loading
  const [checkingProfiles, setCheckingProfiles] = useState<boolean>(false); // Loading for profile check specifically
  const [error, setError] = useState<string | null>(null);
  const [initialCheckDone, setInitialCheckDone] = useState<boolean>(false); // Flag to ensure redirect check runs only once per session

  // Function to perform the profile check and redirect
  const performInitialRedirectCheck = useCallback(async (userToCheck: User | null) => {
    // Don't run if no user, or if the check was already done for this session/user state
    if (!userToCheck || initialCheckDone) {
      setLoading(false); // Ensure overall loading stops if check isn't needed
      setCheckingProfiles(false);
      return;
    }

    logger.info('Performing initial redirect check...');
    setCheckingProfiles(true); // Indicate profile check is happening
    setError(null); // Clear previous errors

    try {
      const profileResponse = await getProfiles();
      // Check if still the same user after the async call
      const { data: { user: currentUserAfterCheck } } = await supabase.auth.getUser();
      if (currentUserAfterCheck?.id === userToCheck.id) {
        if (profileResponse.profiles.length === 0) {
          logger.info('Initial Redirect Check: User has 0 profiles, redirecting to /welcome');
          navigate('/welcome', { replace: true });
        } else {
          logger.info(`Initial Redirect Check: User has ${profileResponse.profiles.length} profiles, proceeding normally.`);
          // Optional: Force redirect to dashboard if profiles exist and user isn't already there
          // if (window.location.pathname === '/welcome' || window.location.pathname === '/') {
          //   navigate('/dashboard', { replace: true });
          // }
        }
        setInitialCheckDone(true); // Mark check as done for this user state
      } else {
         logger.warn('User changed during profile check, aborting redirect logic.');
         setInitialCheckDone(false); // Reset flag as user context changed
      }
    } catch (profileError) {
      logger.error('Error fetching profiles during initial check:', profileError);
      setError('Could not verify profile status. Please try refreshing.');
      setInitialCheckDone(true); // Mark as done even on error to prevent loops for this state
    } finally {
      setCheckingProfiles(false); // Stop profile check loading
      setLoading(false); // Ensure overall loading stops
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate, initialCheckDone]); // Dependency on initialCheckDone prevents re-running if already done


  // Initialize auth state on mount and subscribe to changes
  useEffect(() => {
    let isMounted = true;

    // Function to handle auth state changes
    const handleAuthStateChange = (event: string, newSession: Session | null) => {
      if (!isMounted) return;

      logger.info(`Auth event: ${event}`);
      const currentUser = newSession?.user || null;
      const previousUserId = user?.id; // Capture previous user ID

      setSession(newSession);
      setUser(currentUser);

      // Reset check flag only if user identity changes (login/logout)
      if (previousUserId !== currentUser?.id) {
        logger.info('User identity changed, resetting initialCheckDone flag.');
        setInitialCheckDone(false);
      }

      // Perform check on SIGNED_IN, relying on the flag and useCallback dependency
      if (event === 'SIGNED_IN' && currentUser) {
         // The check will be triggered by the change in `user` dependency in the next effect
         // Or we can call it directly, ensuring the flag prevents loops
         // Let's rely on the next effect triggered by user change for simplicity now.
      } else if (event === 'SIGNED_OUT') {
        setInitialCheckDone(false); // Reset flag on sign out
        navigate('/login', { replace: true });
      } else if (event === 'INITIAL_SESSION') {
         // Initial session loaded, trigger the check if user exists
         performInitialRedirectCheck(currentUser);
      } else {
         // For other events like TOKEN_REFRESHED, USER_UPDATED, ensure loading is false if not already checking
         if (!checkingProfiles) setLoading(false);
      }
    };

    // Get initial session state
    supabase.auth.getSession().then(({ data, error }) => {
      if (!isMounted) return;
      if (error) {
        logger.error('Error getting initial session:', error);
        setError('Failed to initialize authentication');
        setLoading(false);
      } else {
        handleAuthStateChange('INITIAL_SESSION', data.session);
      }
    }).catch(err => {
       if (isMounted) {
         logger.error('Exception getting initial session:', err);
         setError('Failed to initialize authentication');
         setLoading(false);
       }
    });

    // Subscribe to subsequent auth changes
    const { data: authListener } = supabase.auth.onAuthStateChange(handleAuthStateChange);

    // Cleanup
    return () => {
      isMounted = false;
      authListener?.subscription.unsubscribe();
    };
  // Run only once on mount
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Effect to run the check when the user object changes (e.g., after login completes)
  // This is separated to ensure state updates from the listener happen first
  useEffect(() => {
    performInitialRedirectCheck(user);
  }, [user, performInitialRedirectCheck]);


  // --- Auth Action Methods ---

  const signUp = async (email: string, password: string) => {
    setError(null);
    setInitialCheckDone(false); // Reset check flag for potential new user session
    return await supabase.auth.signUp({ email, password });
  };

  const signIn = async (email: string, password: string) => {
    setError(null);
    setInitialCheckDone(false); // Reset check flag before sign-in attempt
    // onAuthStateChange listener will handle the redirect logic after success
    return await supabase.auth.signInWithPassword({ email, password });
  };

  const signInWithGoogle = async () => {
    setError(null);
    setInitialCheckDone(false); // Reset check flag before OAuth attempt
    const redirectUrl = import.meta.env.VITE_FRONTEND_URL || window.location.origin;
    logger.info(`Auth redirect URL: ${redirectUrl}/auth/callback`);
    // onAuthStateChange listener will handle the redirect logic after success
    return await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${redirectUrl}/auth/callback`,
        queryParams: { prompt: 'select_account', access_type: 'online' }
      },
    });
  };

  const signOut = async () => {
    setError(null);
    setInitialCheckDone(false); // Reset flag
    // onAuthStateChange listener handles the redirect to /login
    return await supabase.auth.signOut();
  };

  const resetPassword = async (email: string) => {
    setError(null);
    const redirectUrl = import.meta.env.VITE_FRONTEND_URL || window.location.origin;
    return await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${redirectUrl}/reset-password`,
    });
  };

  // Context value
  const value = {
    user,
    session,
    loading: loading || checkingProfiles, // Combine loading states for simplicity downstream
    checkingProfiles, // Expose specific state if needed
    error,
    signUp,
    signIn,
    signInWithGoogle,
    signOut,
    resetPassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
