import React from 'react';
import NewSignupForm from '../components/auth/NewSignupForm';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const NewSignupPage: React.FC = () => {
  const { user, loading } = useAuth();

  // If user is already authenticated, redirect to dashboard
  if (user && !loading) {
    return <Navigate to="/dashboard" replace />;
  }

  // Show loading state while auth state is initializing
  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#0F1A2E] to-[#132440] text-white font-[Inter,SF_Pro] p-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#4A7AFF]"></div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#0F1A2E] to-[#132440] text-white font-[Inter,SF_Pro] p-4"
      onClick={(e) => e.stopPropagation()} // Stop event propagation
    >
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Subtle glow effects in background */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-gradient-radial from-[rgba(99,102,241,0.08)] via-[rgba(99,102,241,0.03)] to-transparent blur-3xl opacity-40"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-gradient-radial from-[rgba(45,125,144,0.08)] via-[rgba(45,125,144,0.03)] to-transparent blur-3xl opacity-40"></div>
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIEwgMCAxMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwgMjU1LCAyNTUsIDAuMDIpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-20"></div>
      </div>

      {/* Main content container */}
      <div className="relative z-10 max-w-md w-full flex flex-col items-center">
        {/* Title - clean and centered */}
        <h1 className="text-2xl md:text-3xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-300 text-center">
          Vein Diagram
        </h1>

        {/* Signup form container - clean and focused */}
        <div className="w-full bg-gradient-to-b from-[rgba(30,41,59,0.8)] to-[rgba(15,23,42,0.8)] backdrop-blur-md rounded-xl border border-[rgba(99,102,241,0.15)] shadow-lg overflow-hidden">
          {/* Form header */}
          <div className="px-6 pt-6 pb-3 border-b border-[rgba(99,102,241,0.1)]">
            <h2 className="text-xl font-semibold text-white">Create an account</h2>
            <p className="text-gray-400 mt-2 text-sm">
              Join our health analytics platform to get started.
            </p>
          </div>
          
          {/* Form */}
          <div className="p-6">
            <NewSignupForm />
          </div>
          
          {/* Features summary - at the very bottom, smaller */}
          <div className="px-6 pb-4 flex flex-wrap gap-x-6 gap-y-2 justify-center text-xs text-gray-500">
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded-full bg-[rgba(99,102,241,0.2)] flex items-center justify-center text-[#8b5cf6] text-xs">✓</div>
              <span>Personalized insights</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded-full bg-[rgba(99,102,241,0.2)] flex items-center justify-center text-[#8b5cf6] text-xs">✓</div>
              <span>AI-powered analysis</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded-full bg-[rgba(99,102,241,0.2)] flex items-center justify-center text-[#8b5cf6] text-xs">✓</div>
              <span>Secure data storage</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewSignupPage;
