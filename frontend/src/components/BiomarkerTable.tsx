import React, { useState } from 'react'; // Removed useEffect
import {
  Box,
  // Paper removed - unused
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
  // CircularProgress removed - unused
  // Avatar removed - unused
  Grid // Added Grid import
} from '@mui/material';
import {
  Search as SearchIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Refresh as RefreshIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  // FilterListIcon removed - unused
  // ErrorIcon removed - unused
  Warning as WarningIcon, // Keep WarningIcon as it's used in StatusChip
  // CheckIcon removed - unused
  // TimelineIcon removed - unused
  History as HistoryIcon,
  Psychology as PsychologyIcon,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  StarBorder as StarBorderIcon,
  Star as StarIcon
} from '@mui/icons-material';
import { Menu, MenuItem, keyframes } from '@mui/material'; // Removed SvgIcon import, Added keyframes
import type { Biomarker } from '../types/biomarker';

// Define pulse animation
const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
`;

// Re-export the Biomarker type
export type { Biomarker };

interface BiomarkerTableProps {
  // fileId?: string; // Removed unused prop
  biomarkers?: Biomarker[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onViewHistory?: (biomarker: Biomarker) => void;
  onExplainWithAI?: (biomarker: Biomarker) => void;
  onDeleteBiomarker?: (biomarkerId: number) => void;
  onToggleFavorite?: (biomarkerName: string) => void;
  isFavoriteChecker?: (biomarkerName: string) => boolean;
  isFavoriteLimitReached?: boolean;
  onReplaceFavoriteRequest?: (biomarkerName: string) => void;
  showSource?: boolean;
}

// Interface for the column definition
interface Column {
  id: keyof Biomarker | 'status' | 'actions';
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

// Updated StatusChip component with more subtle design
const StatusChip: React.FC<{ biomarker: Biomarker }> = ({ biomarker }) => {
  const theme = useTheme();
  const isAbnormal = biomarker.isAbnormal !== undefined
    ? biomarker.isAbnormal
    : isOutsideRange(biomarker);

  if (isAbnormal === undefined) {
    return (
      <Chip
        size="small"
        label="Unknown"
        sx={{
          backgroundColor: alpha(theme.palette.grey[500], 0.12),
          color: theme.palette.text.secondary,
          fontWeight: 500,
          borderRadius: '8px',
          border: 'none'
        }}
      />
    );
  }

  return isAbnormal ? (
    <Tooltip title="Outside normal range">
      <Chip
        size="small"
        label="Abnormal"
        icon={<WarningIcon sx={{ fontSize: '1rem', color: theme.palette.error.main }} />} // Ensure icon is used if needed
        sx={{
          backgroundColor: alpha(theme.palette.error.main, 0.12),
          color: theme.palette.error.main,
          fontWeight: 500,
          borderRadius: '8px',
          border: 'none'
        }}
      />
    </Tooltip>
  ) : (
    <Tooltip title="Within normal range">
      <Chip
        size="small"
        label="Normal"
        sx={{
          backgroundColor: alpha(theme.palette.success.main, 0.12),
          color: theme.palette.success.main,
          fontWeight: 500,
          borderRadius: '8px',
          border: 'none'
        }}
      />
    </Tooltip>
  );
};

// Enhanced action button
const ActionIconButton: React.FC<{
  icon: React.ReactNode;
  tooltip: string;
  onClick: () => void;
  color?: string;
}> = ({ icon, tooltip, onClick, color }) => {
  const theme = useTheme();

  return (
    <Tooltip title={tooltip}>
      <IconButton
        size="small"
        onClick={onClick}
        sx={{
          color: color || theme.palette.primary.main,
          backgroundColor: alpha(color || theme.palette.primary.main, 0.08),
          '&:hover': {
            backgroundColor: alpha(color || theme.palette.primary.main, 0.15),
          },
          mr: 1,
          width: 36,
          height: 36
        }}
      >
        {icon}
      </IconButton>
    </Tooltip>
  );
};

// Updated BiomarkerRow component
const BiomarkerRow: React.FC<{
  biomarker: Biomarker;
  onViewHistory?: (biomarker: Biomarker) => void;
  onExplainWithAI?: (biomarker: Biomarker) => void;
  onDeleteBiomarker?: (biomarkerId: number) => void;
  onToggleFavorite?: (biomarkerName: string) => void;
  isFavoriteChecker?: (biomarkerName: string) => boolean;
  isFavoriteLimitReached?: boolean;
  onReplaceFavoriteRequest?: (biomarkerName: string) => void;
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
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);
  const theme = useTheme();

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
    }
  };

  const handleFavoriteToggle = () => {
    handleMenuClose();
    if (onToggleFavorite) {
      if (isFavoriteChecker && !isFavoriteChecker(biomarker.name) && isFavoriteLimitReached) {
        // Handle the limit reached case
        if (onReplaceFavoriteRequest) {
          onReplaceFavoriteRequest(biomarker.name);
        }
      } else {
        onToggleFavorite(biomarker.name);
      }
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const getSourceDisplayName = () => {
    if (!biomarker.fileName) return 'Unknown';

    // Just return the filename without the path and extension
    const filename = biomarker.fileName.split('/').pop() || '';
    return filename.replace(/\.[^.]+$/, '');
  };

  const isFavorite = isFavoriteChecker ? isFavoriteChecker(biomarker.name) : false;

  return (
    <>
      <TableRow
        sx={{
          '&:hover': {
            backgroundColor: alpha(theme.palette.primary.main, 0.04),
          },
          cursor: 'pointer',
          backgroundColor: open ? alpha(theme.palette.primary.main, 0.03) : 'transparent',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}
      >
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
            sx={{ color: theme.palette.text.secondary }}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>

        <TableCell component="th" scope="row">
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column' }}>
              <Typography variant="body2" fontWeight={500}>
                {biomarker.name}
              </Typography>
              {/* Removed description display */}
            </Box>
          </Box>
        </TableCell>

        <TableCell align="right">
          <Typography variant="body2" fontWeight={600}>
            {typeof biomarker.value === 'number' ? biomarker.value.toFixed(2) : biomarker.value}
          </Typography>
        </TableCell>

        <TableCell align="center">
          <Typography variant="body2" color="text.secondary">
            {biomarker.unit || '-'}
          </Typography>
        </TableCell>

        <TableCell align="center">
          <Typography variant="body2" color="text.secondary">
            {biomarker.referenceRange || (
              biomarker.reference_range_low !== null && biomarker.reference_range_high !== null
                ? `${biomarker.reference_range_low} - ${biomarker.reference_range_high}`
                : '-'
            )}
          </Typography>
        </TableCell>

        <TableCell align="center">
          <StatusChip biomarker={biomarker} />
        </TableCell>

        <TableCell align="center">
          <Chip
            label={biomarker.category || 'General'}
            size="small"
            sx={{
              backgroundColor: alpha(theme.palette.primary.main, 0.08),
              color: theme.palette.primary.main,
              fontWeight: 500,
              borderRadius: '8px',
              border: 'none'
            }}
          />
        </TableCell>

        <TableCell align="center">
          <Typography variant="body2" color="text.secondary">
            {biomarker.reportDate ? formatDate(biomarker.reportDate) : '-'}
          </Typography>
        </TableCell>

        <TableCell align="center">
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            {/* Favorite Toggle Button */}
            {onToggleFavorite && isFavoriteChecker && (
              <Tooltip title={isFavorite ? "Remove from favorites" : "Add to favorites"}>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent row collapse/expand
                    handleFavoriteToggle();
                  }}
                  className="opacity-60 hover:opacity-100 transition-opacity duration-200" // Added Tailwind classes
                  sx={{ // Kept color and margin in sx
                    color: isFavorite ? theme.palette.warning.main : theme.palette.text.disabled,
                    mr: 0.5,
                    '&:hover': {
                      backgroundColor: 'transparent' // Prevent hover background if not desired
                    }
                  }}
                >
                  {isFavorite ? <StarIcon fontSize="small" /> : <StarBorderIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            )}

            {/* AI Explain Button */}
            {onExplainWithAI && (
              <Tooltip title="Explain with AI">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent row collapse/expand
                    onExplainWithAI(biomarker);
                  }}
                  className="animate-pulse shadow-md shadow-secondary-main/40 rounded-full" // Reverted to animate-pulse, kept shadow
                  sx={{ // Kept color, margin, and hover in sx
                    color: theme.palette.secondary.main,
                    opacity: 1, // Ensure full opacity
                    mr: 0.5,
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.secondary.main, 0.1) // Optional hover effect
                    }
                    }}
                  >
                    <PsychologyIcon sx={{ fontSize: '1.2rem' }} /> {/* Increased size */}
                  </IconButton>
                </Tooltip>
            )}

            {/* More Actions Menu (including Delete) */}
            {(onDeleteBiomarker || onViewHistory) && ( // Show if delete or history action exists
              <>
                <Tooltip title="More actions">
                  <IconButton
                    aria-label="more actions"
                    id={`actions-button-${biomarker.id}`}
                    aria-controls={menuOpen ? `actions-menu-${biomarker.id}` : undefined}
                    aria-expanded={menuOpen ? 'true' : undefined}
                    aria-haspopup="true"
                    onClick={(e) => {
                      e.stopPropagation(); // Prevent row collapse/expand
                      handleMenuClick(e);
                    }}
                    size="small"
                    className="opacity-60 hover:opacity-100 transition-opacity duration-200" // Added Tailwind classes
                    sx={{ // Kept color in sx
                      color: theme.palette.text.secondary,
                    }}
                  >
                    <MoreVertIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Menu
                  id={`actions-menu-${biomarker.id}`}
                  MenuListProps={{ 'aria-labelledby': `actions-button-${biomarker.id}` }}
                  anchorEl={anchorEl}
                  open={menuOpen}
                  onClose={(e: React.MouseEvent<HTMLElement>) => {
                     e.stopPropagation(); // Prevent row collapse/expand
                     handleMenuClose();
                  }}
                  onClick={(e) => e.stopPropagation()} // Prevent row collapse/expand when clicking menu
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                >
                  {onViewHistory && (
                     <MenuItem onClick={() => { /* Remove event parameter 'e' */ handleMenuClose(); onViewHistory(biomarker); }}>
                       <HistoryIcon fontSize="small" sx={{ mr: 1 }} /> View History
                     </MenuItem>
                  )}
                  {onDeleteBiomarker && biomarker.id && (
                    <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
                      <DeleteIcon fontSize="small" sx={{ mr: 1 }} /> Delete Entry
                    </MenuItem>
                  )}
                </Menu>
              </>
            )}
          </Box>
        </TableCell>
      </TableRow>

      <TableRow>
        <TableCell colSpan={9} sx={{ py: 0, borderBottom: open ? `1px solid ${alpha(theme.palette.divider, 0.1)}` : 'none' }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{
              py: 3,
              px: 2,
              backgroundColor: alpha(theme.palette.background.paper, 0.4),
              borderRadius: 2
            }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom component="div" color="primary.main">
                    Biomarker Details
                  </Typography>
                  <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 2,
                    '& .detail-label': {
                      color: theme.palette.text.secondary,
                      fontSize: '0.875rem'
                    },
                    '& .detail-value': {
                      fontWeight: 500,
                      fontSize: '0.875rem'
                    }
                  }}>
                    <Typography className="detail-label">Name:</Typography>
                    <Typography className="detail-value">{biomarker.name}</Typography>

                    <Typography className="detail-label">Category:</Typography>
                    <Typography className="detail-value">{biomarker.category || 'General'}</Typography>

                    <Typography className="detail-label">Value:</Typography>
                    <Typography className="detail-value">
                      {typeof biomarker.value === 'number' ? biomarker.value.toFixed(2) : biomarker.value} {biomarker.unit || ''}
                    </Typography>

                    <Typography className="detail-label">Status:</Typography>
                    <Typography className="detail-value">
                      <StatusChip biomarker={biomarker} />
                    </Typography>

                    {biomarker.reportDate && (
                      <>
                        <Typography className="detail-label">Report Date:</Typography>
                        <Typography className="detail-value">{formatDate(biomarker.reportDate)}</Typography>
                      </>
                    )}

                    {showSource && biomarker.fileName && (
                      <>
                        <Typography className="detail-label">Source:</Typography>
                        <Typography className="detail-value">{getSourceDisplayName()}</Typography>
                      </>
                    )}
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  {/* Removed description section */}

                  <Box sx={{
                    mt: 0, // Removed dependency on description
                    display: 'flex',
                    gap: 1,
                    flexWrap: 'wrap',
                    justifyContent: { xs: 'center', md: 'flex-start' }
                  }}>
                    {onExplainWithAI && (
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<PsychologyIcon />}
                        onClick={() => onExplainWithAI(biomarker)}
                        sx={{
                          borderRadius: '10px',
                          textTransform: 'none',
                          bgcolor: theme.palette.secondary.main,
                          '&:hover': {
                            bgcolor: theme.palette.secondary.dark
                          }
                        }}
                      >
                        Explain with AI
                      </Button>
                    )}

                    {onViewHistory && (
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<HistoryIcon />}
                        onClick={() => onViewHistory(biomarker)}
                        sx={{
                          borderRadius: '10px',
                          textTransform: 'none',
                          borderColor: alpha(theme.palette.primary.main, 0.5)
                        }}
                      >
                        View History
                      </Button>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

// Updated BiomarkerTable component
const BiomarkerTable: React.FC<BiomarkerTableProps> = ({
  // fileId, // Removed unused prop
  biomarkers = [],
  isLoading = false,
  error = null,
  onRefresh,
  onViewHistory,
  onExplainWithAI,
  onDeleteBiomarker,
  onToggleFavorite,
  isFavoriteChecker,
  isFavoriteLimitReached,
  onReplaceFavoriteRequest,
  showSource = false
}) => {
  const theme = useTheme();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  // Allow orderBy to be a key of Biomarker OR 'status'
  const [orderBy, setOrderBy] = useState<keyof Biomarker | 'status'>('name');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');

  const filteredBiomarkers = biomarkers.filter((biomarker) => {
    const searchFields = [
      biomarker.name,
      biomarker.category,
      // Removed description from search
      String(biomarker.value),
      biomarker.unit
    ].filter(Boolean);

    return searchFields.some(field =>
      field && field.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const sortedBiomarkers = [...filteredBiomarkers].sort((a, b) => {
    const isAsc = order === 'asc';

    // Handle special case for sorting by 'status'
    if (orderBy === 'status') {
      const aStatus = a.isAbnormal || isOutsideRange(a) || false;
      const bStatus = b.isAbnormal || isOutsideRange(b) || false;
      return isAsc ? (aStatus === bStatus ? 0 : aStatus ? 1 : -1) : (aStatus === bStatus ? 0 : aStatus ? -1 : 1);
    }

    // Default sorting for other fields (ensure orderBy is a valid key here)
    const validOrderBy = orderBy as keyof Biomarker; // Cast because we handled 'status'
    const aValue = a[validOrderBy] as string | number;
    const bValue = b[validOrderBy] as string | number;

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return isAsc ? aValue - bValue : bValue - aValue;
    }

    const aString = String(aValue || '').toLowerCase();
    const bString = String(bValue || '').toLowerCase();

    return isAsc ? aString.localeCompare(bString) : bString.localeCompare(aString);
  });

  const handleRequestSort = (property: keyof Biomarker) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    // Allow setting orderBy to 'status'
    setOrderBy(property as keyof Biomarker | 'status');
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  const handleChangePage = (_event: unknown, newPage: number) => { // Removed unused event param
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => { // Kept event param as it's used
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Simplified getColumns as 'viewHistory' was never a column id
  const getColumns = (): Column[] => {
    return columns;
  };

  const paginatedBiomarkers = sortedBiomarkers.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box>
      {/* Search, Filter, Refresh Bar */}
      <Box sx={{
        p: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 2
      }}>
        <TextField
          variant="outlined"
          size="small"
          placeholder="Search biomarkers..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
            sx: {
              borderRadius: '10px',
              bgcolor: alpha(theme.palette.background.paper, 0.5),
              '& fieldset': {
                borderColor: alpha(theme.palette.divider, 0.2),
              }
            }
          }}
          sx={{ minWidth: 250 }}
        />

        <Box sx={{ display: 'flex', gap: 1 }}>
          {onRefresh && (
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={onRefresh}
              size="small"
              sx={{
                borderRadius: '10px',
                textTransform: 'none',
                borderColor: alpha(theme.palette.primary.main, 0.3),
                color: theme.palette.primary.main
              }}
            >
              Refresh
            </Button>
          )}
        </Box>
      </Box>

      {isLoading && (
        <LinearProgress sx={{ height: 2 }} />
      )}

      {error && (
        <Alert
          severity="error"
          sx={{
            mx: 2,
            mt: 1,
            mb: 2,
            borderRadius: '10px'
          }}
        >
          {error}
        </Alert>
      )}

      {!isLoading && biomarkers.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 5 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No biomarkers found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your filters or upload a new report.
          </Typography>
        </Box>
      ) : (
        <>
          <TableContainer>
            <Table aria-label="biomarkers table" size="medium">
              <TableHead>
                <TableRow sx={{ '& th': { borderBottom: `2px solid ${alpha(theme.palette.divider, 0.1)}` } }}>
                  <TableCell sx={{ width: 48 }}></TableCell>

                  {getColumns().map((column) => (
                    <TableCell
                      key={column.id}
                      align={column.align}
                      style={{ minWidth: column.minWidth }}
                      sortDirection={orderBy === column.id ? order : false}
                      sx={{
                        color: theme.palette.text.secondary,
                        fontWeight: 600,
                        fontSize: '0.82rem'
                      }}
                    >
                      {column.sortable ? (
                        <TableSortLabel
                          active={orderBy === column.id}
                          direction={orderBy === column.id ? order : 'asc'}
                          onClick={() => handleRequestSort(column.id as keyof Biomarker)}
                          IconComponent={order === 'asc' ? ArrowUpwardIcon : ArrowDownwardIcon}
                          sx={{
                            '& .MuiTableSortLabel-icon': {
                              fontSize: '0.9rem',
                              opacity: 0.5
                            }
                          }}
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
                {paginatedBiomarkers.length > 0 ? (
                  paginatedBiomarkers.map((biomarker) => (
                    <BiomarkerRow
                      key={`${biomarker.name}-${biomarker.value}-${biomarker.id || Math.random()}`}
                      biomarker={biomarker}
                      onViewHistory={onViewHistory}
                      onExplainWithAI={onExplainWithAI}
                      onDeleteBiomarker={onDeleteBiomarker}
                      onToggleFavorite={onToggleFavorite}
                      isFavoriteChecker={isFavoriteChecker}
                      isFavoriteLimitReached={isFavoriteLimitReached}
                      onReplaceFavoriteRequest={onReplaceFavoriteRequest}
                      showSource={showSource}
                    />
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                      <Typography variant="body1" color="text.secondary">
                        No matching biomarkers found
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={filteredBiomarkers.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            sx={{
              borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                fontSize: '0.875rem',
                color: theme.palette.text.secondary
              },
              '& .MuiSelect-outlined': {
                borderRadius: '8px'
              }
            }}
          />
        </>
      )}
    </Box>
  );
};

export default BiomarkerTable;
