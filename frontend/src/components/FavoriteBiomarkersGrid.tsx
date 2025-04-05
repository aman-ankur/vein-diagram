import React from 'react'; // Removed unused useState
import { Grid } from '@mui/material'; // Import MUI Grid
import BiomarkerTile from './BiomarkerTile';
import AddBiomarkerTile from './AddBiomarkerTile'; // Import the new component
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent, // Import DragEndEvent type
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy, // Use a grid-compatible strategy
  useSortable, // Will be used in BiomarkerTile itself
} from '@dnd-kit/sortable';
import { ProcessedFavoriteData } from '../utils/biomarkerUtils';
// Removed import for checkIsFavorite as it's no longer needed here

const MAX_DISPLAY_TILES = 8; // Define the total number of tiles to display (CHANGED TO 8)

interface FavoriteBiomarkersGridProps {
  profileId: string;
  favoriteData: ProcessedFavoriteData[]; // This should contain up to MAX_DISPLAY_TILES items
  onToggleFavorite: (biomarkerName: string) => void; // Keep for star icon if needed
  onDeleteFavorite: (biomarkerName: string) => void; // Add delete handler prop
  onAddClick: () => void; // Handler for clicking the add tile
  onOrderChange: (orderedNames: string[]) => void; // Callback when order changes via D&D
}

// Make BiomarkerTile sortable
const SortableBiomarkerTile: React.FC<{ 
  id: string; 
  biomarkerData: ProcessedFavoriteData;
  isFavorite: boolean;
  onToggleFavorite: (biomarkerName: string) => void;
  onDeleteFavorite: (biomarkerName: string) => void;
}> = (props) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging, // Use isDragging for styling
  } = useSortable({ id: props.id });

  const style = {
    transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
    transition,
    opacity: isDragging ? 0.5 : 1, // Make tile semi-transparent while dragging
    zIndex: isDragging ? 100 : 'auto', // Ensure dragging tile is on top
  };

  // Create a wrapped onDeleteFavorite handler with debug logging
  const handleDelete = (biomarkerName: string) => {
    console.log(`🟢 SortableBiomarkerTile: Delete handler called for "${biomarkerName}"`);
    // Call the original handler
    props.onDeleteFavorite(biomarkerName);
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <BiomarkerTile 
        {...props} 
        onDeleteFavorite={handleDelete} 
      />
    </div>
  );
};


const FavoriteBiomarkersGrid: React.FC<FavoriteBiomarkersGridProps> = ({
  profileId,
  favoriteData,
  onToggleFavorite,
  onDeleteFavorite, // Destructure the new prop
  onAddClick,
  onOrderChange, // Destructure the order change handler
}) => {
  // Configure a custom pointer sensor that ignores clicks on elements with data-no-dnd attribute
  const customPointerSensor = useSensor(PointerSensor, {
    activationConstraint: {
      distance: 8, // Start dragging after moving 8px
    },
    // Add a custom handler to prevent dragging when clicking on no-drag elements
    eventListeners: {
      // @ts-ignore - DndKit types might not include all the event properties
      onPointerDown: ({ nativeEvent }) => {
        let target = nativeEvent.target;
        
        // Check if the click is on or within an element with data-no-dnd
        while (target) {
          if (target.hasAttribute && target.hasAttribute('data-no-dnd')) {
            console.log('🚫 Preventing drag start on no-drag element');
            return false; // Prevents drag from starting
          }
          target = target.parentElement;
        }
        return true; // Allow drag to start
      }
    }
  });
  
  // Use sensors for pointer and keyboard interactions
  const sensors = useSensors(
    customPointerSensor,
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

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

  // Extract just the names for SortableContext items
  const favoriteNames = favoriteData.map(data => data.name);
  const numDataTiles = favoriteData.length;
  const numAddTiles = Math.max(0, MAX_DISPLAY_TILES - numDataTiles);

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = favoriteNames.indexOf(active.id as string);
      const newIndex = favoriteNames.indexOf(over.id as string);

      if (oldIndex !== -1 && newIndex !== -1) {
        const newOrderedNames = arrayMove(favoriteNames, oldIndex, newIndex);
        console.log("Drag ended, new order:", newOrderedNames);
        onOrderChange(newOrderedNames); // Call the callback with the new order
      } else {
         console.warn("Could not find dragged item indices:", { activeId: active.id, overId: over.id, names: favoriteNames });
      }
    }
  }

  // Use MUI Grid for layout
  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={favoriteNames} strategy={rectSortingStrategy}>
        {/* spacing={2} corresponds to 16px if theme.spacing(1) = 8px */}
        <Grid container spacing={2}>
          {/* Render Sortable Biomarker Tiles */}
          {favoriteData.map((data) => (
            // xs={6}: 2 columns on mobile
            // sm={4}: 3 columns on tablet
            // md={3}: 4 columns on desktop
            <Grid item key={`biomarker-${data.name}`} xs={6} sm={4} md={3}>
              <SortableBiomarkerTile
                id={data.name} // Use name as the unique ID for sorting
                biomarkerData={data}
                isFavorite={favoriteNames.includes(data.name)} // Check against the state passed via favoriteData
                onToggleFavorite={onToggleFavorite} // Pass toggle handler
                onDeleteFavorite={onDeleteFavorite} // Pass delete handler
              />
            </Grid>
          ))}

          {/* Render Add Tiles (Not sortable) */}
      {Array.from({ length: numAddTiles }).map((_, index) => (
        // Use the same responsive column settings for the add tile
        <Grid item key={`add-${index}`} xs={6} sm={4} md={3}> 
          <AddBiomarkerTile onAddClick={onAddClick} />
        </Grid>
      ))}
        </Grid> 
      </SortableContext> 
    </DndContext> 
  );
};

export default FavoriteBiomarkersGrid; // Ensure default export exists
