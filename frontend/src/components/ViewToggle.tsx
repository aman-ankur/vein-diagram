import React from 'react';
import { ToggleButtonGroup, ToggleButton, Box, Typography, Tooltip, Paper, Stack } from '@mui/material';
import { Description as DescriptionIcon, History as HistoryIcon } from '@mui/icons-material';

/**
 * Props for the ViewToggle component
 */
export interface ViewToggleProps {
  /**
   * Current view mode
   */
  currentView: 'current' | 'history';
  
  /**
   * Callback function when view mode changes
   */
  onViewChange: (view: 'current' | 'history') => void;
  
  /**
   * Whether to disable the toggle functionality
   */
  disabled?: boolean;
  
  /**
   * Descriptive text to show when the component is disabled
   */
  disabledText?: string;
}

/**
 * Component that provides a toggle between current PDF biomarkers and full profile history
 */
const ViewToggle: React.FC<ViewToggleProps> = ({
  currentView,
  onViewChange,
  disabled = false,
  disabledText
}) => {
  const handleChange = (
    _event: React.MouseEvent<HTMLElement>,
    newView: 'current' | 'history',
  ) => {
    if (newView !== null) {
      onViewChange(newView);
    }
  };

  const toggleContent = (
    <Paper 
      elevation={2} 
      sx={{ 
        p: 1.5, 
        borderRadius: 2,
        backgroundColor: theme => theme.palette.background.paper
      }}
    >
      <Stack spacing={1}>
        <Typography 
          variant="subtitle1" 
          fontWeight="medium" 
          align="center"
          sx={{ mb: 0.5 }}
        >
          View Mode
        </Typography>
        
        <ToggleButtonGroup
          value={currentView}
          exclusive
          onChange={handleChange}
          aria-label="biomarker view mode"
          disabled={disabled}
          size="large"
          fullWidth
          sx={{ 
            '& .MuiToggleButtonGroup-grouped': {
              border: 1,
              borderColor: 'divider',
              py: 1,
              '&.Mui-selected': {
                backgroundColor: theme => theme.palette.primary.main,
                color: theme => theme.palette.primary.contrastText,
                '&:hover': {
                  backgroundColor: theme => theme.palette.primary.dark,
                },
              },
              '&:not(.Mui-selected)': {
                '&:hover': {
                  backgroundColor: theme => theme.palette.action.hover,
                }
              }
            }
          }}
        >
          <ToggleButton value="current" aria-label="current PDF view">
            <DescriptionIcon sx={{ mr: 1 }} />
            <Typography variant="body1" fontWeight="medium">Current PDF</Typography>
          </ToggleButton>
          <ToggleButton value="history" aria-label="profile history view">
            <HistoryIcon sx={{ mr: 1 }} />
            <Typography variant="body1" fontWeight="medium">Profile History</Typography>
          </ToggleButton>
        </ToggleButtonGroup>
        
        <Typography 
          variant="caption" 
          color="text.secondary" 
          align="center"
        >
          {currentView === 'current' 
            ? 'Viewing biomarkers from the current lab report only' 
            : 'Viewing all historical biomarkers for this profile'}
        </Typography>
      </Stack>
    </Paper>
  );

  return (
    <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto', mb: 3 }}>
      {disabled && disabledText ? (
        <Tooltip title={disabledText}>
          <span>{toggleContent}</span>
        </Tooltip>
      ) : (
        toggleContent
      )}
    </Box>
  );
};

export default ViewToggle; 