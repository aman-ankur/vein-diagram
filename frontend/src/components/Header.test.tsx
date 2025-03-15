import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Header from './Header';

describe('Header Component', () => {
  test('renders the logo', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    );
    
    const logoElement = screen.getByText('Vein Diagram');
    expect(logoElement).toBeInTheDocument();
  });
  
  test('renders navigation links', () => {
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    );
    
    const homeLink = screen.getByText('Home');
    const uploadLink = screen.getByText('Upload');
    const visualizationsLink = screen.getByText('Visualizations');
    
    expect(homeLink).toBeInTheDocument();
    expect(uploadLink).toBeInTheDocument();
    expect(visualizationsLink).toBeInTheDocument();
  });
}); 