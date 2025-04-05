import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react'; // Removed act
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '../main'; // Adjust path if needed
import BiomarkerTable, { Biomarker } from './BiomarkerTable';

// Sample biomarker data for testing
const sampleBiomarkers: Biomarker[] = [
  {
    id: 1,
    name: 'Glucose',
    value: 95,
    unit: 'mg/dL',
    reference_range_low: 70,
    reference_range_high: 99,
    category: 'Metabolic',
    isAbnormal: false, // Corrected case
    reportDate: '2024-01-15T10:00:00Z',
    fileName: 'Report_Jan.pdf',
    fileId: 'file1'
  },
  {
    id: 2,
    name: 'Total Cholesterol',
    value: 210,
    unit: 'mg/dL',
    reference_range_low: null,
    reference_range_high: 200,
    referenceRange: '< 200', // Corrected case
    category: 'Lipid',
    isAbnormal: true, // Corrected case
    reportDate: '2024-01-15T10:00:00Z',
    fileName: 'Report_Jan.pdf',
    fileId: 'file1'
  },
  {
    id: 3,
    name: 'HDL Cholesterol',
    value: 55,
    unit: 'mg/dL',
    reference_range_low: 40,
    reference_range_high: null,
    referenceRange: '> 40', // Corrected case
    category: 'Lipid',
    isAbnormal: false, // Corrected case
    reportDate: '2024-03-20T11:00:00Z',
    fileName: 'Report_Mar_Very_Long_Name.pdf',
    fileId: 'file2'
  },
  {
    id: 4,
    name: 'Vitamin D, 25-OH',
    value: 32,
    unit: 'ng/mL',
    reference_range_low: 30,
    reference_range_high: 100,
    category: 'Vitamin',
    isAbnormal: false, // Corrected case
    // Remove original_* properties as they are not in the frontend type
    reportDate: '2023-11-01T09:00:00Z', // Earlier date for sorting test
    fileName: 'Report_Nov.pdf',
    fileId: 'file3'
  }
];

// Helper to wrap component with ThemeProvider
const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};


