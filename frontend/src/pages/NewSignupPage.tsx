import React from 'react';
import NewSignupForm from '../components/auth/NewSignupForm'; // Import form when created

const NewSignupPage: React.FC = () => {
  return (
    <div className="min-h-screen flex bg-gradient-to-br from-[#0F1A2E] to-[#132440] text-white font-[Inter,SF_Pro]">
      {/* Left Panel (40%) */}
      <div className="w-2/5 p-8 hidden md:flex flex-col justify-center items-center relative overflow-hidden">
        {/* Subtle abstract pattern representing vascular system */}
        {/* TODO: Add SVG or background pattern here */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0A2342]/50 to-[#2D7D90]/30 opacity-50"></div>
        <div className="relative z-10 text-center">
          {/* Optional content for the left panel if needed */}
          <h2 className="text-3xl font-semibold mb-4">Vein Diagram</h2>
          <p className="text-lg text-[#E0E6ED]">Advanced Vascular Diagnostics</p>
        </div>
      </div>

      {/* Right Panel (60%) */}
      <div className="w-full md:w-3/5 p-8 flex items-center justify-center">
        <div className="max-w-md w-full">
          {/* Render NewSignupForm component here */}
          <NewSignupForm />
        </div>
      </div>
    </div>
  );
};

export default NewSignupPage;
