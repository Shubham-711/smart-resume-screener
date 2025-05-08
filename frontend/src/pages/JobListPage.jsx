// frontend/src/pages/JobListPage.jsx

import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { fetchJobs } from '../api/apiService';
import {
  Box, Typography, CircularProgress, Alert, Card,
  CardContent, CardActions, Button
} from '@mui/material';

// Define sx styles reusable within this component
const glassCardSx = {
  mb: 2.5, // Margin bottom
  backgroundColor: 'rgba(31, 35, 44, 0.6)', // bg.paper with transparency
  backdropFilter: 'blur(8px)',
  WebkitBackdropFilter: 'blur(8px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  borderRadius: '12px',
  transition: 'background-color 0.3s ease',
  '&:hover': {
    backgroundColor: 'rgba(44, 48, 58, 0.75)',
  }
};

const glowButtonSx = {
  fontWeight: 'bold',
  mt: 2, // Add margin top
  mb: 1,
  boxShadow: { // Define base and hover shadows using theme colors
    xs: 'none', // No initial glow unless desired
    ':hover': theme => `0 0 12px ${theme.palette.primary.main}, 0 0 25px ${theme.palette.primary.main}`
  },
  transition: theme => theme.transitions.create(['box-shadow', 'background-color'], {
    duration: theme.transitions.duration.short,
  }),
  '&.Mui-disabled': { // Style disabled state
    boxShadow: 'none',
    backgroundColor: 'action.disabledBackground'
  }
};


function JobListPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { /* ... keep existing useEffect logic ... */
      const loadJobs = async () => { try { setLoading(true); setError(null); const response = await fetchJobs(); setJobs(response.data || []); } catch (err) { console.error("Error fetching jobs:", err); if (err.response) { setError(`Failed to fetch jobs (${err.response.status})`); } else if (err.request) { setError('No response from server. Is backend running?');} else { setError(`Error: ${err.message}`); } } finally { setLoading(false); } }; loadJobs();
  }, []);

  if (loading) { /* ... keep loading state ... */
      return ( <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}> <CircularProgress /> </Box> );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Job Postings
        </Typography>
        <Button component={RouterLink} to="/create-job" variant="contained" color="primary" sx={glowButtonSx}> {/* Apply glow style */}
          Create New Job
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {jobs.length === 0 && !error ? (
        <Typography>No jobs found.</Typography>
      ) : (
        <Box>
          {jobs.map((job) => (
            // --- APPLY glassCardSx HERE ---
            <Card key={job.id} sx={glassCardSx} elevation={0}> {/* Use sx prop, maybe elevation 0 if border/backdrop is enough */}
              <CardContent>
                <Typography variant="h6" component={RouterLink} to={`/jobs/${job.id}`} sx={{ textDecoration: 'none', color: 'text.primary', '&:hover': { color: 'primary.main'} }}>
                  {job.title || 'Untitled Job'}
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  ID: {job.id} | Created: {new Date(job.created_at).toLocaleDateString()} | Required Years: {job.required_years ?? 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, height: '4.5em', overflow: 'hidden', /* Basic multiline ellipsis */ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                  {job.description ? job.description : 'No description.'}
                </Typography>
              </CardContent>
              <CardActions sx={{pt: 0}}> {/* Remove padding top */}
                <Button component={RouterLink} to={`/jobs/${job.id}`} size="small" color="primary">
                  View Details & Resumes
                </Button>
              </CardActions>
            </Card>
            // ------------------------------
          ))}
        </Box>
      )}
    </Box>
  );
}

export default JobListPage;