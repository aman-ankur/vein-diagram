// React import removed - unused
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ExplanationModal from '../ExplanationModal'; // Default import
import { ThemeProvider } from '@mui/material';
import { theme } from '../../theme';
import { Biomarker } from '../../types/biomarker.d'; // Correct path based on file listing
import { BiomarkerExplanation as BiomarkerExplanationType } from '../../types/api'; // Correct type import

// Mock biomarker data conforming to the Biomarker type
const mockBiomarker: Biomarker = {
  id: 1, // Added missing id
  name: 'Glucose',
  value: 100, // Changed to number
  unit: 'mg/dL',
  referenceRange: '70-99 mg/dL',
  reference_range_low: 70,
  reference_range_high: 99,
  isAbnormal: true,
  date: '2023-10-15T00:00:00Z', // Added missing date
  reportDate: '2023-10-15', // Added reportDate
  category: 'Metabolic', // Added category
  fileId: 'file123', // Added fileId
  fileName: 'report.pdf' // Added fileName
};

// Mock explanation data conforming to BiomarkerExplanationType
const mockExplanationData: BiomarkerExplanationType = {
  name: 'Glucose', // Added name as it's required in the type
  general_explanation: 'General info about Glucose.',
  specific_explanation: 'Your Glucose level is analyzed.',
  // biomarker_id, created_at, from_cache are optional per api.ts
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
          loading={true} // Use 'loading' prop
          error={null}
          biomarker={mockBiomarker} // Pass a valid biomarker even in loading state
          explanation={null}
        />
      </ThemeProvider>
    );

    // Check for loading text/indicator (adjust based on actual implementation)
    expect(screen.getByText(/analyzing your biomarker data/i)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    const errorMessage = 'Failed to fetch explanation';
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={mockOnClose}
          loading={false} // Use 'loading' prop
          error={errorMessage}
          biomarker={mockBiomarker} // Pass valid biomarker
          explanation={null}
        />
      </ThemeProvider>
    );

    expect(screen.getByText(/unable to generate explanation/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('renders explanation content correctly', () => {
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={mockOnClose}
          loading={false} // Use 'loading' prop
          error={null}
          biomarker={mockBiomarker}
          explanation={mockExplanationData} // Pass mock explanation data
        />
      </ThemeProvider>
    );

    // Check title and values
    expect(screen.getByText(mockBiomarker.name)).toBeInTheDocument();
    // Check for the formatted value and unit
    expect(screen.getByText(`${mockBiomarker.value.toFixed(2)}`)).toBeInTheDocument();
    expect(screen.getByText(mockBiomarker.unit)).toBeInTheDocument();
    // Check for reference range
    expect(screen.getByText(mockBiomarker.referenceRange || `${mockBiomarker.reference_range_low}-${mockBiomarker.reference_range_high}`)).toBeInTheDocument();

    // Check explanation text
    expect(screen.getByText(mockExplanationData.general_explanation)).toBeInTheDocument();
    expect(screen.getByText(mockExplanationData.specific_explanation)).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <ExplanationModal
          open={true}
          onClose={mockOnClose}
          loading={false} // Use 'loading' prop
          error={null}
          biomarker={mockBiomarker}
          explanation={mockExplanationData}
        />
      </ThemeProvider>
    );

    // Find close button by aria-label
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
