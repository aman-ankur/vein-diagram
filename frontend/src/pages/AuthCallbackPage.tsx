import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';

const AuthCallbackPage = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Extract the hash fragment from the URL (used by Supabase auth)
        const hashFragment = window.location.hash;
        
        if (!hashFragment) {
          throw new Error('No auth hash fragment found in URL');
        }

        // Process the callback
        const { error } = await supabase.auth.getSession();
        
        if (error) {
          throw error;
        }

        // Redirect to dashboard or home page upon successful authentication
        navigate('/dashboard');
      } catch (err: any) {
        console.error('Auth callback error:', err);
        setError(err.message || 'Authentication failed');
        
        // Redirect to login after a short delay
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    };

    handleAuthCallback();
  }, [navigate]);

  // Render a loading state or error
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="p-8 bg-white shadow-md rounded-md max-w-md w-full text-center">
        {error ? (
          <div>
            <h2 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h2>
            <p className="text-gray-700 mb-4">{error}</p>
            <p className="text-gray-500">Redirecting you to the login page...</p>
          </div>
        ) : (
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Completing Authentication</h2>
            <div className="flex justify-center mb-4">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
            <p className="text-gray-600">Please wait while we complete the sign-in process...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthCallbackPage; 