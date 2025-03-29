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
  Psychology as PsychologyIcon
} from '@mui/icons-material';
import { Biomarker as BiomarkerType } from '../types/pdf';
import { SvgIcon } from '@mui/material';

// Export the Biomarker type for other components to use
export type Biomarker = BiomarkerType;

interface BiomarkerTableProps {
  fileId?: string;
  biomarkers?: Biomarker[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onViewHistory?: (biomarker: Biomarker) => void;
  onExplainWithAI?: (biomarker: Biomarker) => void;
}

// Interface for the column definition
interface Column {
  id: keyof Biomarker | 'status';
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
  { id: 'actions', label: 'Actions', minWidth: 150, align: 'center' },
];

// Function to determine if a value is outside the reference range
const isOutsideRange = (biomarker: Biomarker): boolean | undefined => {
  // If isAbnormal is set, use that value
  if (biomarker.isAbnormal !== undefined) {
    return biomarker.isAbnormal;
  }
  
  // If we have numeric reference range bounds, use those
  if (biomarker.reference_range_low !== null && biomarker.reference_range_high !== null) {
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
}> = ({ biomarker, onViewHistory, onExplainWithAI }) => {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  
  return (
    <>
      <TableRow 
        sx={{ 
          '& > *': { borderBottom: 'unset' },
          '&:hover': {
            backgroundColor: theme.palette.mode === 'dark' 
              ? 'rgba(255, 255, 255, 0.08)' 
              : 'rgba(0, 0, 0, 0.04)'
          }
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
            <Button
              onClick={() => {
                console.log('Explain button clicked for biomarker:', biomarker);
                if (onExplainWithAI) {
                  console.log('Calling onExplainWithAI handler...');
                  onExplainWithAI(biomarker);
                } else {
                  console.warn('onExplainWithAI handler is not defined');
                }
              }}
              startIcon={<PsychologyIcon />}
              variant="contained"
              size="small"
              sx={{
                backgroundColor: theme.palette.primary.main,
                color: '#fff',
                whiteSpace: 'nowrap',
                minWidth: 'auto',
                px: 1,
                '&:hover': {
                  backgroundColor: theme.palette.primary.dark,
                }
              }}
            >
              Explain
            </Button>
          </Box>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
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
                    <><strong>Measurement Date:</strong> {new Date(biomarker.date).toLocaleDateString()}<br /></>
                  )}
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                  {onViewHistory && (
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<TimelineIcon />}
                      onClick={() => onViewHistory(biomarker)}
                    >
                      View History
                    </Button>
                  )}
                  
                  <Button
                    variant="contained"
                    size="medium"
                    color="primary"
                    startIcon={<PsychologyIcon />}
                    onClick={() => {
                      console.log('Expanded Explain button clicked for biomarker:', biomarker);
                      if (onExplainWithAI) {
                        console.log('Calling onExplainWithAI handler from expanded view...');
                        onExplainWithAI(biomarker);
                      } else {
                        console.warn('onExplainWithAI handler is not defined');
                      }
                    }}
                  >
                    Explain with AI
                  </Button>
                </Box>
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
  onExplainWithAI
}) => {
  const [filteredBiomarkers, setFilteredBiomarkers] = useState<Biomarker[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [orderBy, setOrderBy] = useState<keyof Biomarker>('name');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
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