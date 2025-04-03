import React, { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface AuthLayoutProps {
  children: ReactNode;
  title?: string;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ 
  children,
  title = 'Vein Diagram',
}) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link to="/">
          <div className="flex justify-center">
            {/* Logo placeholder - replace with your app logo */}
            <div className="h-12 w-12 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xl font-bold">
              VD
            </div>
          </div>
        </Link>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">{title}</h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        {children}
      </div>
      
      <div className="mt-8 text-center text-sm text-gray-500">
        &copy; {new Date().getFullYear()} Vein Diagram. All rights reserved.
      </div>
    </div>
  );
};

export default AuthLayout; 