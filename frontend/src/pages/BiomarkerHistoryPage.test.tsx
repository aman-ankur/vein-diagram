// React import removed - unused
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import BiomarkerHistoryPage from './BiomarkerHistoryPage';
import * as api from '../services/api'; // Mock the api module
import { theme } from '../main'; // Assuming theme is exported from main
import { Biomarker } from '../types/biomarker'; // Use the correct type

// Mock the API module
jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

// Mock the BiomarkerTable component to check props passed to it
jest.mock('../components/BiomarkerTable', () => ({
  __esModule: true,
  default: jest.fn(({ biomarkers, isLoading, error, showSource }) => (
    <div data-testid="biomarker-table">
      <span data-testid="biomarker-count">{biomarkers?.length || 0}</span>
      <span data-testid="is-loading">{isLoading ? 'true' : 'false'}</span>
      <span data-testid="error-prop">{error || 'null'}</span>
      <span data-testid="show-source-prop">{showSource ? 'true' : 'false'}</span>
      {/* Render biomarker names to help with filtering tests */}
      {biomarkers?.map((b: Biomarker) => <div key={b.id}>{b.name}</div>)}
    </div>
  )),
}));

const mockProfileId = 'profile-123';

const mockBiomarkers: Biomarker[] = [
  { id: 1, name: 'Glucose', value: 95, unit: 'mg/dL', category: 'Metabolic', isAbnormal: false, reportDate: '2024-01-15T10:00:00Z', fileName: 'Report_Jan.pdf', fileId: 'file1' },
  { id: 2, name: 'HDL', value: 55, unit: 'mg/dL', category: 'Lipid', isAbnormal: false, reportDate: '2024-01-15T10:00:00Z', fileName: 'Report_Jan.pdf', fileId: 'file1' },
  { id: 3, name: 'Glucose', value: 105, unit: 'mg/dL', category: 'Metabolic', isAbnormal: true, reportDate: '2024-03-20T11:00:00Z', fileName: 'Report_Mar.pdf', fileId: 'file2' },
  { id: 4, name: 'LDL', value: 130, unit: 'mg/dL', category: 'Lipid', isAbnormal: true, reportDate: '2024-03-20T11:00:00Z', fileName: 'Report_Mar.pdf', fileId: 'file2' },
  { id: 5, name: 'Vitamin D', value: 30, unit: 'ng/mL', category: 'Vitamin', isAbnormal: false, reportDate: '2024-03-20T11:00:00Z', fileName: 'Report_Mar.pdf', fileId: 'file2' },
];

const mockCategories = ['All', 'Metabolic', 'Lipid', 'Vitamin'];

const renderComponent = (profileIdParam = mockProfileId) => {
  return render(
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <MemoryRouter initialEntries={[`/profile/${profileIdParam}/history`]}>
          <Routes>
            <Route path="/profile/:profileId/history" element={<BiomarkerHistoryPage />} />
          </Routes>
        </MemoryRouter>
      </LocalizationProvider>
    </ThemeProvider>
  );
};

