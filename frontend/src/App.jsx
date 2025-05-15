// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { AppBar, Toolbar, Container, Button, Box, Typography, CssBaseline } from '@mui/material';
import HomePage from './pages/HomePage';
import JobListPage from './pages/JobListPage';
import JobDetailPage from './pages/JobDetailPage';
import CreateJobPage from './pages/CreateJobPage';

function App() {
  return (
    <Router>
      <CssBaseline />
      <AppBar
        position="fixed"
        elevation={1}
        sx={{
          backgroundColor: (theme) => theme.palette.background.paper,
          opacity: 0.95,
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
        }}
      >
        <Container maxWidth="lg">
          <Toolbar disableGutters>
            <Typography
              variant="h6"
              noWrap
              component={NavLink}
              to="/"
              sx={{
                mr: 2,
                display: { xs: 'none', md: 'flex' },
                fontFamily: 'monospace',
                fontWeight: 700,
                letterSpacing: '.1rem',
                color: 'text.primary', // Should be white from theme
                textDecoration: 'none',
                '&:hover': {
                    color: 'primary.light'
                }
              }}
            >
              Resume Screener
            </Typography>

            <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: { xs: 'flex-end', md: 'flex-start' } }}>
              <Button
                component={NavLink}
                to="/jobs"
                end 
                // Remove color="primary" prop if it was there by default
                // Or explicitly set a color that results in white text
                // color="inherit" // This will inherit the AppBar's text color (usually white)
                sx={(theme) => ({
                  my: 2,
                  mx: 1.5,
                  color: theme.palette.text.primary, // <<< EXPLICITLY use primary text color (white)
                  display: 'block',
                  '&.active': { // Style for active NavLink
                    color: theme.palette.primary.main, // Active link uses primary theme color
                    fontWeight: 'bold',
                  },
                  '&:hover:not(.active)': { // Hover for non-active links
                    backgroundColor: 'action.hover', // Subtle background on hover
                    // color: theme.palette.text.secondary, // Optional: slightly dimmer text on hover
                  }
                })}
              >
                Job List
              </Button>
              <Button
                component={NavLink}
                to="/create-job"
                // color="inherit"
                sx={(theme) => ({
                  my: 2,
                  mx: 1.5,
                  color: theme.palette.text.primary, // <<< EXPLICITLY use primary text color (white)
                  display: 'block',
                  '&.active': {
                    color: theme.palette.primary.main, // Active link uses primary theme color
                    fontWeight: 'bold',
                  },
                  '&:hover:not(.active)': {
                    backgroundColor: 'action.hover',
                  }
                })}
              >
                Create Job
              </Button>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* ... rest of the App.jsx ... */}
      <Toolbar />
      <Container component="main" maxWidth="lg" sx={{ mt: 4, mb: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Routes>
        <Route path="/" element={<HomePage />} /> {/* <<< NEW: Root route is HomePage */}
        <Route path="/jobs" element={<JobListPage />} /> {/* <<< NEW: Job List is now at /jobs */}
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/create-job" element={<CreateJobPage />} />
          <Route path="*" element={<Typography variant="h4" align="center" sx={{ mt: 5 }}>404 Page Not Found</Typography>} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;