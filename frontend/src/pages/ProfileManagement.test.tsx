// React import removed - unused
import { render, screen, waitFor, within } from '@testing-library/react'; // fireEvent removed - unused
import userEvent from '@testing-library/user-event'; // Use userEvent for better interaction simulation
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import ProfileManagement from './ProfileManagement';
import * as profileService from '../services/profileService'; // Mock the service
import { theme } from '../main'; // Adjust path if needed
import { Profile } from '../types/Profile'; // Import Profile type

// Mock the profile service, including the new merge function
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
    created_at: '2024-01-01T10:00:00Z',
    favorite_biomarkers: [], // Added previously, ensure it's present
    health_summary: undefined, // Use undefined instead of null
    summary_last_updated: undefined // Use undefined instead of null
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
    created_at: '2024-01-05T11:00:00Z',
    favorite_biomarkers: [], 
    health_summary: undefined, // Use undefined instead of null
    summary_last_updated: undefined // Use undefined instead of null
  },
  {
    id: 'profile-uuid-3', // Add a third profile for testing merge
    name: 'Charlie Merge',
    date_of_birth: '2000-01-01T00:00:00',
    gender: 'other',
    patient_id: 'P789',
    biomarker_count: 5,
    pdf_count: 1,
    last_modified: '2024-03-18T09:00:00Z',
    created_at: '2024-02-01T15:00:00Z',
    favorite_biomarkers: [],
    health_summary: undefined, // Use undefined instead of null
    summary_last_updated: undefined // Use undefined instead of null
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
    // Mock the getProfiles response
    mockedProfileService.getProfiles.mockResolvedValue({
      profiles: mockProfiles,
      total: mockProfiles.length
    });
    // Mock other service functions used
    mockedProfileService.createProfile.mockResolvedValue(mockProfiles[0]); // Placeholder
    mockedProfileService.updateProfile.mockResolvedValue(mockProfiles[0]); // Placeholder
    mockedProfileService.deleteProfile.mockResolvedValue(); // Void return
    mockedProfileService.mergeProfiles.mockResolvedValue({ message: "Profiles merged successfully" }); // Mock merge
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

  // --- Tests for Merge Functionality ---

  it('disables Merge button initially and when only one profile is selected', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Alice Test')).toBeInTheDocument();
    });

    const mergeButton = screen.getByRole('button', { name: /merge selected/i });
    expect(mergeButton).toBeDisabled();

    // Select one profile
    const aliceCheckbox = screen.getAllByRole('checkbox')[1]; // First data row checkbox
    await userEvent.click(aliceCheckbox);
    expect(mergeButton).toBeDisabled();
  });

  it('enables Merge button when two or more profiles are selected', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Alice Test')).toBeInTheDocument();
    });

    const mergeButton = screen.getByRole('button', { name: /merge selected/i });
    expect(mergeButton).toBeDisabled();

    // Select two profiles
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]); // Select Alice
    await userEvent.click(checkboxes[2]); // Select Bob
    
    expect(mergeButton).toBeEnabled();
    expect(mergeButton).toHaveTextContent('Merge Selected (2)');
  });

  it('opens the merge dialog when Merge button is clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Alice Test')).toBeInTheDocument();
    });

    // Select two profiles to enable the button
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]); // Select Alice
    await userEvent.click(checkboxes[2]); // Select Bob

    const mergeButton = screen.getByRole('button', { name: /merge selected/i });
    await userEvent.click(mergeButton);

    // Check if dialog is open
    const dialogTitle = await screen.findByRole('heading', { name: /confirm profile merge/i });
    expect(dialogTitle).toBeInTheDocument();
    expect(screen.getByText(/select target profile/i)).toBeInTheDocument();
  });

  it('shows selected profiles in the merge dialog and enables confirm button only after target selection', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Alice Test')).toBeInTheDocument();
    });

    // Select Alice and Bob
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]); 
    await userEvent.click(checkboxes[2]); 

    const mergeButton = screen.getByRole('button', { name: /merge selected/i });
    await userEvent.click(mergeButton);

    // Dialog should be open
    const dialog = await screen.findByRole('dialog', { name: /confirm profile merge/i });
    expect(dialog).toBeInTheDocument();

    // Check radio buttons for selected profiles exist
    const aliceRadio = within(dialog).getByLabelText(/alice test/i);
    const bobRadio = within(dialog).getByLabelText(/bob sample/i);
    expect(aliceRadio).toBeInTheDocument();
    expect(bobRadio).toBeInTheDocument();
    // Ensure Charlie (not selected) is not there
    expect(within(dialog).queryByLabelText(/charlie merge/i)).not.toBeInTheDocument();

    // Confirm button should be disabled initially
    const confirmMergeButton = within(dialog).getByRole('button', { name: /confirm merge/i });
    expect(confirmMergeButton).toBeDisabled();

    // Select Alice as target
    await userEvent.click(aliceRadio);
    expect(confirmMergeButton).toBeEnabled();

    // Select Bob as target
    await userEvent.click(bobRadio);
    expect(confirmMergeButton).toBeEnabled();
  });

  it('calls mergeProfiles service on confirm merge with correct payload', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Alice Test')).toBeInTheDocument();
    });

    // Select Alice and Bob
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]); 
    await userEvent.click(checkboxes[2]); 

    const mergeButton = screen.getByRole('button', { name: /merge selected/i });
    await userEvent.click(mergeButton);

    // Dialog should be open
    const dialog = await screen.findByRole('dialog', { name: /confirm profile merge/i });
    
    // Select Bob as target
    const bobRadio = within(dialog).getByLabelText(/bob sample/i);
    await userEvent.click(bobRadio);

    // Click confirm
    const confirmMergeButton = within(dialog).getByRole('button', { name: /confirm merge/i });
    await userEvent.click(confirmMergeButton);

    // Verify service call
    expect(mockedProfileService.mergeProfiles).toHaveBeenCalledTimes(1);
    expect(mockedProfileService.mergeProfiles).toHaveBeenCalledWith({
      source_profile_ids: [mockProfiles[0].id], // Alice is source
      target_profile_id: mockProfiles[1].id,   // Bob is target
    });

    // Check if dialog closes and profiles are refetched (mocked)
    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: /confirm profile merge/i })).not.toBeInTheDocument();
    });
    // getProfiles is called initially, then again after merge
    expect(mockedProfileService.getProfiles).toHaveBeenCalledTimes(2); 
  });

});
