// frontend/src/components/ResumeUpload.jsx
import React, { useState, useRef } from 'react';
import { uploadResumes } from '../api/apiService';
import {
  Box, Button, Typography, List, ListItem, ListItemIcon, ListItemText,
  CircularProgress, Alert, Paper, useTheme,alpha // Added Paper, useTheme
} from '@mui/material';

import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DescriptionIcon from '@mui/icons-material/Description';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { glassMorphismPaperSx, glowButtonSx } from '../styles/commonStyles'; // Import styles

function ResumeUpload({ jobId, onUploadSuccess }) {
  const theme = useTheme();
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => { /* ... as before ... */
    if (event.target.files) { setSelectedFiles(Array.from(event.target.files)); setError(null); setSuccessMessage(''); }
  };
  const handleChooseFilesClick = () => { fileInputRef.current.click(); };
  const handleUpload = async () => { /* ... as before ... */
    if (!selectedFiles || selectedFiles.length === 0) { setError('Please select one or more resume files first.'); return; } setIsLoading(true); setError(null); setSuccessMessage(''); const filesArray = Array.from(selectedFiles); try { const response = await uploadResumes(jobId, filesArray); let successMsgParts = []; if (response.data.uploaded && response.data.uploaded.length > 0) { successMsgParts.push(`${response.data.uploaded.length} file(s) successfully queued.`); } if (response.data.errors && Object.keys(response.data.errors).length > 0) { const errorCount = Object.keys(response.data.errors).length; successMsgParts.push(`${errorCount} file(s) had errors during server validation.`); console.warn("Server-side upload errors:", response.data.errors); } setSuccessMessage(successMsgParts.length > 0 ? successMsgParts.join(' ') : 'Upload initiated.'); if (fileInputRef.current) { fileInputRef.current.value = ""; } setSelectedFiles([]); if (onUploadSuccess) { onUploadSuccess(); } } catch (err) { console.error(`Error uploading resumes for job ${jobId}:`, err); let errMsg = 'Upload failed.'; if (err.response && err.response.data) { errMsg = err.response.data.error || errMsg; if (err.response.data.details) { errMsg += ` Details: ${JSON.stringify(err.response.data.details)}`; } } else if (err.request) { errMsg = 'Upload failed: No response from server.'; } else { errMsg = err.message; } setError(errMsg); } finally { setIsLoading(false); }
  };

  return (
    <Paper elevation={0} sx={{ ...glassMorphismPaperSx(theme), p: {xs: 2, sm:3}, mt: 1 }}> {/* Apply glass style */}
      <input type="file" multiple accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={handleFileChange} ref={fileInputRef} style={{ display: 'none' }} id={`resume-file-input-${jobId}`} />
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          color="secondary"
          onClick={handleChooseFilesClick}
          startIcon={<CloudUploadIcon />}
          disabled={isLoading}
          fullWidth
          sx={{ maxWidth: '450px' }} // Control width of choose files button
        >
          Choose Files ({selectedFiles.length} selected)
        </Button>

        {selectedFiles.length > 0 && (
          <Box sx={{ width: '100%', maxWidth: '450px', maxHeight: '150px', overflowY: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: theme.shape.borderRadius * 0.5, p:1, backgroundColor: alpha(theme.palette.common.black, 0.2) }}>
            <Typography variant="caption" display="block" gutterBottom sx={{color: 'text.secondary'}}>Selected files:</Typography>
            <List dense disablePadding>
              {selectedFiles.map((file, index) => (
                <ListItem key={index} disableGutters dense sx={{py: 0.2}}>
                  <ListItemIcon sx={{minWidth: '30px', color: 'text.secondary'}}><DescriptionIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary={file.name} primaryTypographyProps={{ variant: 'body2', noWrap: true, color: 'text.secondary' }} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Box sx={{ position: 'relative', display: 'inline-block' }}>
            <Button
                variant="contained"
                color="primary"
                onClick={handleUpload}
                disabled={isLoading || selectedFiles.length === 0}
                sx={glowButtonSx(theme)}
                startIcon={isLoading ? null : <CloudUploadIcon />}
                size="large"
            >
                 <Box component="span" sx={{ visibility: isLoading ? 'hidden' : 'visible' }}>
                    {`Upload ${selectedFiles.length} File(s)`}
                </Box>
            </Button>
            {isLoading && ( <CircularProgress size={24} sx={{ color: 'primary.contrastText', position: 'absolute', top: '50%', left: '50%', marginTop: '-12px', marginLeft: '-12px', }} /> )}
        </Box>
      </Box>
      {successMessage && <Alert severity="success" icon={<CheckCircleIcon fontSize="inherit" />} sx={{ mt: 2 }}>{successMessage}</Alert>}
      {error && <Alert severity="error" icon={<ErrorIcon fontSize="inherit" />} sx={{ mt: 2 }}>{error}</Alert>}
    </Paper>
  );
}
export default ResumeUpload;