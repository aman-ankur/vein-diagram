import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Box,
  useTheme,
  alpha,
} from '@mui/material';
import { ProcessedFavoriteData } from '../utils/biomarkerUtils';
import { format } from 'date-fns';
import { DATE_FORMAT } from '../config';
import { ResponsiveContainer, LineChart, Line, Tooltip as RechartsTooltip } from 'recharts';

// --- Icons ---
import StarBorderIcon from '@mui/icons-material/StarBorder';
import StarIcon from '@mui/icons-material/Star';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import RemoveIcon from '@mui/icons-material/Remove'; // Stable trend
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'; // Unknown trend/status
import ScienceIcon from '@mui/icons-material/Science'; // Generic biomarker icon
import BloodtypeIcon from '@mui/icons-material/Bloodtype'; // Example: Hematology
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart'; // Example: Cardiovascular
import BubbleChartIcon from '@mui/icons-material/BubbleChart'; // Example: Hormones/Endocrine
import WaterDropIcon from '@mui/icons-material/WaterDrop'; // Example: Lipids
import CloseIcon from '@mui/icons-material/Close'; // Icon for delete button

interface BiomarkerTileProps {
  biomarkerData: ProcessedFavoriteData;
  isFavorite: boolean; // Still needed to show star state
  onToggleFavorite: (biomarkerName: string) => void; // Can be used by star if needed, or removed if delete replaces it
  onDeleteFavorite: (biomarkerName: string) => void; // Callback specifically for deletion
  onClickTile?: (biomarkerName: string) => void; // For expanding details
}

// Helper function to get status colors
const getStatusStyle = (status: string | null | undefined, theme: any) => {
  switch (status) {
    case 'Normal':
      return {
        backgroundColor: alpha(theme.palette.success.main, 0.15),
        color: theme.palette.mode === 'dark' ? theme.palette.success.light : theme.palette.success.dark,
        borderColor: alpha(theme.palette.success.main, 0.3),
      };
    case 'Abnormal':
      return {
        backgroundColor: alpha(theme.palette.error.main, 0.15),
        color: theme.palette.mode === 'dark' ? theme.palette.error.light : theme.palette.error.dark,
        borderColor: alpha(theme.palette.error.main, 0.3),
      };
    case 'Borderline': // Assuming 'Borderline' might be a status
       return {
        backgroundColor: alpha(theme.palette.warning.main, 0.15),
        color: theme.palette.mode === 'dark' ? theme.palette.warning.light : theme.palette.warning.dark,
        borderColor: alpha(theme.palette.warning.main, 0.3),
      };
    default: // Unknown or null
      return {
        backgroundColor: alpha(theme.palette.grey[500], 0.1),
        color: theme.palette.text.secondary,
        borderColor: alpha(theme.palette.grey[500], 0.2),
      };
  }
};

// Helper function to get trend icon and color
const getTrendInfo = (trend: string | null | undefined, theme: any) => {
  switch (trend) {
    case 'Up':
      // Consider if 'Up' is good or bad based on biomarker context? For now, using warning.
      return { Icon: ArrowUpwardIcon, color: theme.palette.warning.main }; 
    case 'Down':
      // Consider if 'Down' is good or bad? For now, using info.
      return { Icon: ArrowDownwardIcon, color: theme.palette.info.main }; 
    case 'Stable':
      return { Icon: RemoveIcon, color: theme.palette.text.secondary };
    default:
      return { Icon: HelpOutlineIcon, color: theme.palette.text.disabled };
  }
};

// Helper for biomarker category icons (expand this mapping)
const getBiomarkerIcon = (category: string | undefined) => {
  switch (category?.toLowerCase()) {
    case 'hematology': return <BloodtypeIcon fontSize="inherit" />;
    case 'cardiovascular':
    case 'lipids': return <WaterDropIcon fontSize="inherit" />;
    case 'hormones':
    case 'endocrine': return <BubbleChartIcon fontSize="inherit" />;
    // Add more specific categories as needed
    default: return <ScienceIcon fontSize="inherit" />; // Generic fallback
  }
};

