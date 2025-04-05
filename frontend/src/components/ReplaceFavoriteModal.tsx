import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Radio,
  // Box removed - unused
  CircularProgress,
} from '@mui/material';

interface ReplaceFavoriteModalProps {
  open: boolean;
  onClose: () => void;
  biomarkerToAdd: string | null;
  currentFavorites: string[]; // List of current favorite names
  onConfirmReplace: (favoriteToRemove: string, favoriteToAdd: string) => void;
  isLoading?: boolean; // Optional loading state for confirmation action
}

const ReplaceFavoriteModal: React.FC<ReplaceFavoriteModalProps> = ({
  open,
  onClose,
  biomarkerToAdd,
  currentFavorites,
  onConfirmReplace,
  isLoading = false,
}) => {
  const [selectedFavoriteToRemove, setSelectedFavoriteToRemove] = useState<string | null>(null);

  const handleSelectFavorite = (favoriteName: string) => {
    setSelectedFavoriteToRemove(favoriteName);
  };

  const handleConfirm = () => {
    if (selectedFavoriteToRemove && biomarkerToAdd) {
      onConfirmReplace(selectedFavoriteToRemove, biomarkerToAdd);
    }
    // Reset selection on confirm/close
    setSelectedFavoriteToRemove(null); 
  };

  const handleCancel = () => {
    setSelectedFavoriteToRemove(null); // Reset selection
    onClose();
  };

  // Reset selection when modal closes externally
  React.useEffect(() => {
    if (!open) {
      setSelectedFavoriteToRemove(null);
    }
  }, [open]);

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="xs" fullWidth>
      <DialogTitle>Replace Favorite</DialogTitle>
      <DialogContent>
        <Typography variant="body1" gutterBottom>
          Your favorites are full. Select an existing favorite below to replace it with{' '}
          <strong>{biomarkerToAdd || 'the selected biomarker'}</strong>.
        </Typography>
        <List dense sx={{ pt: 1 }}>
          {currentFavorites.map((favName) => (
            <ListItem key={favName} disablePadding>
              <ListItemButton 
                role={undefined} 
                onClick={() => handleSelectFavorite(favName)} 
                dense
                selected={selectedFavoriteToRemove === favName}
              >
                <Radio
                  edge="start"
                  checked={selectedFavoriteToRemove === favName}
                  tabIndex={-1}
                  disableRipple
                  inputProps={{ 'aria-labelledby': `label-${favName}` }}
                  size="small"
                />
                <ListItemText id={`label-${favName}`} primary={favName} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={handleCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button 
          onClick={handleConfirm} 
          variant="contained" 
          disabled={!selectedFavoriteToRemove || isLoading}
          sx={{ minWidth: 90 }} // Prevent layout shift with loader
        >
          {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Replace'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ReplaceFavoriteModal;
