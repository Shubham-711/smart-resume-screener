// frontend/src/components/ResumeList.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { fetchResumesForJob } from '../api/apiService'; // Adjust path if needed
// MUI Components
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon, // Optional: for icons
  Paper, // Use Paper for list item background/elevation
  Chip, // For status display
  Button,
  CircularProgress,
  Alert,
  IconButton, // For potential icons on buttons
  Tooltip // For hints on buttons
} from '@mui/material';
// MUI Icons (Optional, install @mui/icons-material if not already)
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HourglassTopIcon from '@mui/icons-material/HourglassTop';
import PendingIcon from '@mui/icons-material/Pending';


// Helper to format score
const formatScore = (score) => {
  if (score === null || score === undefined) {
    return '--'; // Placeholder for pending/processing/failed
  }
  // Format as percentage with 1 decimal place
  return `${(score * 100).toFixed(1)}%`;
};

// Helper to determine Chip color based on status
const getStatusChipColor = (status) => {
  switch (status) {
    case 'COMPLETED': return 'success';
    case 'PROCESSING': return 'warning';
    case 'PENDING': return 'default'; // Or 'info'
    case 'FAILED': return 'error';
    default: return 'default';
  }
};

// Helper to get an icon based on status (optional)
const getStatusIcon = (status) => {
    switch (status) {
        case 'COMPLETED': return <CheckCircleOutlineIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        case 'PROCESSING': return <HourglassTopIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        case 'PENDING': return <PendingIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        case 'FAILED': return <ErrorOutlineIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />;
        default: return null;
      }
}

function ResumeList({ jobId }) { // Accept jobId as a prop
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);

  const loadResumes = useCallback(async (showLoadingIndicator = true) => {
    if (!jobId) return;
    if (showLoadingIndicator) setLoading(true); // Only show main spinner on manual refresh/initial load
    setError(null);
    try {
      const response = await fetchResumesForJob(jobId);
      const fetchedResumes = response.data || [];
      setResumes(fetchedResumes);

      // Check if polling should continue
      const stillProcessing = fetchedResumes.some(r => r.status === 'PENDING' || r.status === 'PROCESSING');
      setIsPolling(stillProcessing);

    } catch (err) {
      console.error(`Error fetching resumes for job ${jobId}:`, err);
       if (err.response) { setError(`Failed to fetch resumes (${err.response.status})`); }
       else if (err.request) { setError('No response from server.');}
       else { setError(`Error: ${err.message}`); }
      setIsPolling(false); // Stop polling on error
    } finally {
      if (showLoadingIndicator) setLoading(false);
    }
  }, [jobId]); // Recreate only if jobId changes

  // Initial fetch and polling setup
  useEffect(() => {
    loadResumes(true); // Initial load with loading indicator

    let intervalId = null;
    if (isPolling) {
      console.log(`Starting polling for Job ID: ${jobId}`);
      // Use loadResumes with showLoadingIndicator = false for subsequent polls
      intervalId = setInterval(() => loadResumes(false), 5000); // Poll every 5 seconds
    } else {
      console.log(`Polling stopped or not needed for Job ID: ${jobId}`);
    }

    // Cleanup function
    return () => {
      if (intervalId) {
        console.log(`Clearing polling interval for Job ID: ${jobId}`);
        clearInterval(intervalId);
      }
    };
  }, [jobId, loadResumes, isPolling]); // Dependencies


  // --- Render Logic ---
  return (
    <Box sx={{ mt: 2 }}> {/* Add some margin top */}
      <Button
        variant="outlined"
        startIcon={<RefreshIcon />}
        onClick={() => loadResumes(true)} // Pass true to show loading on manual refresh
        disabled={loading}
        sx={{ mb: 2 }} // Margin bottom for spacing
      >
        {loading ? 'Refreshing...' : 'Refresh List'}
      </Button>

      {/* Display overall loading indicator only on initial load/manual refresh */}
      {loading && resumes.length === 0 && (
         <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
         </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {!loading && resumes.length === 0 && !error && <Typography>No resumes uploaded yet.</Typography>}

      {/* Use MUI List component */}
      <List disablePadding>
        {resumes.map((resume) => (
          <Paper
            key={resume.id}
            elevation={2} // Subtle shadow
            sx={{
              mb: 1.5, // Margin between items
              p: 1.5, // Padding inside the paper
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap', // Allow wrapping on smaller screens
              backgroundColor: 'background.paper' // Use theme paper color
            }}
          >
            {/* Left side: Filename and details */}
            <Box sx={{ flexGrow: 1, mr: 2, wordBreak: 'break-all' }}> {/* Allow filename to wrap */}
              <Typography variant="body1" component="div" fontWeight="500">
                {resume.filename}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ID: {resume.id} | Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}
              </Typography>
            </Box>

            {/* Right side: Score, Status, Actions */}
            <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}> {/* Prevent shrinking */}
              <Typography variant="body2" sx={{ mr: 2, fontWeight: 'bold', color: 'primary.light' }}>
                 Score: {formatScore(resume.score)}
              </Typography>
              <Chip
                // icon={getStatusIcon(resume.status)} // Optional icon
                label={resume.status}
                color={getStatusChipColor(resume.status)}
                size="small"
                sx={{ mr: 1 }}
              />
              <Tooltip title="Download Original Resume">
                  {/* Link acts as the button container */}
                  <IconButton
                     component="a" // Render as an anchor tag
                     href={`${import.meta.env.VITE_API_BASE_URL}/api/resumes/${resume.id}/download`}
                     target="_blank" // Open in new tab
                     rel="noopener noreferrer" // Security
                     color="primary"
                     size="small"
                     disabled={!resume.filepath} // Disable if somehow no path exists
                  >
                      <DownloadIcon />
                  </IconButton>
              </Tooltip>
            </Box>
          </Paper>
        ))}
      </List>
    </Box>
  );
}

export default ResumeList;