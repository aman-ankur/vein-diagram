import React from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';

const HomePage: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8">
        <section className="mb-12">
          <div className="card">
            <h2 className="text-2xl font-bold mb-4">Welcome to Vein Diagram</h2>
            <p className="mb-4">
              Vein Diagram helps you visualize and track your blood test results over time.
              Upload your lab reports and gain insights into your health markers.
            </p>
            <Link to="/upload" className="btn btn-primary">
              Upload Lab Report
            </Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default HomePage; 