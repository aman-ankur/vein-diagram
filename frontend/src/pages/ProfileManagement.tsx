import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Button,
  Typography,
  Card,
  CardContent,
  Box,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
  MenuItem,
  IconButton,
  Grid,
  InputAdornment,
  Snackbar,
  Alert,
  Tooltip, // Import Tooltip
  Checkbox, // Import Checkbox
  Radio, // Import Radio
  RadioGroup, // Import RadioGroup
  FormControlLabel, // Import FormControlLabel
  FormControl, // Import FormControl
  FormLabel // Import FormLabel
} from '@mui/material';
import { 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  PersonAdd as PersonAddIcon,
  Search as SearchIcon,
  History as HistoryIcon, // Import History icon
  MergeType as MergeIcon // Import Merge icon
} from '@mui/icons-material';
import { Link } from 'react-router-dom'; // Import Link
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { format } from 'date-fns';
import { 
  getProfiles, 
  createProfile, 
  updateProfile, 
  deleteProfile,
  mergeProfiles, // Import the new service function
  migrateProfilesToCurrentUser
} from '../services/profileService';
import { Profile, ProfileCreate, ProfileUpdate } from '../types/Profile';

// Function to safely format dates
const safeFormatDate = (date: string | Date | null | undefined, formatString: string, defaultValue = '-'): string => {
  if (!date) return defaultValue;
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return format(dateObj, formatString);
  } catch (error) {
    console.error('Error formatting date:', error);
    return defaultValue;
  }
};

