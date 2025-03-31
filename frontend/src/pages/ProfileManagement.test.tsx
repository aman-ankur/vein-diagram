import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import ProfileManagement from './ProfileManagement';
import * as profileService from '../services/profileService'; // Mock the service
import { theme } from '../main'; // Adjust path if needed
import { Profile } from '../types/Profile'; // Import Profile type

// Mock the profile service
jest.mock('../services/profileService');
const mockedProfileService = profileService as jest.Mocked<typeof profileService>;

const mockProfiles: Profile[] = [
  {
    id: 'profile-uuid-1',
    name: 'Alice Test',
    date_of_birth: '1990-05-15T00:00:00',
    gender: 'female',
    patient_id: 'P123',
    biomarker_count: 15,
    pdf_count: 2,
    last_modified: '2024-03-10T12:00:00Z',
    created_at: '2024-01-01T10:00:00Z'
  },
  {
    id: 'profile-uuid-2',
    name: 'Bob Sample',
    date_of_birth: '1985-11-20T00:00:00',
    gender: 'male',
    patient_id: 'P456',
    biomarker_count: 30,
    pdf_count: 3,
    last_modified: '2024-03-15T14:30:00Z',
    created_at: '2024-01-05T11:00:00Z'
  },
];

// Helper to wrap component
const renderComponent = () => {
  return render(
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <MemoryRouter>
          <ProfileManagement />
        </MemoryRouter>
      </LocalizationProvider>
    </ThemeProvider>
  );
};

describe('ProfileManagement Page', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    // Mock the getProfiles response according to ProfileListResponse type
    mockedProfileService.getProfiles.mockResolvedValue({
      profiles: mockProfiles,
      total: mockProfiles.length
      // Remove incorrect page, size, pages properties
    });
  });

  it('renders the profile table', async () => {
    renderComponent();
    await waitFor(() => {
      expect(mockedProfileService.getProfiles).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Alice Test')).toBeInTheDocument();
      expect(screen.getByText('Bob Sample')).toBeInTheDocument();
    });
  });

  it('renders the "View History" button for each profile linking correctly', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Alice Test')).toBeInTheDocument();
    });

    // Find rows
    const rows = screen.getAllByRole('row');

    // Check Alice Test row
    const aliceRow = rows.find(row => within(row).queryByText('Alice Test'));
    expect(aliceRow).toBeInTheDocument();
    if (aliceRow) {
      const historyButton = within(aliceRow).getByRole('link', { name: /view biomarker history/i });
      expect(historyButton).toBeInTheDocument();
      expect(historyButton).toHaveAttribute('href', `/profile/${mockProfiles[0].id}/history`);
    }

    // Check Bob Sample row
    const bobRow = rows.find(row => within(row).queryByText('Bob Sample'));
    expect(bobRow).toBeInTheDocument();
    if (bobRow) {
      const historyButton = within(bobRow).getByRole('link', { name: /view biomarker history/i });
      expect(historyButton).toBeInTheDocument();
      expect(historyButton).toHaveAttribute('href', `/profile/${mockProfiles[1].id}/history`);
    }
  });

  // Add more tests for create, edit, delete, search, pagination as needed...
});
