import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Header from './Header';
import { AuthProvider } from '../contexts/AuthContext';

describe('Header Component', () => {
  it('renders navigation links correctly', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Header />
        </AuthProvider>
      </BrowserRouter>
    );

    // Check for navigation links
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Biomarkers')).toBeInTheDocument();
  });

  it('renders logo correctly', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Header />
        </AuthProvider>
      </BrowserRouter>
    );

    // Check for logo text
    expect(screen.getByText('VD')).toBeInTheDocument();
    expect(screen.getByText('Vein Diagram')).toBeInTheDocument();
  });
}); 