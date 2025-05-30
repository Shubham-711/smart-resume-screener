// frontend/src/pages/JobListPage.jsx
import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { fetchJobs } from '../api/apiService';
import {
  Box, Typography, CircularProgress, Alert, Card,
  CardContent, CardActions, Button
} from '@mui/material';

// sx prop for individual card styling
const cardSx = {
  width: '100%', // Card takes full width of its container
  maxWidth: '800px', // But card itself has a max width
  mb: 2.5,
  backgroundColor: 'background.paper', // Use theme paper color
  // For glassmorphism (can be added later if performance allows)
  // backgroundColor: 'rgba(31, 35, 44, 0.75)',
  // backdropFilter: 'blur(8px)',
  // WebkitBackdropFilter: 'blur(8px)',
  // border: '1px solid rgba(255, 255, 255, 0.12)',
  borderRadius: '8px', // Standard MUI card radius
  elevation: 3,
};

function JobListPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadJobs = async () => {
      try {
        setLoading(true); setError(null);
         console.log('FROM JobListPage.jsx -> Calling fetchJobs()');
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
    };
    loadJobs();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 120px)' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    // This Box will be centered by the Container in App.jsx
    // To center items *within* this page, use flex properties here
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Box sx={{ width: '100%', maxWidth: '800px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ color: 'text.primary' }}>
          Job Postings
        </Typography>
        <Button component={RouterLink} to="/create-job" variant="contained" color="primary">
          Create New Job
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2, width: '100%', maxWidth: '800px' }}>{error}</Alert>}

      {jobs.length === 0 && !error ? (
        <Typography sx={{ color: 'text.secondary' }}>No jobs found.</Typography>
      ) : (
        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          {jobs.map((job) => (
            <Card key={job.id} sx={cardSx}>
              <CardContent>
                <Typography
                  variant="h6"
                  component={RouterLink}
                  to={`/jobs/${job.id}`}
                  sx={{ textDecoration: 'none', color: 'primary.light', '&:hover': { color: 'primary.main' } }}
                >
                  {job.title || 'Untitled Job'}
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  ID: {job.id} | Created: {new Date(job.created_at).toLocaleDateString()} | Required Years: {job.required_years ?? 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, maxHeight: '4.5em', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                  {job.description ? job.description : 'No description.'}
                </Typography>
              </CardContent>
              <CardActions sx={{ pt: 0, justifyContent: 'flex-start' }}>
                <Button
                  component={RouterLink}
                  to={`/jobs/${job.id}`}
                  size="small"
                  color="secondary" // Using secondary color for this button
                  sx={{ fontWeight: 'medium' }} // Make text slightly bolder
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