describe('BiomarkerHistoryPage', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    mockedApi.getAllBiomarkers.mockResolvedValue(mockBiomarkers);
    mockedApi.getBiomarkerCategories.mockResolvedValue(mockCategories.slice(1)); // Exclude 'All'
  });

  it('renders loading state initially', () => {
    renderComponent();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.queryByTestId('biomarker-table')).not.toBeInTheDocument();
  });

  it('fetches biomarkers and categories on mount with profileId', async () => {
    renderComponent();
    await waitFor(() => {
      expect(mockedApi.getAllBiomarkers).toHaveBeenCalledTimes(1);
      expect(mockedApi.getAllBiomarkers).toHaveBeenCalledWith({ profile_id: mockProfileId, limit: 1000 });
      expect(mockedApi.getBiomarkerCategories).toHaveBeenCalledTimes(1);
    });
  });

  it('renders the table with fetched biomarkers after loading', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      expect(screen.getByTestId('biomarker-table')).toBeInTheDocument();
      // Check props passed to BiomarkerTable
      expect(screen.getByTestId('biomarker-count')).toHaveTextContent(mockBiomarkers.length.toString());
      expect(screen.getByTestId('is-loading')).toHaveTextContent('false');
      expect(screen.getByTestId('error-prop')).toHaveTextContent('null');
      expect(screen.getByTestId('show-source-prop')).toHaveTextContent('true'); // Verify showSource is true
    });
  });

  it('displays an error message if fetching fails', async () => {
    const errorMessage = 'Failed to fetch';
    mockedApi.getAllBiomarkers.mockRejectedValue({ message: errorMessage });
    renderComponent();
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveTextContent(errorMessage);
      expect(screen.queryByTestId('biomarker-table')).not.toBeInTheDocument();
    });
  });

  it('renders filter controls', async () => {
    renderComponent();
    await waitFor(() => expect(mockedApi.getAllBiomarkers).toHaveBeenCalled());

    expect(screen.getByLabelText('Category')).toBeInTheDocument();
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
    expect(screen.getByLabelText('Report')).toBeInTheDocument();
  });

  it('filters biomarkers by category', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByTestId('biomarker-table')).toBeInTheDocument());

    // Initial count
    expect(screen.getByTestId('biomarker-count')).toHaveTextContent('5');
    expect(screen.getByText('Glucose')).toBeInTheDocument(); // Both Glucose entries
    expect(screen.getByText('HDL')).toBeInTheDocument();
    expect(screen.getByText('LDL')).toBeInTheDocument();
    expect(screen.getByText('Vitamin D')).toBeInTheDocument();


    // Select 'Lipid' category
    const categorySelect = screen.getByLabelText('Category');
    await act(async () => {
        fireEvent.mouseDown(categorySelect);
    });
    // Wait for menu items to appear
    await waitFor(() => screen.getByRole('option', { name: 'Lipid' }));
    fireEvent.click(screen.getByRole('option', { name: 'Lipid' }));

    // Check filtered count and content
    await waitFor(() => {
      expect(screen.getByTestId('biomarker-count')).toHaveTextContent('2'); // HDL and LDL
      expect(screen.queryByText('Glucose')).not.toBeInTheDocument();
      expect(screen.getByText('HDL')).toBeInTheDocument();
      expect(screen.getByText('LDL')).toBeInTheDocument();
      expect(screen.queryByText('Vitamin D')).not.toBeInTheDocument();
    });
  });

   it('filters biomarkers by status', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByTestId('biomarker-table')).toBeInTheDocument());

    // Initial count
    expect(screen.getByTestId('biomarker-count')).toHaveTextContent('5');

    // Select 'Abnormal' status
    const statusSelect = screen.getByLabelText('Status');
     await act(async () => {
        fireEvent.mouseDown(statusSelect);
    });
    await waitFor(() => screen.getByRole('option', { name: 'Abnormal' }));
    fireEvent.click(screen.getByRole('option', { name: 'Abnormal' }));

    // Check filtered count (Glucose id:3 and LDL id:4 are abnormal)
    await waitFor(() => {
      expect(screen.getByTestId('biomarker-count')).toHaveTextContent('2');
      expect(screen.getByText('Glucose')).toBeInTheDocument(); // The abnormal one
      expect(screen.getByText('LDL')).toBeInTheDocument();
      expect(screen.queryByText('HDL')).not.toBeInTheDocument();
      expect(screen.queryByText('Vitamin D')).not.toBeInTheDocument();
    });
  });

  it('filters biomarkers by report', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByTestId('biomarker-table')).toBeInTheDocument());

    // Initial count
    expect(screen.getByTestId('biomarker-count')).toHaveTextContent('5');

    // Select 'Report_Jan.pdf' report
    const reportSelect = screen.getByLabelText('Report');
     await act(async () => {
        fireEvent.mouseDown(reportSelect);
    });
    await waitFor(() => screen.getByRole('option', { name: 'Report_Jan.pdf' }));
    fireEvent.click(screen.getByRole('option', { name: 'Report_Jan.pdf' }));

    // Check filtered count (Glucose id:1 and HDL id:2 are from Jan report)
    await waitFor(() => {
      expect(screen.getByTestId('biomarker-count')).toHaveTextContent('2');
      expect(screen.getByText('Glucose')).toBeInTheDocument(); // The one from Jan
      expect(screen.getByText('HDL')).toBeInTheDocument();
      expect(screen.queryByText('LDL')).not.toBeInTheDocument();
      expect(screen.queryByText('Vitamin D')).not.toBeInTheDocument();
    });
  });

});
