import React from 'react';
import { Grid } from '@mui/material'; // Import MUI Grid
import BiomarkerTile from './BiomarkerTile';
import AddBiomarkerTile from './AddBiomarkerTile'; // Import the new component
import { ProcessedFavoriteData } from '../utils/biomarkerUtils';
import { isFavorite as checkIsFavorite } from '../utils/favoritesUtils'; // Only need checker here

const MAX_DISPLAY_TILES = 8; // Define the total number of tiles to display (CHANGED TO 8)

interface FavoriteBiomarkersGridProps {
  profileId: string;
  favoriteData: ProcessedFavoriteData[]; // This should contain up to MAX_DISPLAY_TILES items
  onToggleFavorite: (biomarkerName: string) => void;
  onAddClick: () => void; // Handler for clicking the add tile
}

const FavoriteBiomarkersGrid: React.FC<FavoriteBiomarkersGridProps> = ({
  profileId,
  favoriteData,
  onToggleFavorite,
  onAddClick,
}) => {

  if (!profileId) {
    // This shouldn't happen if the parent component checks, but good practice
    return <p className="text-red-500">Error: Profile ID is missing.</p>;
  }

  if (favoriteData.length === 0) {
    return (
      <p className="text-gray-600 dark:text-gray-400">
        No favorite biomarker data to display. Add some biomarkers to your favorites!
      </p>
    );
  }

  const numDataTiles = favoriteData.length;
  const numAddTiles = Math.max(0, MAX_DISPLAY_TILES - numDataTiles);

  // Use MUI Grid for layout
  return (
    // spacing={2} corresponds to 16px if theme.spacing(1) = 8px
    <Grid container spacing={2}> 
      {/* Render Biomarker Tiles */}
      {favoriteData.map((data) => (
        // xs={6}: 2 columns on mobile
        // sm={4}: 3 columns on tablet
        // md={3}: 4 columns on desktop
        <Grid item key={`biomarker-${data.name}`} xs={6} sm={4} md={3}> 
          <BiomarkerTile
            biomarkerData={data}
            isFavorite={checkIsFavorite(profileId, data.name)}
            onToggleFavorite={onToggleFavorite}
          />
        </Grid>
      ))}

      {/* Render Add Tiles */}
      {Array.from({ length: numAddTiles }).map((_, index) => (
        // Use the same responsive column settings for the add tile
        <Grid item key={`add-${index}`} xs={6} sm={4} md={3}> 
          <AddBiomarkerTile onAddClick={onAddClick} />
        </Grid>
      ))}
    </Grid>
  );
};

export default FavoriteBiomarkersGrid;