describe('BiomarkerTable', () => {
  test('renders the table with biomarker data (default view)', () => {
    renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} />);

    // Check if standard table headers are present
    expect(screen.getByText('Biomarker')).toBeInTheDocument();
    expect(screen.getByText('Value')).toBeInTheDocument();
    expect(screen.getByText('Unit')).toBeInTheDocument();
    expect(screen.getByText('Reference Range')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument(); // Check Status header
    expect(screen.getByText('Category')).toBeInTheDocument();
    expect(screen.getByText('Date')).toBeInTheDocument(); // Default date column label
    expect(screen.getByText('Actions')).toBeInTheDocument();
    expect(screen.queryByText('Source Report')).not.toBeInTheDocument(); // Source column shouldn't be there

    // Check if biomarker data is displayed
    expect(screen.getByText('Glucose')).toBeInTheDocument();
    expect(screen.getByText('95')).toBeInTheDocument();
    expect(screen.getByText('210')).toBeInTheDocument();

    // Check pagination count
    expect(screen.getByText(/1–4 of 4/)).toBeInTheDocument(); // Example pagination text
  });

  test('renders status chips correctly', () => {
    renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} />);
    expect(screen.getAllByText('Normal')).toHaveLength(3); // Glucose, HDL, Vit D
    expect(screen.getByText('Abnormal')).toBeInTheDocument(); // Total Cholesterol
  });

  test('filters biomarkers based on search input', () => {
    renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} />);

    // Initial state should show all biomarkers
    expect(screen.getByText('Glucose')).toBeInTheDocument();
    expect(screen.getByText('Total Cholesterol')).toBeInTheDocument();
    expect(screen.getByText('HDL Cholesterol')).toBeInTheDocument();
    expect(screen.getByText('Vitamin D, 25-OH')).toBeInTheDocument();

    // Get the search input and type 'cholesterol'
    const searchInput = screen.getByPlaceholderText('Search biomarkers...');
    fireEvent.change(searchInput, { target: { value: 'cholesterol' } });

    // After filtering, only cholesterol related biomarkers should be shown
    expect(screen.queryByText('Glucose')).not.toBeInTheDocument();
    expect(screen.getByText('Total Cholesterol')).toBeInTheDocument();
    expect(screen.getByText('HDL Cholesterol')).toBeInTheDocument();
    expect(screen.queryByText('Vitamin D, 25-OH')).not.toBeInTheDocument();
  });

  test('handles empty biomarker list', () => {
    renderWithTheme(<BiomarkerTable biomarkers={[]} />);

    // Should show a message when no biomarkers are available
    expect(screen.getByText('No biomarker data available')).toBeInTheDocument();
  });

  test('displays loading state', () => {
    renderWithTheme(<BiomarkerTable biomarkers={[]} isLoading={true} />);

    // Should show loading indicator (within the table body)
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByText('Loading biomarker data...')).toBeInTheDocument();
  });

  test('displays error state', () => {
    const errorMessage = 'Failed to load biomarker data.';
    renderWithTheme(<BiomarkerTable biomarkers={[]} error={errorMessage} />);

    // Should show the error message within an Alert inside the table
    expect(screen.getByRole('alert')).toHaveTextContent(errorMessage);
  });

  test('sorts biomarkers by value when clicking on Value header', () => {
    renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} />);

    // Initial order might vary, find rows first
    let rows = screen.getAllByRole('row');
    expect(within(rows[1]).getByText('Glucose')).toBeInTheDocument(); // Assuming initial sort by name or ID

    // Click on Value column header to sort by value asc
    const valueHeader = screen.getByRole('button', { name: /Value/i });
    fireEvent.click(valueHeader);

    // Get rows again after sorting
    rows = screen.getAllByRole('row');
    // Now the first row should be the one with the lowest value (32)
    expect(within(rows[1]).getByText('Vitamin D, 25-OH')).toBeInTheDocument();

    // Click again to reverse sort order (desc)
    fireEvent.click(valueHeader);

    // Get rows again after reverse sorting
    rows = screen.getAllByRole('row');
    // Now the first row should be the one with the highest value (210)
    expect(within(rows[1]).getByText('Total Cholesterol')).toBeInTheDocument();
  });

  // --- Tests for showSource prop ---
  describe('when showSource is true', () => {
    test('renders additional columns for Test Date and Source Report', () => {
      renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} showSource={true} />);

      expect(screen.getByText('Test Date')).toBeInTheDocument(); // New column label
      expect(screen.getByText('Source Report')).toBeInTheDocument(); // New column label
      expect(screen.queryByText('Date')).not.toBeInTheDocument(); // Default date label shouldn't be there
    });

    test('renders report date and source chip in rows', () => {
      renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} showSource={true} />);

      // Check first row (Glucose from Report_Jan.pdf)
      const firstRow = screen.getAllByRole('row')[1];
      expect(within(firstRow).getByText('1/15/2024')).toBeInTheDocument(); // Formatted reportDate
      expect(within(firstRow).getByText('Report_Jan.pdf')).toBeInTheDocument(); // Source chip

      // Check third row (HDL from Report_Mar_Very_Long_Name.pdf - should be truncated)
      const thirdRow = screen.getAllByRole('row')[3];
      expect(within(thirdRow).getByText('3/20/2024')).toBeInTheDocument();
      expect(within(thirdRow).getByText('Report_Mar_V...')).toBeInTheDocument(); // Truncated filename
    });

    test('sorts by Test Date column', () => {
       renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} showSource={true} />);

       // Initial order might vary
       let rows = screen.getAllByRole('row');
       // Find the date header (use role 'button' as it has TableSortLabel)
       const dateHeader = screen.getByRole('button', { name: /Test Date/i });

       // Click to sort ascending by date
       fireEvent.click(dateHeader);
       rows = screen.getAllByRole('row');
       // Vitamin D (Nov 2023) should be first
       expect(within(rows[1]).getByText('Vitamin D, 25-OH')).toBeInTheDocument();
       expect(within(rows[1]).getByText('11/1/2023')).toBeInTheDocument();
       // Glucose (Jan 2024) should be second
       expect(within(rows[2]).getByText('Glucose')).toBeInTheDocument();
       expect(within(rows[2]).getByText('1/15/2024')).toBeInTheDocument();


       // Click to sort descending by date
       fireEvent.click(dateHeader);
       rows = screen.getAllByRole('row');
       // HDL (Mar 2024) should be first
       expect(within(rows[1]).getByText('HDL Cholesterol')).toBeInTheDocument();
       expect(within(rows[1]).getByText('3/20/2024')).toBeInTheDocument();
       // Total Cholesterol (Jan 2024) should be second or third
       expect(within(rows[2]).getByText('Total Cholesterol')).toBeInTheDocument();
       expect(within(rows[2]).getByText('1/15/2024')).toBeInTheDocument();

    });

     test('renders help text when showSource is true', () => {
      renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} showSource={true} />);
      expect(screen.getByText(/Showing biomarkers from all lab reports/)).toBeInTheDocument();
      expect(screen.getByText(/Click on the source chip to view the original report./)).toBeInTheDocument();
    });
  });

   describe('when showSource is false (default)', () => {
     test('does not render Source Report column', () => {
       renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} />);
       expect(screen.queryByText('Source Report')).not.toBeInTheDocument();
       expect(screen.getByText('Date')).toBeInTheDocument(); // Default date column
     });

     test('does not render help text', () => {
       renderWithTheme(<BiomarkerTable biomarkers={sampleBiomarkers} />);
       expect(screen.queryByText(/Showing biomarkers from all lab reports/)).not.toBeInTheDocument();
     });
   });

});
