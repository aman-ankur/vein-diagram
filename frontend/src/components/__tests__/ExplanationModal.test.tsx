import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ExplanationModal, { BiomarkerExplanation } from '../ExplanationModal';
import { ThemeProvider, createTheme } from '@mui/material/styles';

// Create a theme for testing
const theme = createTheme();

// Mock explanation data
const mockExplanation: BiomarkerExplanation = {
  biomarker_id: 1,
  name: 'Glucose',
  general_explanation: 'Glucose is a sugar that serves as the primary source of energy for the body. It comes from carbohydrates in foods and is essential for brain function. The glucose test measures the level of glucose in your bloodstream at the time of the test.',
  specific_explanation: 'Your glucose level of 95 mg/dL is within the normal reference range of 70-99 mg/dL. This suggests your body is effectively regulating blood sugar levels. Maintaining normal glucose levels reduces the risk of developing diabetes and related complications.',
  created_at: '2023-10-15T10:30:00Z',
  from_cache: false
};

// Test cases
describe('ExplanationModal Component', () => {
  
  test('renders loading state correctly', () => {
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={() => {}}
          biomarkerName="Glucose"
          biomarkerValue={95}
          biomarkerUnit="mg/dL"
          referenceRange="70-99"
          isLoading={true}
          error={null}
          explanation={null}
        />
      </ThemeProvider>
    );
    
    expect(screen.getByText('Generating explanation...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
  
  test('renders error state correctly', () => {
    const errorMessage = 'Unable to generate explanation. Please try again later.';
    
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={() => {}}
          biomarkerName="Glucose"
          biomarkerValue={95}
          biomarkerUnit="mg/dL"
          referenceRange="70-99"
          isLoading={false}
          error={errorMessage}
          explanation={null}
        />
      </ThemeProvider>
    );
    
    expect(screen.getByText('Error Loading Explanation')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });
  
  test('renders explanation content correctly', () => {
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={() => {}}
          biomarkerName="Glucose"
          biomarkerValue={95}
          biomarkerUnit="mg/dL"
          referenceRange="70-99"
          isLoading={false}
          error={null}
          explanation={mockExplanation}
        />
      </ThemeProvider>
    );
    
    // Check title and values
    expect(screen.getByText('Glucose Explained')).toBeInTheDocument();
    expect(screen.getByText('95 mg/dL')).toBeInTheDocument();
    expect(screen.getByText('70-99')).toBeInTheDocument();
    
    // Check explanation sections
    expect(screen.getByText('About this Biomarker')).toBeInTheDocument();
    expect(screen.getByText('Your Results Explained')).toBeInTheDocument();
    
    // Check explanation content
    expect(screen.getByText(/Glucose is a sugar that serves as the primary source of energy/)).toBeInTheDocument();
    expect(screen.getByText(/Your glucose level of 95 mg\/dL is within the normal reference range/)).toBeInTheDocument();
    
    // Check medical disclaimer
    expect(screen.getByText(/This information is for educational purposes only/)).toBeInTheDocument();
  });
  
  test('calls onClose when close button is clicked', () => {
    const handleClose = jest.fn();
    
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={handleClose}
          biomarkerName="Glucose"
          biomarkerValue={95}
          biomarkerUnit="mg/dL"
          referenceRange="70-99"
          isLoading={false}
          error={null}
          explanation={mockExplanation}
        />
      </ThemeProvider>
    );
    
    // Click the close button
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    
    // Verify that onClose was called
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
}); 