import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  LinearProgress,
  Alert,
  TextField,
  InputAdornment,
  Tooltip,
  TablePagination,
  IconButton,
  Collapse,
  useTheme,
  alpha,
  Button,
  TableSortLabel,
  CircularProgress
} from '@mui/material';
import {
  Search as SearchIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Refresh as RefreshIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  FilterList as FilterListIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Check as CheckIcon,
  Timeline as TimelineIcon,
  History as HistoryIcon,
  Psychology as PsychologyIcon,
  MoreVert as MoreVertIcon, // Added for 3-dot menu
  Delete as DeleteIcon, // Added for delete action
  StarBorder as StarBorderIcon, // Added for favorite toggle
  Star as StarIcon // Added for favorite toggle
} from '@mui/icons-material';
import { SvgIcon, Menu, MenuItem } from '@mui/material'; // Added Menu, MenuItem
import type { Biomarker } from '../types/biomarker';

// Re-export the Biomarker type
export type { Biomarker };

interface BiomarkerTableProps {
  fileId?: string;
  biomarkers?: Biomarker[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onViewHistory?: (biomarker: Biomarker) => void;
  onExplainWithAI?: (biomarker: Biomarker) => void;
  onDeleteBiomarker?: (biomarkerId: number) => void; // Added delete callback
  onToggleFavorite?: (biomarkerName: string) => void; // Added favorite toggle callback
  isFavoriteChecker?: (biomarkerName: string) => boolean; // Function to check if a biomarker is favorite
  isFavoriteLimitReached?: boolean; // Flag if max favorites reached
  onReplaceFavoriteRequest?: (biomarkerName: string) => void; // Callback to trigger replacement modal
  showSource?: boolean; // Show source PDF information
}

// Interface for the column definition
interface Column {
  id: keyof Biomarker | 'status' | 'actions'; // Added 'actions'
  label: string;
  minWidth?: number;
  align?: 'right' | 'left' | 'center';
  format?: (value: any) => string;
  sortable?: boolean;
}

// Define the columns for the table
const columns: Column[] = [
  { id: 'name', label: 'Biomarker', minWidth: 170, sortable: true },
  { id: 'value', label: 'Value', minWidth: 100, align: 'right', sortable: true },
  { id: 'unit', label: 'Unit', minWidth: 80, align: 'center' },
  { id: 'referenceRange', label: 'Reference Range', minWidth: 120, align: 'center' },
  { id: 'status', label: 'Status', minWidth: 100, align: 'center' },
  { id: 'category', label: 'Category', minWidth: 120, align: 'center', sortable: true },
  { id: 'reportDate', label: 'Report Date', minWidth: 120, align: 'center', 
    format: (value: string) => value ? new Date(value).toLocaleDateString() : 'N/A',
    sortable: true 
  },
  { id: 'actions', label: 'Actions', minWidth: 150, align: 'center' },
];

// Function to determine if a value is outside the reference range
const isOutsideRange = (biomarker: Biomarker): boolean | undefined => {
  // If isAbnormal is set, use that value
  if (biomarker.isAbnormal !== undefined) {
    return biomarker.isAbnormal;
  }
  
  // If we have numeric reference range bounds, use those (check for null/undefined)
  if (biomarker.reference_range_low != null && biomarker.reference_range_high != null) {
    return biomarker.value < biomarker.reference_range_low || biomarker.value > biomarker.reference_range_high;
  }
  
  // Otherwise, try to parse from the reference range text
  if (!biomarker.referenceRange) {
    return undefined;
  }

  const referenceRange = biomarker.referenceRange.trim();
  
  // Try to parse ranges in format "X-Y"
  const dashMatch = referenceRange.match(/^(\d+\.?\d*)\s*-\s*(\d+\.?\d*)$/);
  if (dashMatch) {
    const [_, min, max] = dashMatch;
    return biomarker.value < parseFloat(min) || biomarker.value > parseFloat(max);
  }
  
  // Try to parse ranges in format "< X" or "<= X"
  const lessThanMatch = referenceRange.match(/^<\s*=?\s*(\d+\.?\d*)$/);
  if (lessThanMatch) {
    const [_, max] = lessThanMatch;
    return biomarker.value > parseFloat(max);
  }
  
  // Try to parse ranges in format "> X" or ">= X"
  const greaterThanMatch = referenceRange.match(/^>\s*=?\s*(\d+\.?\d*)$/);
  if (greaterThanMatch) {
    const [_, min] = greaterThanMatch;
    return biomarker.value < parseFloat(min);
  }
  
  // Couldn't determine range
  return undefined;
};

// Function to get status chip for biomarker
const StatusChip: React.FC<{ biomarker: Biomarker }> = ({ biomarker }) => {
  const isAbnormal = biomarker.isAbnormal !== undefined 
    ? biomarker.isAbnormal 
    : isOutsideRange(biomarker);
  
  if (isAbnormal === undefined) {
    return (
      <Chip 
        size="small" 
        icon={<WarningIcon />} 
        label="Unknown" 
        color="default"
        variant="outlined"
      />
    );
  }
  
  return isAbnormal ? (
    <Tooltip title="Outside normal range">
      <Chip 
        size="small" 
        icon={<ErrorIcon />} 
        label="Abnormal" 
        color="error" 
        variant="outlined"
      />
    </Tooltip>
  ) : (
    <Tooltip title="Within normal range">
      <Chip 
        size="small" 
        icon={<CheckIcon />} 
        label="Normal" 
        color="success" 
        variant="outlined"
      />
    </Tooltip>
  );
};

// Row component with expandable details
const BiomarkerRow: React.FC<{
  biomarker: Biomarker;
  onViewHistory?: (biomarker: Biomarker) => void;
  onExplainWithAI?: (biomarker: Biomarker) => void;
  onDeleteBiomarker?: (biomarkerId: number) => void; // Added delete callback
  onToggleFavorite?: (biomarkerName: string) => void; // Added favorite toggle callback
  isFavoriteChecker?: (biomarkerName: string) => boolean; // Function to check if a biomarker is favorite
  isFavoriteLimitReached?: boolean; // Flag if max favorites reached
  onReplaceFavoriteRequest?: (biomarkerName: string) => void; // Callback to trigger replacement modal
  showSource?: boolean;
}> = ({ 
  biomarker, 
  onViewHistory, 
  onExplainWithAI, 
  onDeleteBiomarker, 
  onToggleFavorite,
  isFavoriteChecker,
  isFavoriteLimitReached,
  onReplaceFavoriteRequest,
  showSource = false 
}) => {
  const [open, setOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null); // State for menu anchor
  const theme = useTheme();
  
  // Check if the current biomarker is a favorite
  const isCurrentFavorite = isFavoriteChecker ? isFavoriteChecker(biomarker.name) : false;
  
  // --- Menu Handlers ---
  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleDeleteClick = () => {
    handleMenuClose();
    if (onDeleteBiomarker && biomarker.id) {
      onDeleteBiomarker(biomarker.id);
    } else {
      console.error("Delete handler or biomarker ID missing for:", biomarker);
    }
  };
  
  const handleFavoriteToggle = () => {
    if (!onToggleFavorite || !biomarker.name) return;

    if (isCurrentFavorite) {
      // If it's already a favorite, just toggle (remove)
      onToggleFavorite(biomarker.name);
    } else {
      // If it's not a favorite, check the limit
      if (isFavoriteLimitReached && onReplaceFavoriteRequest) {
        // Limit reached, trigger the replacement request flow
        onReplaceFavoriteRequest(biomarker.name);
      } else {
        // Limit not reached, just toggle (add)
        onToggleFavorite(biomarker.name);
      }
    }
  };
  // --- End Menu Handlers ---
  
  // Format date string helper
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  };
  
