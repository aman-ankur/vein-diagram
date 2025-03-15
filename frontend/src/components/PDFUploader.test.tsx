import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PDFUploader from './PDFUploader';
import { pdfService } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  pdfService: {
    uploadPdf: jest.fn()
  }
}));

describe('PDFUploader Component', () => {
  const mockOnSuccess = jest.fn();
  const mockOnError = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('renders the upload area', () => {
    render(
      <PDFUploader 
        onUploadSuccess={mockOnSuccess} 
        onUploadError={mockOnError} 
      />
    );
    
    expect(screen.getByText(/drag and drop your lab report pdf here/i)).toBeInTheDocument();
    expect(screen.getByText(/or click to select a file/i)).toBeInTheDocument();
  });
  
  it('shows an error when a non-PDF file is dropped', async () => {
    render(
      <PDFUploader 
        onUploadSuccess={mockOnSuccess} 
        onUploadError={mockOnError} 
      />
    );
    
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const dropzone = screen.getByText(/drag and drop your lab report pdf here/i).parentElement?.parentElement;
    
    if (dropzone) {
      // Create a custom event
      const dropEvent = createDropEvent([file]);
      fireEvent.drop(dropzone, dropEvent);
      
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('Only PDF files are accepted');
      });
    }
  });
  
  it('shows an error when file is too large', async () => {
    render(
      <PDFUploader 
        onUploadSuccess={mockOnSuccess} 
        onUploadError={mockOnError} 
      />
    );
    
    // Create a mock PDF file that exceeds size limit
    // Note: We can't actually create a 30MB+ file in a test, so we'll mock the size check
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    Object.defineProperty(mockFile, 'size', { value: 31 * 1024 * 1024 }); // 31MB
    
    const dropzone = screen.getByText(/drag and drop your lab report pdf here/i).parentElement?.parentElement;
    
    if (dropzone) {
      const dropEvent = createDropEvent([mockFile]);
      fireEvent.drop(dropzone, dropEvent);
      
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('File size exceeds the 30MB limit');
      });
    }
  });
  
  it('uploads a valid PDF file successfully', async () => {
    // Mock successful upload
    (pdfService.uploadPdf as jest.Mock).mockResolvedValue({
      data: {
        file_id: '123-456',
        filename: 'test.pdf'
      },
      status: 200
    });
    
    render(
      <PDFUploader 
        onUploadSuccess={mockOnSuccess} 
        onUploadError={mockOnError} 
      />
    );
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const dropzone = screen.getByText(/drag and drop your lab report pdf here/i).parentElement?.parentElement;
    
    if (dropzone) {
      const dropEvent = createDropEvent([file]);
      fireEvent.drop(dropzone, dropEvent);
      
      await waitFor(() => {
        expect(pdfService.uploadPdf).toHaveBeenCalledWith(file);
        expect(mockOnSuccess).toHaveBeenCalledWith('123-456', 'test.pdf');
      });
    }
  });
  
  it('handles upload errors', async () => {
    // Mock failed upload
    (pdfService.uploadPdf as jest.Mock).mockRejectedValue({
      message: 'Server error'
    });
    
    render(
      <PDFUploader 
        onUploadSuccess={mockOnSuccess} 
        onUploadError={mockOnError} 
      />
    );
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const dropzone = screen.getByText(/drag and drop your lab report pdf here/i).parentElement?.parentElement;
    
    if (dropzone) {
      const dropEvent = createDropEvent([file]);
      fireEvent.drop(dropzone, dropEvent);
      
      await waitFor(() => {
        expect(pdfService.uploadPdf).toHaveBeenCalledWith(file);
        expect(mockOnError).toHaveBeenCalledWith('Server error');
      });
    }
  });
});

// Helper function to create a drop event
function createDropEvent(files: File[]) {
  return {
    dataTransfer: {
      files,
      items: files.map(file => ({
        kind: 'file',
        type: file.type,
        getAsFile: () => file
      })),
      types: ['Files']
    },
    preventDefault: jest.fn(),
    stopPropagation: jest.fn()
  };
} 