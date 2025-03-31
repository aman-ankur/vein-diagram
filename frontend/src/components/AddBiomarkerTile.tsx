import React from 'react';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';

interface AddBiomarkerTileProps {
  onAddClick: () => void;
}

const AddBiomarkerTile: React.FC<AddBiomarkerTileProps> = ({ onAddClick }) => {
  return (
    <div
      className="bg-gray-50 dark:bg-gray-800 rounded-lg shadow-inner border border-dashed border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 cursor-pointer flex items-center justify-center min-h-[160px]" // Match min-height of BiomarkerTile
      onClick={onAddClick}
      role="button"
      tabIndex={0}
      aria-label="Add favorite biomarker"
    >
      <AddCircleOutlineIcon
        sx={{ fontSize: 40 }} // Make icon larger
        className="text-gray-400 dark:text-gray-500 group-hover:text-gray-500 dark:group-hover:text-gray-400"
      />
    </div>
  );
};

export default AddBiomarkerTile;