  // Get source display name
  const getSourceDisplayName = () => {
    if (!biomarker.fileId) return 'Unknown';
    
    if (biomarker.fileName) {
      // If we have a filename, use that (truncated if needed)
      return biomarker.fileName.length > 15 
        ? `${biomarker.fileName.substring(0, 12)}...` 
        : biomarker.fileName;
    }
    
    // Otherwise use a truncated file ID
    return `Report ${biomarker.fileId.substring(0, 6)}`;
  };
  
  // Debug console logs
  useEffect(() => {
    console.log(`BiomarkerRow: Mounted for ${biomarker.name} (ID: ${biomarker.id})`, {
      hasOnViewHistory: !!onViewHistory,
      hasOnExplainWithAI: !!onExplainWithAI
    });
    
    return () => {
      console.log(`BiomarkerRow: Unmounted for ${biomarker.name} (ID: ${biomarker.id})`);
    };
  }, [biomarker.id, biomarker.name, onViewHistory, onExplainWithAI]);
  
  return (
    <>
      <TableRow 
        sx={{ 
          '& > *': { borderBottom: 'unset' },
          '&:hover': {
            backgroundColor: theme.palette.mode === 'dark' 
              ? 'rgba(255, 255, 255, 0.08)' 
              : 'rgba(0, 0, 0, 0.04)'
          },
          // In history view, highlight rows from current file differently
          ...(showSource && biomarker.fileId && {
            backgroundColor: theme.palette.mode === 'dark' 
              ? 'rgba(0, 100, 255, 0.05)' 
              : 'rgba(0, 100, 255, 0.03)'
          })
        }}
      >
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          {biomarker.name}
        </TableCell>
        <TableCell align="right">{biomarker.value}</TableCell>
        <TableCell align="center">{biomarker.unit}</TableCell>
        <TableCell align="center">{biomarker.referenceRange}</TableCell>
        <TableCell align="center">
          <StatusChip biomarker={biomarker} />
        </TableCell>
        <TableCell align="center">
          <Chip
            label={biomarker.category || 'Uncategorized'}
            size="small"
            sx={{
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.16)'
                : 'rgba(0, 0, 0, 0.08)',
              color: theme.palette.mode === 'dark'
                ? theme.palette.primary.light
                : theme.palette.primary.main
            }}
          />
        </TableCell>
        <TableCell align="center">
          <Chip 
            label={formatDate(biomarker.reportDate || biomarker.date)}
            size="small"
            color={showSource ? "secondary" : "default"}
            variant={showSource ? "filled" : "outlined"}
            sx={{ 
              fontWeight: showSource ? 'medium' : 'normal',
            }}
          />
        </TableCell>
        {showSource && (
          <TableCell align="center">
            {biomarker.fileId ? (
              <Tooltip title={`View source report: ${biomarker.fileName || biomarker.fileId}`}>
                <Chip
                  size="small"
                  label={getSourceDisplayName()}
                  color="primary"
                  variant="outlined"
                  onClick={() => {
                    if (biomarker.fileId) {
                      window.open(`/pdf/${biomarker.fileId}`, '_blank');
                    }
                  }}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: theme.palette.primary.light,
                      color: theme.palette.common.white
                    }
                  }}
                />
              </Tooltip>
            ) : (
              'Unknown'
            )}
          </TableCell>
        )}
        <TableCell align="center">
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'nowrap' }}>
            {onViewHistory && (
              <Tooltip title="View History">
                <IconButton 
                  onClick={() => onViewHistory(biomarker)}
                  size="small"
                  sx={{ 
                    color: theme.palette.mode === 'dark' 
                      ? theme.palette.primary.light
                      : theme.palette.primary.main
                  }}
                >
                  <HistoryIcon />
                </IconButton>
              </Tooltip>
            )}
            {onExplainWithAI && (
              <Tooltip title="Explain with AI">
                <IconButton 
                  onClick={() => onExplainWithAI(biomarker)}
                  size="small"
                  sx={{ 
                    color: theme.palette.mode === 'dark' 
                      ? theme.palette.secondary.light
                      : theme.palette.secondary.main
                  }}
                >
                  <PsychologyIcon />
                </IconButton>
              </Tooltip>
            )}
            {/* 3-Dot Menu */}
            {onDeleteBiomarker && (
              <Tooltip title="More Actions">
                <IconButton
                  aria-label="more actions"
                  aria-controls={`actions-menu-${biomarker.id}`}
                  aria-haspopup="true"
                  onClick={handleMenuClick}
                  size="small"
                >
                  <MoreVertIcon />
                </IconButton>
              </Tooltip>
            )}
            {/* Favorite Toggle Button */}
            {onToggleFavorite && isFavoriteChecker && onReplaceFavoriteRequest && (
              <Tooltip title={isCurrentFavorite ? "Remove from Favorites" : "Add to Favorites"}>
                <IconButton
                  onClick={handleFavoriteToggle}
                  size="small"
                  color={isCurrentFavorite ? "warning" : "default"} // Use warning color for filled star
                >
                  {isCurrentFavorite ? <StarIcon /> : <StarBorderIcon />}
                </IconButton>
              </Tooltip>
            )}
          </Box>
          {/* Actions Menu */}
          <Menu
            id={`actions-menu-${biomarker.id}`}
            anchorEl={anchorEl}
            keepMounted
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={handleDeleteClick} sx={{ color: theme.palette.error.main }}>
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              Delete Entry
            </MenuItem>
            {/* Add other actions here if needed */}
          </Menu>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={showSource ? 10 : 9}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              <Typography variant="h6" gutterBottom component="div">
                Biomarker Details
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" paragraph>
                  <strong>Name:</strong> {biomarker.name}<br />
                  <strong>Value:</strong> {biomarker.value} {biomarker.unit}<br />
                  <strong>Reference Range:</strong> {biomarker.referenceRange || 'Not available'}<br />
                  <strong>Category:</strong> {biomarker.category || 'Uncategorized'}<br />
                  {biomarker.date && (
                    <><strong>Measurement Date:</strong> {formatDate(biomarker.date)}<br /></>
                  )}
                  {biomarker.reportDate && (
                    <><strong>Report Date:</strong> {formatDate(biomarker.reportDate)}<br /></>
                  )}
                  {showSource && biomarker.fileId && (
                    <><strong>Source File:</strong> {biomarker.fileName || biomarker.fileId}<br /></>
                  )}
                  {biomarker.profileId && (
                    <><strong>Profile ID:</strong> {biomarker.profileId}<br /></>
                  )}
                </Typography>
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

