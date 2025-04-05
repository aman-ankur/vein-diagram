import React from 'react';
import { ToggleButtonGroup, ToggleButton, Typography, Box, alpha, useTheme, Tooltip } from '@mui/material';
import { Timeline as TimelineIcon, Description as DescriptionIcon } from '@mui/icons-material';

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
  onChange: (view: 'current' | 'history') => void;
  
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
  onChange,
  disabled = false,
  disabledText
}) => {
  const theme = useTheme();

  const handleChange = (
    _event: React.MouseEvent<HTMLElement>, // Mark event as unused
    newView: 'current' | 'history' | null
  ) => {
    if (newView !== null) {
      onChange(newView);
    }
  };

  const buttonContent = (
    <ToggleButtonGroup
      value={currentView}
      exclusive
      onChange={handleChange}
      aria-label="view toggle"
      disabled={disabled}
      sx={{
        backgroundColor: alpha(theme.palette.background.paper, 0.5),
        backdropFilter: 'blur(8px)',
        borderRadius: '12px',
        padding: '4px',
        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        '& .MuiToggleButtonGroup-grouped': {
          margin: 0,
          border: 0,
          paddingTop: '6px',
          paddingBottom: '6px',
          paddingLeft: '12px',
          paddingRight: '12px',
          '&.Mui-disabled': {
            border: 0,
            color: alpha(theme.palette.text.primary, 0.3),
          },
          '&:not(:first-of-type)': {
            borderRadius: '8px',
          },
          '&:first-of-type': {
            borderRadius: '8px',
          },
        },
      }}
    >
      <ToggleButton 
        value="current" 
        aria-label="current view"
        sx={{
          borderRadius: '8px',
          color: currentView === 'current' ? theme.palette.primary.main : theme.palette.text.secondary,
          typography: 'body2',
          fontWeight: currentView === 'current' ? 600 : 400,
          backgroundColor: currentView === 'current' 
            ? alpha(theme.palette.primary.main, 0.08)
            : 'transparent',
          '&:hover': {
            backgroundColor: currentView === 'current' 
              ? alpha(theme.palette.primary.main, 0.12)
              : alpha(theme.palette.background.paper, 0.6),
          },
          '&.Mui-selected': {
            backgroundColor: alpha(theme.palette.primary.main, 0.08),
            color: theme.palette.primary.main,
            fontWeight: 600,
            '&:hover': {
              backgroundColor: alpha(theme.palette.primary.main, 0.12),
            }
          }
        }}
      >
        <DescriptionIcon 
          fontSize="small" 
          sx={{ mr: 1, fontSize: '1rem' }} 
        />
        <Typography 
          variant="body2" 
          sx={{ 
            fontWeight: 'inherit',
            textTransform: 'none',
            letterSpacing: 0
          }}
        >
          Current Report
        </Typography>
      </ToggleButton>
      
      <ToggleButton 
        value="history" 
        aria-label="history view"
        sx={{
          borderRadius: '8px',
          color: currentView === 'history' ? theme.palette.primary.main : theme.palette.text.secondary,
          typography: 'body2',
          fontWeight: currentView === 'history' ? 600 : 400,
          backgroundColor: currentView === 'history' 
            ? alpha(theme.palette.primary.main, 0.08)
            : 'transparent',
          '&:hover': {
            backgroundColor: currentView === 'history' 
              ? alpha(theme.palette.primary.main, 0.12)
              : alpha(theme.palette.background.paper, 0.6),
          },
          '&.Mui-selected': {
            backgroundColor: alpha(theme.palette.primary.main, 0.08),
            color: theme.palette.primary.main,
            fontWeight: 600,
            '&:hover': {
              backgroundColor: alpha(theme.palette.primary.main, 0.12),
            }
          }
        }}
      >
        <TimelineIcon 
          fontSize="small" 
          sx={{ mr: 1, fontSize: '1rem' }} 
        />
        <Typography 
          variant="body2" 
          sx={{ 
            fontWeight: 'inherit',
            textTransform: 'none',
            letterSpacing: 0
          }}
        >
          History View
        </Typography>
      </ToggleButton>
    </ToggleButtonGroup>
  );

  return disabled && disabledText ? (
    <Tooltip title={disabledText} arrow placement="top">
      <Box sx={{ cursor: 'not-allowed' }}>
        {buttonContent}
      </Box>
    </Tooltip>
  ) : (
    buttonContent
  );
};

export default ViewToggle;
