import React from 'react';
import { render, screen } from '@testing-library/react';
import UploadGuide from './UploadGuide';

describe('UploadGuide Component', () => {
  it('renders the guide title', () => {
    render(<UploadGuide />);
    expect(screen.getByText('Lab Report Upload Guide')).toBeInTheDocument();
  });

  it('displays supported lab providers', () => {
    render(<UploadGuide />);
    expect(screen.getByText('Supported Lab Providers')).toBeInTheDocument();
    expect(screen.getByText('Quest Diagnostics')).toBeInTheDocument();
    expect(screen.getByText('LabCorp')).toBeInTheDocument();
  });

  it('displays file requirements', () => {
    render(<UploadGuide />);
    expect(screen.getByText('File Requirements')).toBeInTheDocument();
    expect(screen.getByText('PDF format only (.pdf extension)')).toBeInTheDocument();
    expect(screen.getByText('Maximum file size: 30MB')).toBeInTheDocument();
  });

  it('displays processing time information', () => {
    render(<UploadGuide />);
    expect(screen.getByText('Processing Time')).toBeInTheDocument();
    expect(screen.getByText(/Most lab reports are processed within 30 seconds/)).toBeInTheDocument();
  });

  it('displays tips for best results', () => {
    render(<UploadGuide />);
    expect(screen.getByText('Tips for Best Results')).toBeInTheDocument();
    expect(screen.getByText('Use the original PDF file from your lab provider')).toBeInTheDocument();
  });

  it('displays privacy information', () => {
    render(<UploadGuide />);
    expect(screen.getByText('Privacy & Security')).toBeInTheDocument();
    expect(screen.getByText(/Your lab reports are processed securely/)).toBeInTheDocument();
  });
}); 