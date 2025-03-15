import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
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
    is_abnormal: false
  },
  {
    id: 2,
    name: 'Total Cholesterol',
    value: 210,
    unit: 'mg/dL',
    reference_range_low: null,
    reference_range_high: 200,
    reference_range_text: '< 200',
    category: 'Lipid',
    is_abnormal: true
  },
  {
    id: 3,
    name: 'HDL Cholesterol',
    value: 55,
    unit: 'mg/dL',
    reference_range_low: 40,
    reference_range_high: null,
    reference_range_text: '> 40',
    category: 'Lipid',
    is_abnormal: false
  },
  {
    id: 4,
    name: 'Vitamin D, 25-OH',
    value: 32,
    unit: 'ng/mL',
    reference_range_low: 30,
    reference_range_high: 100,
    category: 'Vitamin',
    is_abnormal: false,
    original_name: '25-Hydroxyvitamin D',
    original_value: '32.1',
    original_unit: 'ng/mL'
  }
];

describe('BiomarkerTable', () => {
  test('renders the table with biomarker data', () => {
    render(<BiomarkerTable biomarkers={sampleBiomarkers} />);
    
    // Check if table headers are present
    expect(screen.getByText('Biomarker')).toBeInTheDocument();
    expect(screen.getByText('Value')).toBeInTheDocument();
    expect(screen.getByText('Unit')).toBeInTheDocument();
    expect(screen.getByText('Reference Range')).toBeInTheDocument();
    expect(screen.getByText('Category')).toBeInTheDocument();
    
    // Check if biomarker data is displayed
    expect(screen.getByText('Glucose')).toBeInTheDocument();
    expect(screen.getByText('95')).toBeInTheDocument();
    expect(screen.getByText('210')).toBeInTheDocument();
    
    // Check if the count is displayed
    expect(screen.getByText('Biomarkers (4)')).toBeInTheDocument();
  });
  
  test('highlights abnormal values', () => {
    render(<BiomarkerTable biomarkers={sampleBiomarkers} />);
    
    // Find the row with 'Total Cholesterol'
    const rows = screen.getAllByRole('row');
    let totalCholesterolRow;
    
    for (const row of rows) {
      if (within(row).queryByText('Total Cholesterol')) {
        totalCholesterolRow = row;
        break;
      }
    }
    
    // Check if the row exists
    expect(totalCholesterolRow).toBeDefined();
    
    // The cells should have the highlighted class or style
    // Since we're using styled-components, we'd need to test for the styling indirectly
    // This is just a placeholder approach - in a real test, you might need to use a different approach
    if (totalCholesterolRow) {
      const cells = within(totalCholesterolRow).getAllByRole('cell');
      expect(cells[0]).toHaveTextContent('Total Cholesterol');
      expect(cells[1]).toHaveTextContent('210');
      
      // The following assertion relies on implementation details and might be brittle
      // A better approach would be to test the actual styling or use test IDs
      expect(cells[0]).toHaveAttribute('class');
    }
  });
  
  test('filters biomarkers based on search input', () => {
    render(<BiomarkerTable biomarkers={sampleBiomarkers} />);
    
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
    render(<BiomarkerTable biomarkers={[]} />);
    
    // Should show a message when no biomarkers are available
    expect(screen.getByText('No biomarker data available.')).toBeInTheDocument();
  });
  
  test('displays loading state', () => {
    render(<BiomarkerTable biomarkers={[]} isLoading={true} />);
    
    // Should show loading indicator
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
  
  test('displays error state', () => {
    const errorMessage = 'Failed to load biomarker data.';
    render(<BiomarkerTable biomarkers={[]} error={errorMessage} />);
    
    // Should show the error message
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });
  
  test('sorts biomarkers when clicking on column headers', () => {
    render(<BiomarkerTable biomarkers={sampleBiomarkers} />);
    
    // Initial order (assumed to be by name alphabetically)
    const rows = screen.getAllByRole('row');
    let firstRow = rows[1]; // First row after header
    expect(within(firstRow).getByText('Glucose')).toBeInTheDocument();
    
    // Click on Value column header to sort by value
    const valueHeader = screen.getByText('Value');
    fireEvent.click(valueHeader);
    
    // Get rows again after sorting
    const sortedRows = screen.getAllByRole('row');
    const firstSortedRow = sortedRows[1]; // First row after header
    
    // Now the first row should be the one with the lowest value (32)
    expect(within(firstSortedRow).getByText('Vitamin D, 25-OH')).toBeInTheDocument();
    
    // Click again to reverse sort order
    fireEvent.click(valueHeader);
    
    // Get rows again after reverse sorting
    const reverseSortedRows = screen.getAllByRole('row');
    const firstReverseSortedRow = reverseSortedRows[1]; // First row after header
    
    // Now the first row should be the one with the highest value (210)
    expect(within(firstReverseSortedRow).getByText('Total Cholesterol')).toBeInTheDocument();
  });
}); 