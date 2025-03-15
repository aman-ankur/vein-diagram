import React, { useState, useMemo } from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Typography, 
  TextField,
  InputAdornment,
  Box,
  IconButton,
  Tooltip,
  Chip,
  TableSortLabel,
  CircularProgress,
  Alert
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { styled } from '@mui/material/styles';

// Define the biomarker interface
export interface Biomarker {
  id: number;
  name: string;
  value: number;
  unit: string;
  original_name?: string;
  original_value?: string;
  original_unit?: string;
  reference_range_low?: number | null;
  reference_range_high?: number | null;
  reference_range_text?: string;
  category?: string;
  is_abnormal?: boolean;
  notes?: string;
}

// Define props for the BiomarkerTable component
interface BiomarkerTableProps {
  biomarkers: Biomarker[];
  isLoading?: boolean;
  error?: string | null;
}

// Styled component for highlighted cells
const HighlightedCell = styled(TableCell)(({ theme }) => ({
  backgroundColor: 'rgba(255, 152, 0, 0.1)',
  fontWeight: 'bold',
  color: theme.palette.warning.dark,
}));

// Sort types
type SortDirection = 'asc' | 'desc';
type SortKey = 'name' | 'value' | 'category';

/**
 * BiomarkerTable component displays biomarker data in a sortable, filterable table
 */
const BiomarkerTable: React.FC<BiomarkerTableProps> = ({ 
  biomarkers, 
  isLoading = false,
  error = null
}) => {
  // State for search term
  const [searchTerm, setSearchTerm] = useState<string>('');
  
  // State for sorting
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [sortBy, setSortBy] = useState<SortKey>('name');
  
  // Handle search input change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };
  
  // Handle sort request
  const handleRequestSort = (property: SortKey) => {
    const isAsc = sortBy === property && sortDirection === 'asc';
    setSortDirection(isAsc ? 'desc' : 'asc');
    setSortBy(property);
  };
  
  // Filter and sort biomarkers based on search term and sort settings
  const filteredAndSortedBiomarkers = useMemo(() => {
    if (!biomarkers) return [];
    
    // First filter based on search term
    const filtered = searchTerm
      ? biomarkers.filter(biomarker => 
          biomarker.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          biomarker.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          biomarker.notes?.toLowerCase().includes(searchTerm.toLowerCase())
        )
      : biomarkers;
    
    // Then sort based on sort settings
    return [...filtered].sort((a, b) => {
      if (sortBy === 'name') {
        return sortDirection === 'asc'
          ? a.name.localeCompare(b.name)
          : b.name.localeCompare(a.name);
      } else if (sortBy === 'value') {
        return sortDirection === 'asc'
          ? a.value - b.value
          : b.value - a.value;
      } else if (sortBy === 'category') {
        const catA = a.category || '';
        const catB = b.category || '';
        return sortDirection === 'asc'
          ? catA.localeCompare(catB)
          : catB.localeCompare(catA);
      }
      return 0;
    });
  }, [biomarkers, searchTerm, sortBy, sortDirection]);
  
  // Render the table with biomarker data
  return (
    <Box sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h2">
          Biomarkers
          {biomarkers.length > 0 && ` (${biomarkers.length})`}
        </Typography>
        
        <TextField
          placeholder="Search biomarkers..."
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ width: '250px' }}
        />
      </Box>
      
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : biomarkers.length === 0 ? (
        <Alert severity="info">
          No biomarker data available. Upload a lab report to see your biomarkers.
        </Alert>
      ) : (
        <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
          <Table stickyHeader aria-label="biomarker table">
            <TableHead>
              <TableRow>
                <TableCell>
                  <TableSortLabel
                    active={sortBy === 'name'}
                    direction={sortBy === 'name' ? sortDirection : 'asc'}
                    onClick={() => handleRequestSort('name')}
                  >
                    Biomarker
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortBy === 'value'}
                    direction={sortBy === 'value' ? sortDirection : 'asc'}
                    onClick={() => handleRequestSort('value')}
                  >
                    Value
                  </TableSortLabel>
                </TableCell>
                <TableCell>Unit</TableCell>
                <TableCell>Reference Range</TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sortBy === 'category'}
                    direction={sortBy === 'category' ? sortDirection : 'asc'}
                    onClick={() => handleRequestSort('category')}
                  >
                    Category
                  </TableSortLabel>
                </TableCell>
                <TableCell>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAndSortedBiomarkers.map((biomarker) => {
                const isAbnormal = biomarker.is_abnormal || 
                  (biomarker.reference_range_low !== null && biomarker.value < biomarker.reference_range_low) ||
                  (biomarker.reference_range_high !== null && biomarker.value > biomarker.reference_range_high);
                
                const Cell = isAbnormal ? HighlightedCell : TableCell;
                
                return (
                  <TableRow key={biomarker.id}>
                    <Cell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {biomarker.name}
                        {biomarker.original_name && biomarker.original_name !== biomarker.name && (
                          <Tooltip title={`Original name: ${biomarker.original_name}`}>
                            <IconButton size="small">
                              <InfoOutlinedIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </Cell>
                    <Cell>
                      {biomarker.value}
                      {biomarker.original_value && biomarker.original_value !== biomarker.value.toString() && (
                        <Tooltip title={`Original value: ${biomarker.original_value}`}>
                          <IconButton size="small">
                            <InfoOutlinedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Cell>
                    <Cell>
                      {biomarker.unit}
                      {biomarker.original_unit && biomarker.original_unit !== biomarker.unit && (
                        <Tooltip title={`Original unit: ${biomarker.original_unit}`}>
                          <IconButton size="small">
                            <InfoOutlinedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Cell>
                    <Cell>
                      {biomarker.reference_range_text || (
                        <>
                          {biomarker.reference_range_low !== null && 
                            biomarker.reference_range_high !== null && 
                              `${biomarker.reference_range_low}-${biomarker.reference_range_high}`}
                          {biomarker.reference_range_low === null && 
                            biomarker.reference_range_high !== null && 
                              `< ${biomarker.reference_range_high}`}
                          {biomarker.reference_range_low !== null && 
                            biomarker.reference_range_high === null && 
                              `> ${biomarker.reference_range_low}`}
                          {biomarker.reference_range_low === null && 
                            biomarker.reference_range_high === null && 
                              ''}
                        </>
                      )}
                    </Cell>
                    <Cell>
                      {biomarker.category ? (
                        <Chip 
                          label={biomarker.category}
                          size="small"
                          sx={{ 
                            bgcolor: getCategoryColor(biomarker.category),
                            color: '#fff'
                          }}
                        />
                      ) : (
                        '-'
                      )}
                    </Cell>
                    <Cell>{biomarker.notes || '-'}</Cell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

// Helper function to get color for category
function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    'Metabolic': '#4CAF50',
    'Lipid': '#2196F3',
    'Vitamin': '#FF9800',
    'Hormone': '#9C27B0',
    'Mineral': '#795548',
    'Blood': '#F44336',
    'Liver': '#FF5722',
    'Kidney': '#673AB7',
    'Thyroid': '#3F51B5',
    'Inflammatory': '#E91E63',
    'Protein': '#009688',
    'Electrolyte': '#8BC34A',
    'Cardiac': '#F44336',
    'Cancer': '#9E9E9E',
    'Other': '#607D8B'
  };
  
  return colors[category] || colors['Other'];
}

export default BiomarkerTable; 