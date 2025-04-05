import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  Divider, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon,
  Button,
  useTheme,
  alpha,
  Chip,
  Avatar,
  CircularProgress,
  LinearProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import AssessmentIcon from '@mui/icons-material/Assessment';
import DescriptionIcon from '@mui/icons-material/Description';
import TimelineIcon from '@mui/icons-material/Timeline';
import InsightsIcon from '@mui/icons-material/Insights';
// FavoriteIcon removed - unused
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
// ScaleIcon removed - unused
import VisibilityIcon from '@mui/icons-material/Visibility';
import { Link as RouterLink } from 'react-router-dom';
import storageService, { STORAGE_KEYS } from '../services/localStorage';

// Type definitions for statistics
interface BiomarkerSummary {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'flat';
  status: 'normal' | 'borderline' | 'abnormal';
  lastUpdated: string;
}

interface FileInfo {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadDate: string;
  status: string;
}

// Format date for display
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(date);
};

// Generate mock biomarker summaries
const generateMockBiomarkers = (): BiomarkerSummary[] => {
  const biomarkers: BiomarkerSummary[] = [
    {
      name: 'Total Cholesterol',
      value: 185,
      unit: 'mg/dL',
      trend: 'down',
      status: 'normal',
      lastUpdated: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      name: 'HDL Cholesterol',
      value: 62,
      unit: 'mg/dL',
      trend: 'up',
      status: 'normal',
      lastUpdated: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      name: 'LDL Cholesterol',
      value: 110,
      unit: 'mg/dL',
      trend: 'down',
      status: 'normal',
      lastUpdated: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      name: 'Triglycerides',
      value: 138,
      unit: 'mg/dL',
      trend: 'flat',
      status: 'normal',
      lastUpdated: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      name: 'Glucose',
      value: 102,
      unit: 'mg/dL',
      trend: 'up',
      status: 'borderline',
      lastUpdated: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      name: 'Vitamin D',
      value: 28,
      unit: 'ng/mL',
      trend: 'up',
      status: 'borderline',
      lastUpdated: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()
    }
  ];
  
  return biomarkers;
};

// Get status color
const getStatusColor = (status: string): string => {
  switch(status) {
    case 'normal':
      return 'success';
    case 'borderline':
      return 'warning';
    case 'abnormal':
      return 'error';
    default:
      return 'info';
  }
};