const ProfileManagement: React.FC = () => {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const [rowsPerPage, setRowsPerPage] = useState<number>(10);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [openDialog, setOpenDialog] = useState<boolean>(false);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null);
  
  // Form state
  const [formName, setFormName] = useState<string>('');
  const [formDateOfBirth, setFormDateOfBirth] = useState<Date | null>(null);
  const [formGender, setFormGender] = useState<string>('');
  const [formPatientId, setFormPatientId] = useState<string>('');
  
  // Alert state
  const [alertOpen, setAlertOpen] = useState<boolean>(false);
  const [alertMessage, setAlertMessage] = useState<string>('');
  const [alertSeverity, setAlertSeverity] = useState<'success' | 'error'>('success');

  // State for merging
  const [selectedProfiles, setSelectedProfiles] = useState<Set<string>>(new Set());
  const [mergeDialogOpen, setMergeDialogOpen] = useState<boolean>(false);
  const [targetProfileId, setTargetProfileId] = useState<string | null>(null); // State for target selection in dialog

  // New state for migration
  const [isMigrating, setIsMigrating] = useState<boolean>(false);

  // Fetch profiles on component mount and when pagination/search changes
  useEffect(() => {
    fetchProfiles();
  }, [page, rowsPerPage, searchTerm]);

  const fetchProfiles = async () => {
    try {
      setLoading(true);
      const pageForApi = page + 1; // API uses 1-indexed pages
      const response = await getProfiles(searchTerm, pageForApi, rowsPerPage);
      setProfiles(response.profiles);
      setTotal(response.total);
    } catch (error) {
      showAlert('Failed to fetch profiles', 'error');
      console.error('Error fetching profiles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0); // Reset to first page when searching
    setSelectedProfiles(new Set()); // Clear selection on search
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
    setSelectedProfiles(new Set()); // Clear selection on rows per page change
  };

  // --- Selection Handling ---
  const handleSelectProfile = (profileId: string) => {
    setSelectedProfiles(prevSelected => {
      const newSelected = new Set(prevSelected);
      if (newSelected.has(profileId)) {
        newSelected.delete(profileId);
      } else {
        newSelected.add(profileId);
      }
      return newSelected;
    });
  };

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelecteds = new Set(profiles.map((p) => p.id));
      setSelectedProfiles(newSelecteds);
      return;
    }
    setSelectedProfiles(new Set());
  };

  const isSelected = (id: string) => selectedProfiles.has(id);
  const numSelected = selectedProfiles.size;
  const rowCount = profiles.length;
  // --- End Selection Handling ---

  const showCreateDialog = () => {
    setIsEditing(false);
    setCurrentProfile(null);
    resetForm();
    setOpenDialog(true);
  };

  const showEditDialog = (profile: Profile) => {
    setIsEditing(true);
    setCurrentProfile(profile);
    
    // Set form values
    setFormName(profile.name);
    setFormDateOfBirth(profile.date_of_birth ? new Date(profile.date_of_birth) : null);
    setFormGender(profile.gender || '');
    setFormPatientId(profile.patient_id || '');
    
    setOpenDialog(true);
  };

  const resetForm = () => {
    setFormName('');
    setFormDateOfBirth(null);
    setFormGender('');
    setFormPatientId('');
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const showAlert = (message: string, severity: 'success' | 'error') => {
    setAlertMessage(message);
    setAlertSeverity(severity);
    setAlertOpen(true);
  };

  const handleCloseAlert = () => {
    setAlertOpen(false);
  };

  const handleSubmit = async () => {
    try {
      // Validate form
      if (!formName.trim()) {
        showAlert('Please enter a name', 'error');
        return;
      }
      
      // Format date if provided
      const dateOfBirth = formDateOfBirth 
        ? format(formDateOfBirth, 'yyyy-MM-dd') + 'T00:00:00'
        : undefined;
      
      const profileData: ProfileCreate | ProfileUpdate = {
        name: formName,
        date_of_birth: dateOfBirth,
        gender: formGender || undefined,
        patient_id: formPatientId || undefined
      };
      
      if (isEditing && currentProfile) {
        // Update existing profile
        await updateProfile(currentProfile.id, profileData as ProfileUpdate);
        showAlert('Profile updated successfully', 'success');
      } else {
        // Create new profile
        await createProfile(profileData as ProfileCreate);
        showAlert('Profile created successfully', 'success');
      }
      
      setOpenDialog(false);
      fetchProfiles();
    } catch (error) {
      console.error('Error submitting profile:', error);
      showAlert('Failed to save profile', 'error');
    }
  };

  const handleDelete = async (profileId: string) => {
    try {
      await deleteProfile(profileId);
      showAlert('Profile deleted successfully', 'success');
      fetchProfiles();
    } catch (error) {
      console.error('Error deleting profile:', error);
      showAlert('Failed to delete profile', 'error');
    }
  };

  const handleConfirmMerge = async () => {
    if (!targetProfileId || selectedProfiles.size < 2) {
      showAlert('Please select at least two profiles to merge and choose a target profile.', 'error');
      return;
    }

    const sourceProfileIds = Array.from(selectedProfiles).filter(id => id !== targetProfileId);

    if (sourceProfileIds.length === 0) {
      showAlert('Cannot merge a profile into itself. Select at least one other profile.', 'error');
      return;
    }

    const payload = {
      source_profile_ids: sourceProfileIds,
      target_profile_id: targetProfileId,
    };

    console.log("Merge Payload:", payload); // For debugging

    try {
      setLoading(true); // Indicate loading state
      await mergeProfiles(payload); 
      showAlert('Profiles merged successfully', 'success'); 
      setMergeDialogOpen(false);
      setSelectedProfiles(new Set()); // Clear selection
      setTargetProfileId(null); // Reset target
      fetchProfiles(); // Refresh the profile list
    } catch (error) {
      console.error('Error merging profiles:', error);
      showAlert('Failed to merge profiles', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Add handler for migrating profiles
  const handleMigrateProfiles = async () => {
    try {
      setIsMigrating(true);
      const result = await migrateProfilesToCurrentUser();
      showAlert(`${result.message}`, 'success');
      fetchProfiles(); // Refresh the profiles list
    } catch (error) {
      console.error('Error migrating profiles:', error);
      showAlert('Failed to migrate profiles', 'error');
    } finally {
      setIsMigrating(false);
    }
  };

  const confirmDelete = (profile: Profile) => {
    if (window.confirm(`Are you sure you want to delete the profile "${profile.name}"? This will unlink all biomarkers and PDFs from this profile.`)) {
      handleDelete(profile.id);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h4" gutterBottom>Profile Management</Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            Manage profiles to organize biomarkers and lab reports by individual
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, mt: 2 }}>
            <TextField
              placeholder="Search profiles..."
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={handleSearch}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ width: 300 }}
            />
            <Box>
              {profiles.length === 0 && (
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={handleMigrateProfiles}
                  disabled={isMigrating}
                  sx={{ mr: 1 }}
                >
                  {isMigrating ? 'Migrating...' : 'Migrate Existing Profiles'}
                </Button>
              )}
              <Button
                variant="contained"
                color="secondary"
                startIcon={<MergeIcon />}
                onClick={() => setMergeDialogOpen(true)} // Open merge dialog
                disabled={numSelected < 2} // Enable only if 2 or more are selected
                sx={{ mr: 1 }} // Add margin if needed
              >
                Merge Selected ({numSelected})
              </Button>
              <Button 
                variant="contained" 
                color="primary" 
                startIcon={<PersonAddIcon />} 
                onClick={showCreateDialog}
              >
                Create Profile
              </Button>
            </Box>
          </Box>
          
          {/* Show a notice when no profiles are found */}
          {profiles.length === 0 && !loading && (
            <Paper sx={{ p: 3, mb: 3, textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>No profiles found</Typography>
              <Typography variant="body1" paragraph>
                You don't have any profiles yet. You can create a new profile or migrate existing profiles to your account.
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={handleMigrateProfiles}
                  disabled={isMigrating}
                >
                  {isMigrating ? <CircularProgress size={24} /> : 'Migrate Existing Profiles'}
                </Button>
                <Button 
                  variant="contained" 
                  color="primary" 
                  startIcon={<PersonAddIcon />}
                  onClick={showCreateDialog}
                >
                  Create New Profile
                </Button>
              </Box>
            </Paper>
          )}
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={numSelected > 0 && numSelected < rowCount}
                        checked={rowCount > 0 && numSelected === rowCount}
                        onChange={handleSelectAllClick}
                        inputProps={{ 'aria-label': 'select all profiles' }}
                      />
                    </TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Patient ID</TableCell>
                    <TableCell>Date of Birth</TableCell>
                    <TableCell>Gender</TableCell>
                    <TableCell>Biomarkers</TableCell>
                    <TableCell>PDFs</TableCell>
                    <TableCell>Last Modified</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {profiles.map((profile) => {
                    const isItemSelected = isSelected(profile.id);
                    return (
                    <TableRow 
                      key={profile.id}
                      hover
                      onClick={() => handleSelectProfile(profile.id)} // Allow clicking row to select
                      role="checkbox"
                      aria-checked={isItemSelected}
                      tabIndex={-1}
                      selected={isItemSelected}
                      sx={{ cursor: 'pointer' }} // Indicate clickable row
                    >
                       <TableCell padding="checkbox">
                        <Checkbox
                          checked={isItemSelected}
                          inputProps={{ 'aria-labelledby': `profile-checkbox-${profile.id}` }}
                        />
                      </TableCell>
                      <TableCell id={`profile-checkbox-${profile.id}`}>{profile.name}</TableCell>
                      <TableCell>{profile.patient_id || '-'}</TableCell>
                      <TableCell>
                        {safeFormatDate(profile.date_of_birth, 'yyyy-MM-dd')}
                      </TableCell>
                      <TableCell>{profile.gender || '-'}</TableCell>
                      <TableCell>{profile.biomarker_count || 0}</TableCell>
                      <TableCell>{profile.pdf_count || 0}</TableCell>
                      <TableCell>
                        {safeFormatDate(profile.last_modified, 'yyyy-MM-dd HH:mm')}
                      </TableCell>
                      <TableCell>
                        <IconButton 
                          color="primary" 
                          onClick={() => showEditDialog(profile)}
                          size="small"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton 
                          color="error" 
                          onClick={() => confirmDelete(profile)}
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                        {/* Add View History Button */}
                        <Tooltip title="View Biomarker History">
                          <IconButton
                            color="secondary"
                            component={Link}
                            to={`/profile/${profile.id}/history`}
                            size="small"
                          >
                            <HistoryIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  )})}
                </TableBody>
              </Table>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={total}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
              />
            </TableContainer>
          )}
        </CardContent>
      </Card>
      
      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{isEditing ? 'Edit Profile' : 'Create New Profile'}</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              label="Name"
              fullWidth
              required
              margin="normal"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
            />
            
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Date of Birth"
                value={formDateOfBirth}
                onChange={(date) => setFormDateOfBirth(date)}
                slotProps={{ textField: { fullWidth: true, margin: 'normal' } }}
              />
            </LocalizationProvider>
            
            <TextField
              select
              label="Gender"
              fullWidth
              margin="normal"
              value={formGender}
              onChange={(e) => setFormGender(e.target.value)}
            >
              <MenuItem value="">Select gender</MenuItem>
              <MenuItem value="male">Male</MenuItem>
              <MenuItem value="female">Female</MenuItem>
              <MenuItem value="other">Other</MenuItem>
            </TextField>
            
            <TextField
              label="Patient ID"
              fullWidth
              margin="normal"
              value={formPatientId}
              onChange={(e) => setFormPatientId(e.target.value)}
              placeholder="Patient ID from lab reports"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            {isEditing ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Merge Confirmation Dialog */}
      <Dialog 
        open={mergeDialogOpen} 
        onClose={() => { setMergeDialogOpen(false); setTargetProfileId(null); }} // Reset target on close
        maxWidth="md"
      >
        <DialogTitle>Confirm Profile Merge</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            You have selected {numSelected} profiles to merge. Please select the profile whose details (Name, DOB, Gender, Patient ID, Favorites) you want to keep. All biomarkers and PDFs from the other selected profiles will be moved to this target profile, and the other profiles will be deleted. This action cannot be undone.
          </DialogContentText>
          
          <FormControl component="fieldset" required error={!targetProfileId && numSelected > 0}>
            <FormLabel component="legend">Select Target Profile (to keep)</FormLabel>
            <RadioGroup
              aria-label="target-profile"
              name="target-profile-radio-group"
              value={targetProfileId}
              onChange={(event) => setTargetProfileId(event.target.value)}
            >
              {profiles
                .filter(p => selectedProfiles.has(p.id)) // Only show selected profiles
                .map(profile => (
                  <FormControlLabel 
                    key={profile.id} 
                    value={profile.id} 
                    control={<Radio />} 
                    label={`${profile.name} (ID: ...${profile.id.slice(-6)})`} 
                  />
              ))}
            </RadioGroup>
            {!targetProfileId && numSelected > 0 && (
              <Typography variant="caption" color="error">Please select a target profile.</Typography>
            )}
          </FormControl>

        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setMergeDialogOpen(false); setTargetProfileId(null); }}>Cancel</Button>
          <Button 
            onClick={handleConfirmMerge} 
            variant="contained" 
            color="primary"
            disabled={numSelected < 2 || !targetProfileId || loading} // Disable if less than 2 selected, no target, or loading
          >
            {loading ? <CircularProgress size={24} /> : 'Confirm Merge'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Alert Snackbar */}
      <Snackbar open={alertOpen} autoHideDuration={6000} onClose={handleCloseAlert}>
        <Alert onClose={handleCloseAlert} severity={alertSeverity} sx={{ width: '100%' }}>
          {alertMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ProfileManagement;
