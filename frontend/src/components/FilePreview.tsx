import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Chip,
  useTheme,
  Card,
  CardContent,
  CardMedia,
  Tooltip,
  IconButton
} from '@mui/material';
import { 
  PictureAsPdf as PdfIcon,
  Description as FileIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

interface FilePreviewProps {
  file: File;
  onRemove?: () => void;
}

// Format file size to human-readable format
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Get file type icon based on MIME type
const getFileIcon = (file: File): JSX.Element => {
  const type = file.type;
  
  if (type === 'application/pdf') {
    return <PdfIcon fontSize="large" color="error" />;
  } 
  
  return <FileIcon fontSize="large" color="primary" />;
};

export const FilePreview: React.FC<FilePreviewProps> = ({ file, onRemove }) => {
  const theme = useTheme();
  
  // Get last modified date formatted
  const getLastModified = (): string => {
    const date = new Date(file.lastModified);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  return (
    <Card variant="outlined" sx={{ 
      marginBottom: 2, 
      borderRadius: 2,
      transition: 'all 0.2s ease',
      '&:hover': {
        boxShadow: 2,
      }
    }}>
      <CardContent sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 2,
        paddingY: 2
      }}>
        <Box sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          width: 60,
          height: 60,
          borderRadius: 1,
          backgroundColor: theme.palette.mode === 'light' 
            ? 'rgba(0, 0, 0, 0.03)' 
            : 'rgba(255, 255, 255, 0.05)'
        }}>
          {getFileIcon(file)}
        </Box>
        
        <Box sx={{ flex: 1 }}>
          <Typography variant="subtitle1" component="div" noWrap sx={{ 
            fontWeight: 500,
            maxWidth: '100%'
          }}>
            {file.name}
          </Typography>
          
          <Box sx={{ 
            display: 'flex', 
            gap: 1,
            flexWrap: 'wrap',
            alignItems: 'center',
            mt: 0.5
          }}>
            <Chip 
              label={formatFileSize(file.size)} 
              size="small" 
              variant="outlined" 
              sx={{ height: 20 }}
            />
            
            <Typography variant="caption" color="text.secondary">
              Modified: {getLastModified()}
            </Typography>
            
            <Chip 
              label={file.type || 'Unknown type'} 
              size="small" 
              variant="outlined" 
              sx={{ height: 20 }}
            />
          </Box>
        </Box>
        
        {onRemove && (
          <Tooltip title="Remove file">
            <IconButton 
              size="small" 
              onClick={onRemove} 
              color="default" 
              sx={{ 
                '&:hover': { 
                  color: theme.palette.error.main 
                } 
              }}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        )}
      </CardContent>
    </Card>
  );
};

export default FilePreview; 