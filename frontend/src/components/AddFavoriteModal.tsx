import React, { useState, useMemo } from 'react';
import {
  Modal,
  Box,
  Typography,
  IconButton,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  CircularProgress,
  Alert
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { Biomarker } from '../types/biomarker'; // Assuming Biomarker type is available

interface AddFavoriteModalProps {
  open: boolean;
  onClose: () => void;
  availableBiomarkers: Biomarker[]; // All biomarkers for the profile
  currentFavorites: string[]; // Names of biomarkers already shown in the grid
  onAddFavorite: (biomarkerName: string) => void;
  isLoading?: boolean; // Optional loading state for fetching biomarkers
  error?: string | null; // Optional error state
}

const modalStyle = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 400,
  bgcolor: 'background.paper',
  border: '1px solid #ccc',
  boxShadow: 24,
  p: 4,
  borderRadius: 2,
  maxHeight: '80vh', // Limit height
  display: 'flex',
  flexDirection: 'column',
};

const AddFavoriteModal: React.FC<AddFavoriteModalProps> = ({
  open,
  onClose,
  availableBiomarkers,
  currentFavorites,
  onAddFavorite,
  isLoading = false,
  error = null,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Filter out already favorited/displayed biomarkers and apply search term
  const filteredBiomarkers = useMemo(() => {
    const uniqueBiomarkerNames = Array.from(new Set(availableBiomarkers.map(bm => bm.name)));
    return uniqueBiomarkerNames
      .filter(name => !currentFavorites.includes(name))
      .filter(name => name.toLowerCase().includes(searchTerm.toLowerCase()))
      .sort(); // Sort alphabetically
  }, [availableBiomarkers, currentFavorites, searchTerm]);

  const handleAddClick = (name: string) => {
    onAddFavorite(name);
    onClose(); // Close modal after adding
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="add-favorite-modal-title"
      aria-describedby="add-favorite-modal-description"
    >
      <Box sx={modalStyle}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography id="add-favorite-modal-title" variant="h6" component="h2">
            Add Favorite Biomarker
          </Typography>
          <IconButton onClick={onClose} aria-label="close">
            <CloseIcon />
          </IconButton>
        </Box>

        <TextField
          fullWidth
          variant="outlined"
          label="Search Biomarkers"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="small"
          sx={{ mb: 2 }}
        />

        <Box sx={{ overflowY: 'auto', flexGrow: 1 }}> {/* Make list scrollable */}
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          ) : error ? (
            <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>
          ) : filteredBiomarkers.length > 0 ? (
            <List dense>
              {filteredBiomarkers.map((name) => (
                <ListItem key={name} disablePadding>
                  <ListItemButton onClick={() => handleAddClick(name)}>
                    <ListItemText primary={name} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
              {availableBiomarkers.length === 0 ? 'No biomarkers available.' : 'No matching biomarkers found.'}
            </Typography>
          )}
        </Box>
      </Box>
    </Modal>
  );
};

export default AddFavoriteModal;