const BiomarkerTile: React.FC<BiomarkerTileProps> = ({
  biomarkerData,
  isFavorite, // Keep isFavorite to show star status if desired, or remove if delete replaces toggle
  onToggleFavorite, // Keep if star still toggles, or remove
  onDeleteFavorite, // Add delete handler
  onClickTile = (name) => console.log(`Tile clicked: ${name}`),
}) => {
  const theme = useTheme();
  const {
    name,
    latestValue,
    latestUnit,
    latestDate,
    status,
    trend,
    history = [],
    category, // Assuming category is available in ProcessedFavoriteData
  } = biomarkerData;

  const statusStyle = getStatusStyle(status, theme);
  const { Icon: TrendIcon, color: trendColor } = getTrendInfo(trend, theme);
  const CategoryIcon = getBiomarkerIcon(category);

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click when toggling favorite
    onToggleFavorite(name);
  };
  
  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click when deleting
    onDeleteFavorite(name);
  };

  const handleTileClick = () => {
    onClickTile(name);
  };

  const hasValue = latestValue !== null && latestValue !== undefined;
  const showSparkline = history && history.length > 1;

  // Define gradient based on theme mode
  const gradient = theme.palette.mode === 'dark'
    ? `linear-gradient(145deg, ${alpha(theme.palette.grey[800], 0.4)}, ${alpha(theme.palette.grey[900], 0.6)})`
    : `linear-gradient(145deg, ${alpha(theme.palette.common.white, 0.1)}, ${alpha(theme.palette.grey[100], 0.3)})`; // Lighter gradient for light mode

  // Glow effect for abnormal status
  const glowEffect = status === 'Abnormal'
    ? `0 0 12px ${alpha(theme.palette.error.main, 0.5)}`
    : 'none';

  return (
    <Card
      elevation={0} // Use elevation 0 and manage shadow via sx for glow effect
      sx={{
        p: 2, // 16px padding
        borderRadius: '12px',
        border: `1px solid ${alpha(theme.palette.divider, 0.15)}`,
        background: gradient,
        position: 'relative',
        overflow: 'hidden',
        height: '100%', // Ensure card takes full height of grid item
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
        boxShadow: status === 'Abnormal' ? glowEffect : theme.shadows[1], // Initial shadow + glow
        cursor: 'pointer',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: status === 'Abnormal'
            ? `${glowEffect}, ${theme.shadows[4]}` // Combine glow + hover shadow
            : theme.shadows[4], // Elevate shadow on hover
        },
        // Glassy/Frosted Effect Overlay
        // position: 'relative', // REMOVED DUPLICATE - Already set above
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: alpha(theme.palette.background.paper, 0.1), // 10% opacity overlay
          backdropFilter: 'blur(8px)', // Adjust blur amount as needed
          zIndex: 0,
          borderRadius: 'inherit', // Inherit border radius
          pointerEvents: 'none', // Allow clicks to pass through
        },
      }}
      onClick={handleTileClick} // Make the whole card clickable
    >
      {/* Content needs to be above the ::before pseudo-element */}
      <CardContent sx={{ position: 'relative', zIndex: 1, p: 0, flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header: Icon, Name, Favorite Star */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: theme.palette.text.secondary, minWidth: 0 /* Prevent flex item from overflowing */ }}>
             <Box sx={{ fontSize: '18px', flexShrink: 0 }}>{CategoryIcon}</Box>
             <Typography
               variant="h6"
               component="h3"
               sx={{
                 fontSize: '18px', // 18px font size
                 fontWeight: 600, // Semi-bold
                 color: theme.palette.text.primary,
                 overflow: 'hidden',
                 whiteSpace: 'nowrap',
                 textOverflow: 'ellipsis',
               }}
               title={name}
             >
               {name}
             </Typography>
          </Box>
          <IconButton
            size="small"
            onClick={handleFavoriteClick}
            aria-label={isFavorite ? `Remove ${name} from favorites` : `Add ${name} to favorites`}
            sx={{
              color: isFavorite ? theme.palette.warning.main : theme.palette.action.active,
              transition: 'transform 0.2s ease-in-out, color 0.2s ease-in-out',
              flexShrink: 0, // Prevent star from shrinking
              '&:hover': {
                transform: 'scale(1.2)',
                color: theme.palette.warning.light,
              },
            }}
          >
            {isFavorite ? <StarIcon fontSize="inherit" /> : <StarBorderIcon fontSize="inherit" />}
          </IconButton>
        </Box>
        
        {/* Delete Button - Bottom Right Corner */}
        <IconButton
          size="small"
          onClick={handleDeleteClick} // Ensure this calls the correct prop handler
          aria-label={`Remove ${name} from favorites`}
          sx={{
            position: 'absolute', 
            bottom: 4, // Position near bottom
            right: 4,  // Position near right
            zIndex: 10, 
            color: alpha(theme.palette.text.secondary, 0.6), 
            backgroundColor: alpha(theme.palette.background.paper, 0.6), 
            padding: '2px', 
            '&:hover': {
              color: theme.palette.error.dark, // Darker red on hover
              backgroundColor: alpha(theme.palette.error.light, 0.3), // Slightly more opaque hover background
            },
          }}
        >
          <CloseIcon sx={{ fontSize: '14px' }} /> 
        </IconButton>


        {/* Body: Value, Units, Trend */}
        <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1, minHeight: '32px' /* Ensure space even if no value */ }}>
          {hasValue ? (
            <>
              <Typography
                variant="h4"
                component="span"
                sx={{
                  fontSize: '24px', // Prominent value
                  fontWeight: 700,
                  color: theme.palette.text.primary,
                  mr: 0.5,
                  lineHeight: 1.1, // Adjust line height for large font
                }}
              >
                {latestValue}
              </Typography>
              <Typography
                variant="body2"
                component="span"
                sx={{
                  fontSize: '14px', // Smaller units
                  color: theme.palette.text.secondary,
                  mr: 1,
                }}
              >
                {latestUnit}
              </Typography>
              <TrendIcon sx={{ fontSize: '16px', color: trendColor }} titleAccess={`Trend: ${trend || 'Unknown'}`} />
            </>
          ) : (
            <Typography variant="body2" sx={{ color: theme.palette.text.disabled, fontStyle: 'italic' }}>
              No data
            </Typography>
          )}
        </Box>

        {/* Sparkline */}
        <Box sx={{ height: '40px', width: '100%', my: 1, flexGrow: 1 /* Allow sparkline area to grow slightly */ }}>
          {showSparkline ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 5, right: 0, left: 0, bottom: 5 }}>
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: alpha(theme.palette.background.paper, 0.9),
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: '4px',
                    fontSize: '12px',
                    padding: '4px 8px',
                  }}
                  itemStyle={{ color: theme.palette.text.primary }}
                  labelStyle={{ color: theme.palette.text.secondary, marginBottom: '4px' }}
                  labelFormatter={(label) => {
                    // Check if label is a valid date representation before formatting
                    const date = new Date(label);
                    if (!isNaN(date.getTime())) { // Check if date is valid
                      return `Date: ${format(date, DATE_FORMAT.DISPLAY)}`;
                    }
                    return 'Date: Invalid'; // Fallback for invalid dates
                  }}
                  formatter={(value) => [`${value} ${latestUnit ?? ''}`, null]} // Value only, no name
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={trendColor} // Use trend color for sparkline
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
             hasValue && ( // Only show "not enough data" if there IS a value but not enough history
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <Typography variant="caption" sx={{ color: theme.palette.text.disabled, fontStyle: 'italic' }}>
                  Not enough data for trend line
                </Typography>
              </Box>
             )
          )}
        </Box>

        {/* Footer: Status Pill and Date */}
        <Box sx={{ mt: 'auto', pt: 1 /* Add padding top to separate from sparkline */, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Chip
            label={status || 'Unknown'}
            size="small"
            sx={{
              height: '20px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: '10px', // Pill shape
              border: '1px solid',
              ...statusStyle, // Apply dynamic colors
            }}
          />
          {latestDate && (
            <Typography
              variant="caption"
              sx={{ color: theme.palette.text.secondary, fontSize: '12px' }}
              title={`Latest: ${format(latestDate, DATE_FORMAT.DISPLAY)}`}
            >
              {format(latestDate, 'MMM yyyy')}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default BiomarkerTile;
