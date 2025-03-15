import React from 'react';
import { 
  Typography, 
  Container, 
  Box, 
  Paper, 
  Card, 
  CardContent, 
  Grid, 
  Divider 
} from '@mui/material';

const AboutPage: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography 
          variant="h3" 
          component="h1" 
          align="center" 
          color="primary" 
          gutterBottom
          sx={{ fontWeight: 'bold' }}
        >
          About Vein Diagram
        </Typography>
        
        <Paper elevation={2} sx={{ p: 4, mb: 4 }}>
          <Typography variant="body1" paragraph>
            Vein Diagram is a comprehensive tool designed to help individuals track and visualize 
            their blood test results over time. By providing easy-to-understand visualizations,
            we aim to make health data more accessible and actionable for everyone.
          </Typography>
          
          <Typography variant="body1" paragraph>
            Our application allows you to upload your lab test results, track changes in your
            biomarkers over time, and gain insights into your health trends.
          </Typography>
        </Paper>
        
        <Typography 
          variant="h4" 
          component="h2" 
          color="primary" 
          align="center" 
          gutterBottom
          sx={{ mt: 6, mb: 4 }}
        >
          Key Features
        </Typography>
        
        <Grid container spacing={3} sx={{ mb: 6 }}>
          <Grid item xs={12} md={4}>
            <Card raised sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" component="h3" gutterBottom color="primary">
                  Data Visualization
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body2">
                  Transform complex blood test data into intuitive charts and graphs that make 
                  it easy to understand your health metrics at a glance.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card raised sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" component="h3" gutterBottom color="primary">
                  Trend Tracking
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body2">
                  Monitor changes in your biomarkers over time to identify trends and track 
                  the impact of lifestyle changes or medical interventions.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card raised sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" component="h3" gutterBottom color="primary">
                  Reference Ranges
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body2">
                  Compare your results against standard reference ranges to better understand 
                  where your values fall within typical healthy parameters.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        
        <Paper 
          elevation={1} 
          sx={{ 
            p: 3, 
            bgcolor: '#f5f5ff', 
            borderLeft: '4px solid #6200ee' 
          }}
        >
          <Typography variant="h6" gutterBottom>
            Data Privacy
          </Typography>
          <Typography variant="body2">
            At Vein Diagram, we take your privacy seriously. Your health data is encrypted and 
            stored securely. We never share your personal information with third parties without 
            your explicit consent.
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default AboutPage; 