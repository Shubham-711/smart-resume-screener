// frontend/src/pages/HomePage.jsx
import React from 'react';
import { Box, Typography, Paper, Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom'; // For navigation buttons

// Reusable sx prop for glass-like Paper (can be moved to a shared styles file later)
const glassPaperSx = {
  p: { xs: 2, sm: 3, md: 4 },
  backgroundColor: 'rgba(31, 35, 44, 0.7)', // theme.palette.background.paper with more transparency
  backdropFilter: 'blur(10px)',
  WebkitBackdropFilter: 'blur(10px)',
  border: '1px solid rgba(255, 255, 255, 0.12)',
  borderRadius: '16px', // More rounded
  textAlign: 'center', // Center text within the paper
  maxWidth: '800px', // Limit width
  mx: 'auto', // Center the paper itself if its parent is a flex container
  color: 'text.primary',
};

const glowButtonSx = { // Reusing a similar button style
    fontWeight: 'bold',
    mt: 3,
    mb: 1,
    minWidth: '150px',
    boxShadow: {
      xs: 'none',
      ':hover': theme => `0 0 12px ${theme.palette.primary.light}, 0 0 25px ${theme.palette.primary.light}`
    },
    transition: theme => theme.transitions.create(['box-shadow', 'background-color'], {
      duration: theme.transitions.duration.short,
    }),
  };


function HomePage() {
  return (
    // This Box will be centered by the Container in App.jsx
    // display: flex, flexDirection: column, alignItems: center ensures its children are centered
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
      <Paper elevation={3} sx={glassPaperSx}>
        <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 700, color: 'primary.light' }}>
          Welcome to the Smart Resume Screener!
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph sx={{ maxWidth: '600px', mx: 'auto' }}>
          Streamline your hiring process by automatically screening resumes against job descriptions.
          Our AI-powered system helps you identify the most relevant candidates quickly and efficiently.
        </Typography>
        <Typography variant="body1" paragraph sx={{ mt: 2, maxWidth: '600px', mx: 'auto' }}>
          Get started by creating a new job posting or viewing existing ones to manage resumes.
          This tool leverages Natural Language Processing to match skills and rank applicants, saving you valuable time.
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Button
            component={RouterLink}
            to="/create-job"
            variant="contained"
            color="primary"
            size="large"
            sx={{ ...glowButtonSx, mr: 2 }}
          >
            Create New Job
          </Button>
          <Button
            component={RouterLink}
            to="/jobs" // This currently points to Job List, which is fine as a primary action
            variant="outlined"
            color="secondary"
            size="large"
            sx={{ ...glowButtonSx, backgroundColor:'secondary.main', color:'white', '&:hover': {backgroundColor: 'secondary.dark'} }}
          >
            View Job List
          </Button>
        </Box>
      </Paper>

      {/* You can add more sections here later if needed */}
      {/* Example:
      <Paper elevation={3} sx={{...glassPaperSx, mt: 4}}>
        <Typography variant="h5" gutterBottom>How it Works</Typography>
        <Typography variant="body1">
          1. Create a job. 2. Upload resumes. 3. View ranked candidates.
        </Typography>
      </Paper>
      */}
    </Box>
  );
}

export default HomePage;