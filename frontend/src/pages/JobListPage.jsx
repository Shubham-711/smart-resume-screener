// frontend/src/pages/JobListPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { fetchJobs } from '../api/apiService';
import {
  Box, Typography, CircularProgress, Alert, Card,
  CardContent, CardActions, Button, useTheme // Import useTheme
} from '@mui/material';
import { glassMorphismSx, glowButtonSx } from '../styles/commonStyles'; // Import shared styles

function JobListPage() {
  const theme = useTheme();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true); setError(null);
      const response = await fetchJobs();
      setJobs(response.data || []);
    } catch (err) {
      console.error("Error fetching jobs:", err);
      if (err.response) { setError(`Failed to fetch jobs (${err.response.status})`); }
      else if (err.request) { setError('No response from server. Is backend running?'); }
      else { setError(`Error: ${err.message}`); }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 128px)' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}> {/* Centers its children */}
      <Box sx={{ width: '100%', maxWidth: '800px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ color: 'text.primary', fontWeight: 'bold' }}>
          Job Postings
        </Typography>
        <Button component={RouterLink} to="/create-job" variant="contained" color="primary" sx={glowButtonSx(theme)}>
          Create New Job
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2, width: '100%', maxWidth: '800px' }}>{error}</Alert>}

      {jobs.length === 0 && !error ? (
        <Typography sx={{ color: 'text.secondary', mt: 3 }}>No jobs found.</Typography>
      ) : (
        // This inner Box already has alignItems: 'center' from its parent
        <Box sx={{ width: '100%' }}>
          {jobs.map((job) => (
            <Card key={job.id} sx={{ ...glassMorphismSx(theme), width: '100%', maxWidth: '800px', mx: 'auto' /* Center card if parent isn't flex centering items */ }} elevation={0}>
              <CardContent>
                <Typography
                  variant="h6"
                  component={RouterLink}
                  to={`/jobs/${job.id}`}
                  sx={{ textDecoration: 'none', color: 'primary.light', '&:hover': { color: 'primary.main'}, fontWeight: 500 }}
                >
                  {job.title || 'Untitled Job'}
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                  ID: {job.id} | Created: {new Date(job.created_at).toLocaleDateString()} | Required Years: {job.required_years ?? 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5, height: '4.5em', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                  {job.description ? job.description : 'No description.'}
                </Typography>
              </CardContent>
              <CardActions sx={{ pt: 0, justifyContent: 'flex-start', pl: {xs: 1, sm: 2} }}> {/* Adjusted padding */}
                <Button
                  component={RouterLink}
                  to={`/jobs/${job.id}`}
                  size="small"
                  color="secondary"
                  sx={{ fontWeight: 'medium',  textTransform: 'none' }} // Keep text case as is
                >
                  View Details & Resumes
                </Button>
              </CardActions>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}

export default JobListPage;