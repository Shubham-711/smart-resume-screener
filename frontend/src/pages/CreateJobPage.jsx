// frontend/src/pages/CreateJobPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createJob } from '../api/apiService';
import { Box, Typography, TextField, Button, CircularProgress, Alert, Paper, useTheme } from '@mui/material';
import { glassMorphismPaperSx, glowButtonSx } from '../styles/commonStyles'; // Import your shared styles

function CreateJobPage() {
  const theme = useTheme();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requiredYears, setRequiredYears] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault(); setIsLoading(true); setError(null); setSuccessMessage('');
    if (!title.trim() || !description.trim()) { setError('Job Title and Description cannot be empty.'); setIsLoading(false); return; }
    const jobData = { title: title.trim(), description: description.trim(), required_years: requiredYears ? parseInt(requiredYears, 10) : null, };
    if (requiredYears && (isNaN(jobData.required_years) || jobData.required_years < 0)) { setError('Required Years must be a valid non-negative number.'); setIsLoading(false); return; }
    try {
      const response = await createJob(jobData);
      setSuccessMessage(`Job "${response.data.title}" created successfully with ID: ${response.data.id}`);
      setTitle(''); setDescription(''); setRequiredYears('');
      setTimeout(() => { navigate('/jobs'); }, 2500); // Slightly longer for user to read message
    } catch (err) {
      console.error("Error creating job:", err);
      let errMsg = 'Failed to create job.';
      if (err.response && err.response.data) {
        errMsg = err.response.data.error || errMsg;
        if (err.response.data.messages) {
          errMsg += ` Details: ${JSON.stringify(err.response.data.messages)}`;
        }
      } else if (err.request) { errMsg = 'No response from server. Please check backend.'; }
      else { errMsg = err.message; }
      setError(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // This top-level Box uses flex to center its direct child (the Paper component)
    // It takes full width available from the App.jsx Container
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ fontWeight: 'bold', mb:3 }}>
        Create New Job Posting
      </Typography>

      {/* The Paper component is the form container. It has a maxWidth and mx: 'auto' */}
      <Paper
        component="form" // Make Paper the form element
        onSubmit={handleSubmit}
        noValidate
        elevation={0} // Use sx for custom shadow from glassMorphismPaperSx
        sx={{
          ...glassMorphismPaperSx(theme), // Apply base glass style
          width: '100%',                  // Take available width
          maxWidth: '700px',              // Limit form width
          // mx: 'auto', // Centering handled by parent Box's alignItems: 'center'
        }}
      >
        {/* Inner Box for padding actual form fields if Paper's padding isn't enough */}
        <Box sx={{ p: {xs: 1, sm: 2} }}>
          <TextField
            label="Job Title"
            // variant="filled" // Default from theme now
            fullWidth
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            margin="normal"
            disabled={isLoading}
          />
          <TextField
            label="Job Description"
            // variant="filled"
            fullWidth
            required
            multiline
            rows={10}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            margin="normal"
            disabled={isLoading}
          />
          <TextField
            label="Required Years (Optional)"
            // variant="filled"
            type="number"
            value={requiredYears}
            onChange={(e) => setRequiredYears(e.target.value)}
            margin="normal"
            InputProps={{ inputProps: { min: 0 } }}
            sx={{ width: { xs: '100%', sm: '200px' }}}
            disabled={isLoading}
          />
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', position: 'relative' }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={isLoading}
              sx={glowButtonSx(theme)}
              size="large"
            >
              <Box component="span" sx={{ visibility: isLoading ? 'hidden' : 'visible' }}>
                 Create Job
              </Box>
            </Button>
            {isLoading && (
              <CircularProgress
                size={24}
                sx={{
                  color: 'primary.contrastText',
                  position: 'absolute', top: '50%', left: '50%',
                  marginTop: '-12px', marginLeft: '-12px',
                }}
              />
            )}
          </Box>
        </Box>
      </Paper>

      {successMessage && <Alert severity="success" sx={{ mt: 2, width: '100%', maxWidth: '700px' }}>{successMessage}</Alert>}
      {error && <Alert severity="error" sx={{ mt: 2, width: '100%', maxWidth: '700px' }}>{error}</Alert>}
    </Box>
  );
}
export default CreateJobPage;