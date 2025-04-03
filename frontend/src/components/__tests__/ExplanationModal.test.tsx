import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ExplanationModal, { BiomarkerExplanation } from '../ExplanationModal';
import { ThemeProvider } from '@mui/material';
import { theme } from '../../theme';

// Mock explanation data
const mockExplanation: BiomarkerExplanation = {
  biomarker_id: 1,
  name: 'Glucose',
  general_explanation: 'Glucose is a sugar that serves as the primary source of energy for the body. It comes from carbohydrates in foods and is essential for brain function. The glucose test measures the level of glucose in your bloodstream at the time of the test.',
  specific_explanation: 'Your glucose level of 95 mg/dL is within the normal reference range of 70-99 mg/dL. This suggests your body is effectively regulating blood sugar levels. Maintaining normal glucose levels reduces the risk of developing diabetes and related complications.',
  created_at: '2023-10-15T10:30:00Z',
  from_cache: false
};

const mockBiomarker = {
  name: 'Glucose',
  value: '100',
  unit: 'mg/dL',
  referenceRange: '70-99 mg/dL',
  explanation: 'Your glucose level is slightly elevated.',
  isAbnormal: true
};

describe('ExplanationModal Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state correctly', () => {
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={mockOnClose}
          isLoading={true}
          error={null}
          biomarker={null}
        />
      </ThemeProvider>
    );
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    const errorMessage = 'Failed to fetch explanation';
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={mockOnClose}
          isLoading={false}
          error={errorMessage}
          biomarker={null}
        />
      </ThemeProvider>
    );
    
    expect(screen.getByText(/error/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('renders explanation content correctly', () => {
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={mockOnClose}
          isLoading={false}
          error={null}
          biomarker={mockBiomarker}
        />
      </ThemeProvider>
    );
    
    // Check title and values
    expect(screen.getByText(mockBiomarker.name)).toBeInTheDocument();
    expect(screen.getByText(`${mockBiomarker.value} ${mockBiomarker.unit}`)).toBeInTheDocument();
    expect(screen.getByText(mockBiomarker.referenceRange)).toBeInTheDocument();
    expect(screen.getByText(mockBiomarker.explanation)).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={mockOnClose}
          isLoading={false}
          error={null}
          biomarker={mockBiomarker}
        />
      </ThemeProvider>
    );
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
}); 