// Get trend icon
const getTrendIcon = (trend: string) => {
  switch(trend) {
    case 'up':
      return <TrendingUpIcon fontSize="small" />;
    case 'down':
      return <TrendingDownIcon fontSize="small" />;
    case 'flat':
    default:
      return <TrendingFlatIcon fontSize="small" />;
  }
};

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const [biomarkers, setBiomarkers] = useState<BiomarkerSummary[]>([]);
  const [recentUploads, setRecentUploads] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      // Get biomarker data (mock data for now)
      setBiomarkers(generateMockBiomarkers());
      
      // Get recent uploads from localStorage
      const uploads = storageService.getItem<FileInfo[]>(STORAGE_KEYS.UPLOADED_FILES, [])
        .sort((a, b) => new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime())
        .slice(0, 5); // Get most recent 5
      
      setRecentUploads(uploads);
      setLoading(false);
    }, 800);
    
    return () => clearTimeout(timer);
  }, []);
  
  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Loading your health dashboard...
        </Typography>
      </Box>
    );
  }
  
  return (
    <Box sx={{ mb: 4 }}>
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            className="hover-card"
            sx={{ 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '4px',
                backgroundColor: theme.palette.primary.main
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: theme.palette.primary.main, mr: 2 }}>
                  <AssessmentIcon />
                </Avatar>
                <Typography variant="h6" component="div">
                  Biomarkers
                </Typography>
              </Box>
              
              <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                {biomarkers.length}
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                Total biomarkers tracked
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            className="hover-card"
            sx={{ 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '4px',
                backgroundColor: theme.palette.success.main
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: alpha(theme.palette.success.main, 0.1), color: theme.palette.success.main, mr: 2 }}>
                  <LocalHospitalIcon />
                </Avatar>
                <Typography variant="h6" component="div">
                  Health Score
                </Typography>
              </Box>
              
              <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                85
                <Typography variant="caption" component="span" sx={{ ml: 1, fontSize: '1rem' }}>
                  / 100
                </Typography>
              </Typography>
              
              <LinearProgress 
                variant="determinate" 
                value={85} 
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  mb: 1,
                  backgroundColor: alpha(theme.palette.success.main, 0.1),
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: theme.palette.success.main
                  }
                }} 
              />
              
              <Typography variant="body2" color="text.secondary">
                Optimal range
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            className="hover-card"
            sx={{ 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '4px',
                backgroundColor: theme.palette.warning.main
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: alpha(theme.palette.warning.main, 0.1), color: theme.palette.warning.main, mr: 2 }}>
                  <TimelineIcon />
                </Avatar>
                <Typography variant="h6" component="div">
                  To Monitor
                </Typography>
              </Box>
              
              <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                {biomarkers.filter(b => b.status === 'borderline').length}
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                Biomarkers to watch
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            className="hover-card"
            sx={{ 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '4px',
                backgroundColor: theme.palette.info.main
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), color: theme.palette.info.main, mr: 2 }}>
                  <DescriptionIcon />
                </Avatar>
                <Typography variant="h6" component="div">
                  Reports
                </Typography>
              </Box>
              
              <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                {recentUploads.length}
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                Uploaded test reports
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Biomarkers and Recent Uploads */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Key Biomarkers
              </Typography>
              <Button 
                component={RouterLink} 
                to="/visualize" 
                endIcon={<InsightsIcon />}
                size="small"
              >
                View All
              </Button>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={2}>
              {biomarkers.slice(0, 6).map((biomarker, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Card variant="outlined" sx={{ mb: 1 }}>
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2" component="div">
                          {biomarker.name}
                        </Typography>
                        <Chip 
                          label={biomarker.status} 
                          size="small" 
                          color={getStatusColor(biomarker.status) as "success" | "warning" | "error" | "info"}
                          sx={{ height: 20, '& .MuiChip-label': { px: 1 } }}
                        />
                      </Box>
                      
                      <Box sx={{ display: 'flex', alignItems: 'baseline' }}>
                        <Typography variant="h6" component="div" sx={{ mr: 1 }}>
                          {biomarker.value}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {biomarker.unit}
                        </Typography>
                        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
                          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                            {biomarker.trend}
                          </Typography>
                          {getTrendIcon(biomarker.trend)}
                        </Box>
                      </Box>
                      
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                        <AccessTimeIcon sx={{ fontSize: 12, mr: 0.5, verticalAlign: 'middle' }} />
                        Updated {formatDate(biomarker.lastUpdated)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Recent Uploads
              </Typography>
              <Button 
                component={RouterLink} 
                to="/upload" 
                endIcon={<DescriptionIcon />}
                size="small"
              >
                Upload More
              </Button>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            {recentUploads.length > 0 ? (
              <List disablePadding>
                {recentUploads.map((upload, index) => (
                  <React.Fragment key={upload.id}>
                    {index > 0 && <Divider component="li" />}
                    <ListItem
                      alignItems="flex-start"
                      secondaryAction={
                        <Tooltip title="View Details">
                          <IconButton 
                            edge="end" 
                            component={RouterLink}
                            to="/visualize"
                            size="small"
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      }
                      sx={{ py: 1.5 }}
                    >
                      <ListItemIcon>
                        <DescriptionIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={upload.name}
                        primaryTypographyProps={{ variant: 'subtitle2' }}
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            Uploaded {formatDate(upload.uploadDate)}
                          </Typography>
                        }
                      />
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box sx={{ py: 4, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  No files uploaded yet
                </Typography>
                <Button
                  variant="outlined"
                  component={RouterLink}
                  to="/upload"
                  startIcon={<DescriptionIcon />}
                  sx={{ mt: 2 }}
                >
                  Upload Your First File
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
