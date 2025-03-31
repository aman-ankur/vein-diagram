import React, { useState, useEffect, useRef } from 'react';
import { Box, Card, CardContent, Typography, CircularProgress } from '@mui/material';
import { styled } from '@mui/material/styles';
import healthFacts from '../assets/facts.json';
import FactIcon from './FactIcons';

interface FactsCarouselProps {
  isActive: boolean;
}

// Custom styled components for animations
const FactCard = styled(Card)(({ theme }) => ({
  position: 'relative',
  width: '100%',
  maxWidth: '500px',
  margin: '0 auto',
  opacity: 0,
  transform: 'translateY(20px)',
  transition: 'opacity 0.5s ease-in-out, transform 0.5s ease-in-out',
  boxShadow: theme.shadows[3],
  '&.active': {
    opacity: 1,
    transform: 'translateY(0)',
  },
}));

const ProgressIndicator = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  marginTop: theme.spacing(4),
  marginBottom: theme.spacing(2),
  '& .MuiCircularProgress-root': {
    animation: 'pulse 1.5s ease-in-out infinite',
  },
  '@keyframes pulse': {
    '0%': {
      opacity: 0.6,
      transform: 'scale(0.98)',
    },
    '50%': {
      opacity: 1,
      transform: 'scale(1)',
    },
    '100%': {
      opacity: 0.6,
      transform: 'scale(0.98)',
    },
  },
}));

const FactsCarousel: React.FC<FactsCarouselProps> = ({ isActive }) => {
  const [currentFactIndex, setCurrentFactIndex] = useState<number | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [usedFactIndices, setUsedFactIndices] = useState<number[]>([]);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Function to get a random fact that hasn't been shown yet
  const getRandomFact = () => {
    // If all facts have been shown, reset the used indices
    if (usedFactIndices.length >= healthFacts.length) {
      setUsedFactIndices([]);
      const randomIndex = Math.floor(Math.random() * healthFacts.length);
      setCurrentFactIndex(randomIndex);
      setUsedFactIndices([randomIndex]);
      return;
    }

    // Get a random fact that hasn't been used yet
    const availableIndices = Array.from(
      { length: healthFacts.length },
      (_, i) => i
    ).filter((index) => !usedFactIndices.includes(index));
    
    const randomIndex = availableIndices[Math.floor(Math.random() * availableIndices.length)];
    setCurrentFactIndex(randomIndex);
    setUsedFactIndices([...usedFactIndices, randomIndex]);
  };

  // Initialize with a random fact
  useEffect(() => {
    if (isActive && currentFactIndex === null) {
      getRandomFact();
    }
  }, [isActive]);

  // Rotate facts every 4 seconds
  useEffect(() => {
    if (isActive) {
      setIsVisible(true);
      
      // Clear previous timeout if it exists
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        // Fade out
        setIsVisible(false);
        
        // Wait for fade out animation to complete before changing fact
        setTimeout(() => {
          getRandomFact();
          // Fade in new fact
          setIsVisible(true);
        }, 500); // This should match the CSS transition duration
      }, 4000); // Show each fact for 4 seconds
    } else {
      // Clean up timeout when component becomes inactive
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      setIsVisible(false);
    }

    // Clean up on unmount
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isActive, currentFactIndex]);

  if (!isActive || currentFactIndex === null) {
    return null;
  }

  const currentFact = healthFacts[currentFactIndex];
  
  return (
    <Box sx={{ textAlign: 'center', py: 2 }}>
      <ProgressIndicator>
        <CircularProgress size={60} />
      </ProgressIndicator>
      
      <FactCard className={isVisible ? 'active' : ''}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ mr: 2, mt: 0.5 }}>
              <FactIcon iconName={currentFact.icon || currentFact.category} size="large" />
            </Box>
            <Typography variant="body1" component="div" sx={{ textAlign: 'left' }}>
              {currentFact.text}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Category: {currentFact.category}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Fact {currentFactIndex + 1}/{healthFacts.length}
            </Typography>
          </Box>
        </CardContent>
      </FactCard>
    </Box>
  );
};

export default FactsCarousel; 