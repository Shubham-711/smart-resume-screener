// frontend/src/components/ResumeList.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { fetchResumesForJob, deleteResume } from '../api/apiService'; // Ensure deleteResume is imported
// MUI Components
import {
  Box,
  Typography,
  List,
  Paper, // Using Paper for each list item for better styling control
  Chip,
  Button,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Grid // For layout within each item
} from '@mui/material';
// MUI Icons
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HourglassTopIcon from '@mui/icons-material/HourglassTop';
import PendingIcon from '@mui/icons-material/Pending';


// Helper to format score
const formatScore = (score) => {
  if (score === null || score === undefined) {
    return '--';
  }
  return `${(score * 100).toFixed(1)}%`;
};

// Helper to determine Chip color based on status
const getStatusChipColor = (status) => {
  switch (status?.toUpperCase()) { // Handle potential case variations
    case 'COMPLETED': return 'success';
    case 'PROCESSING': return 'warning';
    case 'PENDING': return 'default';
    case 'FAILED': return 'error';
    default: return 'default';
  }
};

// Helper to get an icon based on status (optional)
const getStatusIcon = (status) => {
    switch (status?.toUpperCase()) {
        case 'COMPLETED': return <CheckCircleOutlineIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        case 'PROCESSING': return <HourglassTopIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        case 'PENDING': return <PendingIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        case 'FAILED': return <ErrorOutlineIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        default: return null;
      }
}

function ResumeList({ jobId }) {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(false); // For initial load / manual refresh
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [deletingId, setDeletingId] = useState(null); // Track which resume is being deleted

  const loadResumes = useCallback(async (showLoadingIndicator = true) => {
    if (!jobId) return;
    if (showLoadingIndicator) setLoading(true);
    setError(null);
    try {
      const response = await fetchResumesForJob(jobId);
      const fetchedResumes = response.data || [];
      setResumes(fetchedResumes);
      const stillProcessing = fetchedResumes.some(r => r.status === 'PENDING' || r.status === 'PROCESSING');
      setIsPolling(stillProcessing);
    } catch (err) {
      console.error(`Error fetching resumes for job ${jobId}:`, err);
      if (err.response) { setError(`Failed to fetch resumes (${err.response.status})`); }
      else if (err.request) { setError('No response from server.');}
      else { setError(`Error: ${err.message}`); }
      setIsPolling(false);
    } finally {
      if (showLoadingIndicator) setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadResumes(true);
    let intervalId = null;
    if (isPolling) {
      console.log(`Polling for Job ID: ${jobId} enabled.`);
      intervalId = setInterval(() => {
        console.log(`Polling resumes for Job ID: ${jobId}...`);
        loadResumes(false); // Poll without showing main spinner
      }, 7000); // Poll every 7 seconds (adjust as needed)
    } else {
      console.log(`Polling for Job ID: ${jobId} stopped or not needed.`);
    }
    return () => {
      if (intervalId) {
        console.log(`Clearing polling interval for Job ID: ${jobId}`);
        clearInterval(intervalId);
      }
    };
  }, [jobId, loadResumes, isPolling]);


  const handleDeleteResume = async (resumeIdToDelete) => {
    if (!window.confirm(`Are you sure you want to delete resume "${resumes.find(r=>r.id === resumeIdToDelete)?.filename || `ID ${resumeIdToDelete}`}"? This action cannot be undone.`)) {
      return;
    }

    setDeletingId(resumeIdToDelete);
    setError(null);

    try {
      await deleteResume(resumeIdToDelete); // Call API to delete
      // Optimistically update UI then refresh from server for consistency
      setResumes(prevResumes => prevResumes.filter(r => r.id !== resumeIdToDelete));
      // alert(`Resume ID ${resumeIdToDelete} marked for deletion.`); // Optional: use MUI Snackbar later
      // Re-fetch the list to confirm deletion and get updated order
      loadResumes(false); // Refresh list without primary loading indicator
    } catch (err) {
      console.error(`Error deleting resume ID ${resumeIdToDelete}:`, err);
      setError(err.response?.data?.error || err.message || 'Failed to delete resume.');
    } finally {
      setDeletingId(null); // Clear deleting indicator
    }
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Button
        variant="outlined"
        startIcon={<RefreshIcon />}
        onClick={() => loadResumes(true)}
        disabled={loading && resumes.length === 0} // Only disable if full loading, not polling
        sx={{ mb: 1.5 }}
      >
        {loading && resumes.length === 0 ? 'Refreshing...' : 'Refresh List'}
      </Button>

      {loading && resumes.length === 0 && (
         <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
         </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

      {!loading && resumes.length === 0 && !error && <Typography>No resumes uploaded for this job yet.</Typography>}

      <List disablePadding> {/* MUI List component */}
        {resumes.map((resume) => (
          <Paper
            key={resume.id}
            elevation={1}
            sx={{
              mb: 0.8,
              p: 1.2, // Padding inside each item
              backgroundColor: 'background.paper',
              borderRadius: '6px',
            }}
          >
            <Grid container alignItems="center" spacing={0.6}>
              {/* Filename and details */}
              <Grid item xs={12} sm={5} md={6} sx={{ wordBreak: 'break-all' }}>
                <Typography variant="body1" component="div" fontWeight="500">
                  {resume.filename}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ID: {resume.id} | Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}
                </Typography>
              </Grid>

              {/* Score, Status, Actions */}
              <Grid item xs={12} sm={6} md={5} sx={{ display: 'flex', alignItems: 'center', justifyContent: {xs: 'flex-start', sm:'flex-end'}, mt: {xs: 0.8, sm: 0}, gap: {xs: 0.6, sm: 1, md: 1.2} }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.light', minWidth: '70px', textAlign:'right' }}>
                   Score: {formatScore(resume.score)}
                </Typography>
                <Chip
                  icon={getStatusIcon(resume.status)}
                  label={resume.status}
                  color={getStatusChipColor(resume.status)}
                  size="small"
                />
                <Tooltip title="Download Original Resume">
                  <IconButton
                     component="a"
                     href={`${import.meta.env.VITE_API_BASE_URL}/api/resumes/${resume.id}/download`}
                     target="_blank"
                     rel="noopener noreferrer"
                     color="primary"
                     size="small"
                     disabled={!resume.filepath}
                  >
                      <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete Resume">
                  <span> {/* Span for Tooltip on disabled button */}
                    <IconButton
                      color="error"
                      size="small"
                      onClick={() => handleDeleteResume(resume.id)}
                      disabled={deletingId === resume.id}
                    >
                      {deletingId === resume.id ? <CircularProgress size={20} color="inherit" /> : <DeleteIcon />}
                    </IconButton>
                  </span>
                </Tooltip>
              </Grid>
            </Grid>
          </Paper>
        ))}
      </List>
    </Box>
  );
}

export default ResumeList;