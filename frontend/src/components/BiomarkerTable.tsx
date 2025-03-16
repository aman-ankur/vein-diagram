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
  Button
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
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { Biomarker as BiomarkerType } from '../types/pdf';

// Export the Biomarker type for other components to use
export type Biomarker = BiomarkerType;

interface BiomarkerTableProps {
  fileId?: string;
  biomarkers?: Biomarker[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onViewHistory?: (biomarker: Biomarker) => void;
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
];

// Check if biomarker value is outside reference range
const isOutsideRange = (biomarker: Biomarker): boolean | undefined => {
  if (!biomarker.referenceRange) return undefined;
  
  // Handle different reference range formats
  const rangeStr = biomarker.referenceRange;
  
  // Handle range with hyphen (e.g., "70-99")
  if (rangeStr.includes('-')) {
    const [min, max] = rangeStr.split('-').map(Number);
    if (!isNaN(min) && !isNaN(max)) {
      return biomarker.value < min || biomarker.value > max;
    }
  }
  
  // Handle range with comparison operators (e.g., "<5.0" or ">3.5")
  if (rangeStr.includes('<')) {
    const maxValue = parseFloat(rangeStr.replace('<', '').trim());
    if (!isNaN(maxValue)) {
      return biomarker.value >= maxValue;
    }
  }
  
  if (rangeStr.includes('>')) {
    const minValue = parseFloat(rangeStr.replace('>', '').trim());
    if (!isNaN(minValue)) {
      return biomarker.value <= minValue;
    }
  }
  
  // Could not determine
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
}> = ({ biomarker, onViewHistory }) => {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  
  const handleViewHistory = () => {
    if (onViewHistory) {
      onViewHistory(biomarker);
    }
  };
  
  return (
    <>
      <TableRow 
        hover 
        sx={{ 
          '& > *': { borderBottom: 'unset' }, 
          cursor: 'pointer',
          '&:hover': {
            backgroundColor: alpha(theme.palette.primary.main, 0.04),
          }
        }}
        onClick={() => setOpen(!open)}
      >
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton
              aria-label="expand row"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                setOpen(!open);
              }}
            >
              {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {biomarker.name}
            </Typography>
          </Box>
        </TableCell>
        <TableCell align="right">
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {biomarker.value}
          </Typography>
        </TableCell>
        <TableCell align="center">{biomarker.unit}</TableCell>
        <TableCell align="center">{biomarker.referenceRange || 'Not available'}</TableCell>
        <TableCell align="center">
          <StatusChip biomarker={biomarker} />
        </TableCell>
        <TableCell align="center">
          {biomarker.category ? (
            <Chip 
              size="small" 
              label={biomarker.category} 
              variant="outlined"
              color="primary"
            />
          ) : (
            'Uncategorized'
          )}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
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
                
                {onViewHistory && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<TimelineIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewHistory();
                    }}
                    sx={{ mt: 1 }}
                  >
                    View History
                  </Button>
                )}
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
  onViewHistory
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
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
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
      <TableContainer sx={{ maxHeight: 440 }}>
        <Table stickyHeader aria-label="biomarkers table">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                  sortDirection={orderBy === column.id ? order : false}
                  sx={{ 
                    fontWeight: 'bold',
                    cursor: column.sortable ? 'pointer' : 'default',
                    '&:hover': {
                      backgroundColor: column.sortable ? 'rgba(0, 0, 0, 0.04)' : 'inherit',
                    },
                  }}
                  onClick={() => column.sortable && handleRequestSort(column.id as keyof Biomarker)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: column.align === 'right' ? 'flex-end' : (column.align === 'center' ? 'center' : 'flex-start') }}>
                    {column.label}
                    {orderBy === column.id ? (
                      order === 'asc' ? <ArrowUpwardIcon fontSize="small" sx={{ ml: 0.5 }} /> : <ArrowDownwardIcon fontSize="small" sx={{ ml: 0.5 }} />
                    ) : null}
                  </Box>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredBiomarkers
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((biomarker, index) => (
                <BiomarkerRow 
                  key={`${biomarker.name}-${index}`} 
                  biomarker={biomarker}
                  onViewHistory={onViewHistory}
                />
              ))}
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