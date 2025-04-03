import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PDFUploader from '../PDFUploader';
import { message } from 'antd';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock antd message
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  message: {
    error: jest.fn(),
    success: jest.fn()
  }
}));

// Helper function to create a drop event
const createDropEvent = (files: File[]) => ({
  preventDefault: jest.fn(),
  stopPropagation: jest.fn(),
  dataTransfer: {
    files,
    items: files.map(file => ({
      kind: 'file',
      type: file.type,
      getAsFile: () => file
    })),
    types: ['Files']
  }
});

describe('PDFUploader Component', () => {
  const mockOnUploadSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders upload area correctly', () => {
    render(<PDFUploader onUploadSuccess={mockOnUploadSuccess} />);
    
    expect(screen.getByText('Click or drag PDF file to this area to upload')).toBeInTheDocument();
    expect(screen.getByText(/support for a single pdf file upload/i)).toBeInTheDocument();
  });

  it('shows an error when a non-PDF file is dropped', () => {
    render(<PDFUploader onUploadSuccess={mockOnUploadSuccess} />);
    
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const dropzone = screen.getByRole('button', { name: /upload/i });
    
    if (dropzone) {
      // Create a custom event
      const dropEvent = createDropEvent([file]);
      fireEvent.drop(dropzone, dropEvent);
      
      expect(message.error).toHaveBeenCalledWith('You can only upload PDF files!');
    }
  });

  it('shows an error when file is too large', () => {
    render(<PDFUploader onUploadSuccess={mockOnUploadSuccess} />);
    
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    Object.defineProperty(mockFile, 'size', { value: 31 * 1024 * 1024 }); // 31MB
    
    const dropzone = screen.getByRole('button', { name: /upload/i });
    
    if (dropzone) {
      const dropEvent = createDropEvent([mockFile]);
      fireEvent.drop(dropzone, dropEvent);
      
      expect(message.error).toHaveBeenCalledWith('File must be smaller than 30MB!');
    }
  });

  it('uploads a valid PDF file successfully', async () => {
    const mockResponse = { data: { file_id: '123' } };
    mockedAxios.post.mockResolvedValueOnce(mockResponse);
    
    render(<PDFUploader onUploadSuccess={mockOnUploadSuccess} />);
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const dropzone = screen.getByRole('button', { name: /upload/i });
    
    if (dropzone) {
      const dropEvent = createDropEvent([file]);
      fireEvent.drop(dropzone, dropEvent);
      
      // Wait for the upload to complete
      await screen.findByText(/uploaded successfully/i);
      
      expect(mockedAxios.post).toHaveBeenCalled();
      expect(mockOnUploadSuccess).toHaveBeenCalledWith('123');
      expect(message.success).toHaveBeenCalledWith('test.pdf uploaded successfully');
    }
  });

  it('handles upload errors', async () => {
    const mockError = new Error('Upload failed');
    mockedAxios.post.mockRejectedValueOnce(mockError);
    
    render(<PDFUploader onUploadSuccess={mockOnUploadSuccess} />);
    
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const dropzone = screen.getByRole('button', { name: /upload/i });
    
    if (dropzone) {
      const dropEvent = createDropEvent([file]);
      fireEvent.drop(dropzone, dropEvent);
      
      // Wait for the error message
      await screen.findByText(/upload failed/i);
      
      expect(message.error).toHaveBeenCalledWith('test.pdf upload failed');
    }
  });
}); 