// Main Biomarker Table component
const BiomarkerTable: React.FC<BiomarkerTableProps> = ({
  fileId,
  biomarkers = [],
  isLoading = false,
  error = null,
  onRefresh,
  onViewHistory,
  onExplainWithAI,
  onDeleteBiomarker, // Added delete prop
  onToggleFavorite, // Added favorite toggle prop
  isFavoriteChecker, // Added favorite checker prop
  isFavoriteLimitReached, // Added limit flag prop
  onReplaceFavoriteRequest, // Added replace request prop
  showSource = false
}) => {
  const [filteredBiomarkers, setFilteredBiomarkers] = useState<Biomarker[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [orderBy, setOrderBy] = useState<keyof Biomarker>('name');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const theme = useTheme();
  
  // Debug console logs
  console.log('BiomarkerTable: Props received', { 
    biomarkersCount: biomarkers?.length,
    isLoading,
    error,
    hasOnRefresh: !!onRefresh,
    hasOnViewHistory: !!onViewHistory,
    hasOnExplainWithAI: !!onExplainWithAI,
    showSource
  });
  
  // Set up effect to log when component mounts and unmounts
  useEffect(() => {
    console.log('BiomarkerTable: Component mounted');
    
    return () => {
      console.log('BiomarkerTable: Component unmounted');
    };
  }, []);
  
  // Filter and sort biomarkers whenever the dependencies change
  useEffect(() => {
    // Filter biomarkers based on search term
    let filtered = biomarkers.filter(biomarker => 
      biomarker.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (biomarker.category && biomarker.category.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    
    // Sort biomarkers
    filtered = filtered.sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return order === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      // For numeric values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return order === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      // Handle null/undefined values
      if (aValue === undefined && bValue !== undefined) return order === 'asc' ? -1 : 1;
      if (aValue !== undefined && bValue === undefined) return order === 'asc' ? 1 : -1;
      
      return 0;
    });
    
    setFilteredBiomarkers(filtered);
    console.log(`BiomarkerTable: Filtered biomarkers updated - ${filtered.length} items`);
  }, [biomarkers, searchTerm, orderBy, order]);
  
  // Handle sort request
  const handleRequestSort = (property: keyof Biomarker) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };
  
  // Handle search
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0); // Reset to first page when searching
  };
  
  // Pagination handlers
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Table column definitions
  const getColumns = (): Column[] => {
    const baseColumns: Column[] = [
      { id: 'name', label: 'Biomarker', minWidth: 150, sortable: true },
      { id: 'value', label: 'Value', minWidth: 80, align: 'right', sortable: true },
      { id: 'unit', label: 'Unit', minWidth: 60, align: 'center', sortable: true },
      { id: 'referenceRange', label: 'Reference Range', minWidth: 120, align: 'center', sortable: false },
      { id: 'status', label: 'Status', minWidth: 100, align: 'center', sortable: true },
      { id: 'category', label: 'Category', minWidth: 120, align: 'center', sortable: true },
    ];
    
    // In history view, make date column more prominent and add source
    if (showSource) {
      baseColumns.push(
        { id: 'reportDate', label: 'Test Date', minWidth: 120, align: 'center', sortable: true },
        { id: 'fileId', label: 'Source Report', minWidth: 140, align: 'center', sortable: false }
      );
    } else {
      baseColumns.push(
        { id: 'reportDate', label: 'Date', minWidth: 100, align: 'center', sortable: true }
      );
    }
    
    // Add actions column
    baseColumns.push({ id: 'actions', label: 'Actions', minWidth: 100, align: 'center', sortable: false });
    
    return baseColumns;
  };

  const columns = getColumns();
  
  // Empty state when no biomarkers
  if (biomarkers.length === 0 && !isLoading && !error) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No Biomarkers Found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {fileId 
            ? "No biomarkers were extracted from this file. The file may not contain laboratory results."
            : "Please upload a laboratory result PDF to view biomarkers."
          }
        </Typography>
        {onRefresh && (
          <Button
            startIcon={<RefreshIcon />}
            onClick={onRefresh}
            sx={{ mt: 2 }}
          >
            Refresh
          </Button>
        )}
      </Paper>
    );
  }
  
  return (
    <Paper sx={{ width: '100%', overflow: 'hidden', borderRadius: 2, boxShadow: 2 }}>
      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
          {onRefresh && (
            <Button 
              size="small" 
              color="inherit" 
              startIcon={<RefreshIcon />} 
              onClick={onRefresh}
              sx={{ ml: 2 }}
            >
              Retry
            </Button>
          )}
        </Alert>
      )}
      
      {/* Loading state */}
      {isLoading && (
        <Box sx={{ width: '100%' }}>
          <LinearProgress />
        </Box>
      )}
      
      {/* Table toolbar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 2, flexWrap: 'wrap', gap: 1 }}>
        <TextField
          size="small"
          variant="outlined"
          placeholder="Search biomarkers..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ width: { xs: '100%', sm: 250 } }}
        />
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Filter">
            <IconButton>
              <FilterListIcon />
            </IconButton>
          </Tooltip>
          {onRefresh && (
            <Tooltip title="Refresh">
              <IconButton onClick={onRefresh} disabled={isLoading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>
      
      {/* Help text for history view */}
      {showSource && (
        <Box sx={{ px: 2, pb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Showing biomarkers from all lab reports associated with this profile. 
            <strong> Click on the source chip to view the original report.</strong>
          </Typography>
        </Box>
      )}
      
      {/* Table */}
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader aria-label="biomarker table">
          <TableHead>
            <TableRow>
              <TableCell style={{ width: 50 }} /> {/* Empty cell for expand/collapse button */}
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                  sortDirection={orderBy === column.id ? order : false}
                >
                  {column.sortable ? (
                    <TableSortLabel
                      active={orderBy === column.id}
                      direction={orderBy === column.id ? order : 'asc'}
                      onClick={() => column.id !== 'status' && column.sortable && handleRequestSort(column.id as keyof Biomarker)}
                    >
                      {column.label}
                    </TableSortLabel>
                  ) : (
                    column.label
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.length + 1} sx={{ py: 5, textAlign: 'center' }}>
                  <CircularProgress size={40} thickness={5} />
                  <Typography variant="body1" sx={{ mt: 2 }}>
                    Loading biomarker data...
                  </Typography>
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={columns.length + 1} sx={{ py: 5, textAlign: 'center' }}>
                  <Alert 
                    severity="error" 
                    sx={{ 
                      justifyContent: 'center', 
                      '& .MuiAlert-message': { width: 'auto' } 
                    }}
                  >
                    {error}
                  </Alert>
                  {onRefresh && (
                    <Button 
                      startIcon={<RefreshIcon />} 
                      onClick={onRefresh}
                      sx={{ mt: 2 }}
                    >
                      Try Again
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ) : filteredBiomarkers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + 1} sx={{ py: 5, textAlign: 'center' }}>
                  {biomarkers.length === 0 ? (
                    <Typography variant="body1" color="text.secondary">
                      No biomarker data available
                    </Typography>
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      No biomarkers match your search
                    </Typography>
                  )}
                </TableCell>
              </TableRow>
            ) : (
              filteredBiomarkers
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((biomarker) => (
                  <BiomarkerRow 
                    key={biomarker.id} 
                    biomarker={biomarker} 
                    onViewHistory={onViewHistory}
                    onExplainWithAI={onExplainWithAI}
                    onDeleteBiomarker={onDeleteBiomarker} // Pass delete handler down
                    onToggleFavorite={onToggleFavorite} // Pass favorite toggle handler
                    isFavoriteChecker={isFavoriteChecker} // Pass favorite checker
                    isFavoriteLimitReached={isFavoriteLimitReached} // Pass limit flag
                    onReplaceFavoriteRequest={onReplaceFavoriteRequest} // Pass replace request handler
                    showSource={showSource}
                  />
                ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Pagination */}
      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={filteredBiomarkers.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
};

export default BiomarkerTable;
