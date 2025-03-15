import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-800 text-white py-8">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between">
          <div className="mb-6 md:mb-0">
            <h3 className="text-xl font-bold mb-2">Vein Diagram</h3>
            <p className="text-gray-300">
              Visualize and track your blood test results over time.
            </p>
          </div>
          <div>
            <h4 className="text-lg font-semibold mb-2">Links</h4>
            <ul className="space-y-2">
              <li>
                <a href="/" className="text-gray-300 hover:text-white">
                  Home
                </a>
              </li>
              <li>
                <a href="/upload" className="text-gray-300 hover:text-white">
                  Upload
                </a>
              </li>
              <li>
                <a href="/visualizations" className="text-gray-300 hover:text-white">
                  Visualizations
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-8 border-t border-gray-700 text-center text-gray-400">
          <p>&copy; {new Date().getFullYear()} Vein Diagram. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 