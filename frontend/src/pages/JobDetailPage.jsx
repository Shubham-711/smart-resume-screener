// frontend/src/pages/JobDetailPage.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { fetchJobDetails } from '../api/apiService';
// MUI Components
import { Box, Typography, Paper, Button, CircularProgress, Alert, Divider } from '@mui/material';

// --- IMPORT THE COMPONENTS ---
import ResumeList from '../components/ResumeList'; // Adjust path if needed
import ResumeUpload from '../components/ResumeUpload'; // Adjust path if needed
// ---------------------------

function JobDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // State to trigger refresh of ResumeList after upload
  const [refreshCounter, setRefreshCounter] = useState(0); // Key state

  const loadJobDetails = useCallback(async () => {
      // ... (keep existing fetch logic for job details) ...
       if (!jobId) return; try { setLoading(true); setError(null); const response = await fetchJobDetails(jobId); setJob(response.data); } catch (err) { console.error(`Error fetching job details for ID ${jobId}:`, err); if (err.response && err.response.status === 404) setError(`Job with ID ${jobId} not found.`); else if (err.request) setError('Failed to fetch job details: No response from server.'); else setError(`Failed to fetch job details: ${err.message}`); setJob(null); } finally { setLoading(false); }
  }, [jobId]);

  useEffect(() => { loadJobDetails(); }, [loadJobDetails]);

  // Callback function for ResumeUpload component to trigger refresh
  const handleUploadSuccess = () => {
    console.log('Upload successful in parent, incrementing refresh key...');
    setRefreshCounter(prev => prev + 1); // Increment key to force ResumeList re-mount
  };

  // --- Render Logic ---
  if (loading) { /* ... loading indicator ... */
    return ( <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}> <CircularProgress /> </Box> );
  }
  if (error) { /* ... error display ... */
    return <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>;
  }
  if (!job) { /* ... no job data ... */
    return <Typography sx={{ p: 3 }}>Job data could not be loaded.</Typography>;
  }

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        {/* ... Job Details content (Title, Description, etc.) ... */}
        <Typography variant="h4" component="h1" gutterBottom> Job Details: {job.title} </Typography>
        {/* ... other details ... */}
      </Paper>

      <Divider sx={{ my: 3 }} />

      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Upload Resumes
        </Typography>
        {/* --- RENDER ResumeUpload COMPONENT --- */}
        {/* Pass jobId and the callback function */}
        <ResumeUpload jobId={job.id} onUploadSuccess={handleUploadSuccess} />
        {/* --------------------------------------- */}
      </Box>

      <Divider sx={{ my: 3 }} />

      <Box>
        <Typography variant="h5" component="h2" gutterBottom>
          Screening Results
        </Typography>
         {/* --- RENDER ResumeList COMPONENT --- */}
         {/* Pass jobId AND the key prop */}
         <ResumeList jobId={job.id} key={refreshCounter} />
         {/* ----------------------------------- */}
      </Box>

       <Button component={RouterLink} to="/" variant="outlined" color="primary" sx={{ mt: 3 }}>
          Back to Job List
       </Button>
    </Box>
  );
}

export default JobDetailPage;