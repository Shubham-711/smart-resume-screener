// frontend/src/pages/CreateJobPage.jsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createJob } from '../api/apiService';
import { Box, Typography, TextField, Button, CircularProgress, Alert, Paper } from '@mui/material';

// Define sx styles reusable within this component (or move to a shared file)
const glassCardSx = { // Using Paper as the card base here
  p: { xs: 2, sm: 3 }, // Responsive padding
  backgroundColor: 'rgba(31, 35, 44, 0.6)',
  backdropFilter: 'blur(8px)',
  WebkitBackdropFilter: 'blur(8px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  borderRadius: '12px',
};

const glowButtonSx = {
  fontWeight: 'bold',
  mt: 2,
  mb: 1,
  minWidth: '120px', // Give button some minimum width
  boxShadow: {
    xs: 'none',
    ':hover': theme => `0 0 12px ${theme.palette.primary.main}, 0 0 25px ${theme.palette.primary.main}`
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


function CreateJobPage() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requiredYears, setRequiredYears] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => { /* ... keep existing handleSubmit logic ... */
      event.preventDefault(); setIsLoading(true); setError(null); setSuccessMessage(''); if (!title.trim() || !description.trim()) { setError('Job Title and Description cannot be empty.'); setIsLoading(false); return; } const jobData = { title: title.trim(), description: description.trim(), required_years: requiredYears ? parseInt(requiredYears, 10) : null, }; if (requiredYears && (isNaN(jobData.required_years) || jobData.required_years < 0)) { setError('Required Years must be a valid non-negative number.'); setIsLoading(false); return; } try { const response = await createJob(jobData); setSuccessMessage(`Job "${response.data.title}" created successfully! ID: ${response.data.id}`); console.log(`Job created successfully: ${response.data.id}`); setTitle(''); setDescription(''); setRequiredYears(''); setTimeout(() => { navigate('/'); }, 2000); } catch (err) { console.error("Error creating job:", err); if (err.response && err.response.data && err.response.data.error) { setError(`Failed to create job: ${err.response.data.error}` + (err.response.data.messages ? ` - ${JSON.stringify(err.response.data.messages)}` : '')); } else if (err.request) { setError('Failed to create job: No response from server.'); } else { setError(`Failed to create job: ${err.message}`); } } finally { setIsLoading(false); }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Create New Job Posting
      </Typography>

      {/* Apply glassCardSx to the Paper component */}
      <Paper elevation={0} sx={glassCardSx}> {/* elevation 0 if using border/backdrop */}
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="Job Title"
            variant="outlined" // Or "filled" or "standard"
            fullWidth
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            margin="normal"
            disabled={isLoading}
          />
          <TextField
            label="Job Description"
            variant="outlined"
            fullWidth
            required
            multiline
            rows={8}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            margin="normal"
            disabled={isLoading}
          />
          <TextField
            label="Required Years (Optional)"
            variant="outlined"
            type="number"
            value={requiredYears}
            onChange={(e) => setRequiredYears(e.target.value)}
            margin="normal"
            InputProps={{ inputProps: { min: 0 } }}
            sx={{ width: { xs: '100%', sm: '200px' } }} // Responsive width
            disabled={isLoading}
          />
          <Box sx={{ mt: 2, position: 'relative', display: 'inline-block' }}> {/* Container for button + spinner */}
            <Button
              type="submit"
              variant="contained" // Contained button often looks better with glow
              color="primary"
              disabled={isLoading}
              sx={glowButtonSx} // Apply glow style
            >
              {/* Add padding for spinner */}
              <Box component="span" sx={{ visibility: isLoading ? 'hidden' : 'visible' }}>
                 Create Job
              </Box>
            </Button>
            {isLoading && (
              <CircularProgress
                size={24}
                sx={{
                  color: 'primary.main', // Use theme color
                  position: 'absolute',
                  top: '50%', left: '50%',
                  marginTop: '-12px', marginLeft: '-12px',
                }}
              />
            )}
          </Box>
        </Box>
      </Paper>

      {successMessage && <Alert severity="success" sx={{ mt: 2 }}>{successMessage}</Alert>}
      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
    </Box>
  );
}

export default CreateJobPage;