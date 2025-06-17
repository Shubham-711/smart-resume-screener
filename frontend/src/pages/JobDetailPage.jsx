// frontend/src/pages/JobDetailPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { fetchJobDetails } from '../api/apiService';
import { Box, Typography, Paper, Button, CircularProgress, Alert, Divider, useTheme } from '@mui/material';
import ResumeList from '../components/ResumeList';
import ResumeUpload from '../components/ResumeUpload';
import { glassMorphismSx, glowButtonSx } from '../styles/commonStyles'; // Import shared styles

function JobDetailPage() {
  const theme = useTheme(); // Hook to access the theme
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshCounter, setRefreshCounter] = useState(0);

  const loadJobDetails = useCallback(async () => {
    if (!jobId) return;
    try { setLoading(true); setError(null); const response = await fetchJobDetails(jobId); setJob(response.data); }
    catch (err) { console.error(`Error fetching job details for ID ${jobId}:`, err); if (err.response && err.response.status === 404) setError(`Job with ID ${jobId} not found.`); else if (err.request) setError('Failed to fetch job details: No response from server.'); else setError(`Failed to fetch job details: ${err.message}`); setJob(null); }
    finally { setLoading(false); }
  }, [jobId]);

  useEffect(() => { loadJobDetails(); }, [loadJobDetails, refreshCounter]); // Add refreshCounter to re-fetch job details too (optional)

  const handleUploadSuccess = () => {
    console.log('Upload successful in parent, incrementing refresh key...');
    setRefreshCounter(prev => prev + 1);
  };

  if (loading) {
    return ( <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 128px)' }}> <CircularProgress /> </Box> );
  }
  if (error) {
    return <Alert severity="error" sx={{ m: 2, width: '100%', maxWidth: '800px', mx: 'auto' }}>{error}</Alert>;
  }
  if (!job) {
    return <Typography sx={{ p: 3, textAlign: 'center' }}>Job data could not be loaded or job not found.</Typography>;
  }

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Paper elevation={0} sx={{ ...glassMorphismSx(theme), width: '100%', maxWidth: '800px', mb: 3 }}>
        <Box sx={{p: {xs: 2, sm: 3}}}> {/* Inner padding for content */}
            <Typography variant="h4" component="h1" gutterBottom sx={{ color: 'text.primary', fontWeight: 'bold' }}>
              Job Details: {job.title}
            </Typography>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              <strong>ID:</strong> {job.id}
            </Typography>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              <strong>Created:</strong> {new Date(job.created_at).toLocaleString()}
            </Typography>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              <strong>Required Years:</strong> {job.required_years ?? 'N/A'}
            </Typography>
            <Typography variant="h6" component="h3" sx={{ mt: 2, color: 'text.primary' }}>
              Description:
            </Typography>
            <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.95em', mt: 1, p: 2, backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 1, color: 'text.secondary', maxHeight: '300px', overflowY: 'auto' }}>
              {job.description}
            </Box>
        </Box>
      </Paper>

      <Box sx={{ width: '100%', maxWidth: '800px', mb: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ color: 'text.primary', fontWeight: 500 }}>
          Upload Resumes
        </Typography>
        <ResumeUpload jobId={job.id} onUploadSuccess={handleUploadSuccess} />
      </Box>

      <Divider sx={{ width: '100%', maxWidth: '800px', my: 3, borderColor: 'rgba(255,255,255,0.2)' }} />

      <Box sx={{ width: '100%', maxWidth: '800px' }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ color: 'text.primary', fontWeight: 500 }}>
          Screening Results
        </Typography>
         <ResumeList jobId={job.id} key={refreshCounter} />
      </Box>

       <Button component={RouterLink} to="/jobs" variant="outlined" color="primary" sx={{ ...glowButtonSx(theme), mt: 4 }}>
          Back to Job List
       </Button>
    </Box>
  );
}

export default JobDetailPage;