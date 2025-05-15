// frontend/src/components/ResumeUpload.jsx

import React, { useState, useRef } from 'react';
import { uploadResumes } from '../api/apiService'; // Adjust path if needed
// MUI Components
import {
  Box,
  Button,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Alert,
  Paper // For containing the upload section
} from '@mui/material';
// MUI Icons
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DescriptionIcon from '@mui/icons-material/Description'; // For file list
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

const glowButtonSx = { // Reusing a similar button style definition
  fontWeight: 'bold',
  minWidth: '120px',
  boxShadow: {
    xs: 'none',
    ':hover': theme => `0 0 10px ${theme.palette.primary.light}, 0 0 20px ${theme.palette.primary.light}`
  },
  transition: theme => theme.transitions.create(['box-shadow', 'background-color'], {
    duration: theme.transitions.duration.short,
  }),
  '&.Mui-disabled': {
    boxShadow: 'none',
    backgroundColor: 'action.disabledBackground',
    color: 'action.disabled'
  }
};

// Accept jobId and an onUploadSuccess callback as props
function ResumeUpload({ jobId, onUploadSuccess }) {
  const [selectedFiles, setSelectedFiles] = useState([]); // Store array of File objects
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const fileInputRef = useRef(null); // Ref to access the hidden file input element

  const handleFileChange = (event) => {
    // event.target.files is a FileList, convert to array
    if (event.target.files) {
      setSelectedFiles(Array.from(event.target.files));
      setError(null); // Clear previous errors
      setSuccessMessage(''); // Clear previous success messages
    }
  };

  // Trigger click on hidden file input
  const handleChooseFilesClick = () => {
    fileInputRef.current.click();
  };

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setError('Please select one or more resume files first.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMessage('');

    try {
      // uploadResumes expects an array of File objects
      const response = await uploadResumes(jobId, selectedFiles);

      let successMsgParts = [];
      if (response.data.uploaded && response.data.uploaded.length > 0) {
          successMsgParts.push(`${response.data.uploaded.length} file(s) successfully queued.`);
      }
      if (response.data.errors && Object.keys(response.data.errors).length > 0) {
          const errorCount = Object.keys(response.data.errors).length;
          successMsgParts.push(`${errorCount} file(s) had errors during server validation.`);
          // For more detail, you could list the filenames and their errors
          console.warn("Server-side upload errors:", response.data.errors);
      }
      setSuccessMessage(successMsgParts.length > 0 ? successMsgParts.join(' ') : 'Upload initiated.');


      // Clear the file input and state after successful API call
      if (fileInputRef.current) {
          fileInputRef.current.value = ""; // Reset file input so same file can be chosen again
      }
      setSelectedFiles([]); // Clear selected files state

      // Call the callback function passed from the parent (JobDetailPage)
      if (onUploadSuccess) {
        onUploadSuccess();
      }

    } catch (err) {
      console.error(`Error uploading resumes for job ${jobId}:`, err);
       if (err.response && err.response.data && err.response.data.error) {
         setError(`Upload failed: ${err.response.data.error}` + (err.response.data.details ? ` - ${JSON.stringify(err.response.data.details)}` : ''));
      } else if (err.request) {
          setError('Upload failed: No response from server. Is the backend running?');
      } else {
          setError(`Upload failed: ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 2, backgroundColor: 'background.paper', borderRadius: '8px' }}>
      {/* Hidden file input */}
      <input
        type="file"
        multiple
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={handleFileChange}
        ref={fileInputRef}
        style={{ display: 'none' }} // Hide the default input
        id="resume-file-input"
      />

      {/* Button to trigger file selection */}
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          color="secondary"
          onClick={handleChooseFilesClick}
          startIcon={<CloudUploadIcon />}
          disabled={isLoading}
          fullWidth // Make choose files button take more space
          sx={{maxWidth: '400px'}}
        >
          Choose Files ({selectedFiles.length} selected)
        </Button>

        {/* Display list of selected files */}
        {selectedFiles.length > 0 && (
          <Box sx={{ width: '100%', maxWidth: '400px', maxHeight: '150px', overflowY: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1, p:1 }}>
            <Typography variant="caption" display="block" gutterBottom>Selected:</Typography>
            <List dense disablePadding>
              {selectedFiles.map((file, index) => (
                <ListItem key={index} disableGutters dense>
                  <ListItemIcon sx={{minWidth: '30px'}}>
                    <DescriptionIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={file.name} primaryTypographyProps={{ variant: 'body2', noWrap: true }} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Upload Button */}
        <Box sx={{ position: 'relative', display: 'inline-block' }}>
            <Button
                variant="contained"
                color="primary"
                onClick={handleUpload}
                disabled={isLoading || selectedFiles.length === 0}
                sx={glowButtonSx} // Apply glow style
                startIcon={isLoading ? null : <CloudUploadIcon />} // Only show icon when not loading
            >
                 <Box component="span" sx={{ visibility: isLoading ? 'hidden' : 'visible' }}>
                    {`Upload ${selectedFiles.length} File(s)`}
                </Box>
            </Button>
            {isLoading && (
              <CircularProgress
                size={24}
                sx={{
                  color: 'primary.contrastText', // Spinner color that contrasts with button
                  position: 'absolute',
                  top: '50%', left: '50%',
                  marginTop: '-12px', marginLeft: '-12px',
                }}
              />
            )}
        </Box>
      </Box>

      {/* Display Success or Error Messages */}
      {successMessage && <Alert severity="success" icon={<CheckCircleIcon fontSize="inherit" />} sx={{ mt: 2 }}>{successMessage}</Alert>}
      {error && <Alert severity="error" icon={<ErrorIcon fontSize="inherit" />} sx={{ mt: 2 }}>{error}</Alert>}
    </Paper>
  );
}

export default ResumeUpload;