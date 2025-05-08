// frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
// MUI Components
import { AppBar, Toolbar, Container, Button, Box, CssBaseline } from '@mui/material'; // Added CssBaseline here too just in case
// Import Pages
import JobListPage from './pages/JobListPage';
import JobDetailPage from './pages/JobDetailPage';
import CreateJobPage from './pages/CreateJobPage';

function App() {
  return (
    <Router>
      <CssBaseline /> {/* Ensure baseline styles */}
      <AppBar position="fixed" elevation={2} sx={{
          // Glass effect for AppBar
          backgroundColor: 'rgba(22, 24, 29, 0.8)', // Dark transparent background
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)', // Safari
        }}>
        <Container maxWidth="lg"> {/* Constrain toolbar content */}
          <Toolbar disableGutters> {/* disableGutters removes default padding */}
            {/* Logo/Title Placeholder */}
            <Typography variant="h6" noWrap component="div" sx={{ mr: 2, flexGrow: { xs: 1, md: 0} }}> {/* Adjust flexGrow */}
              Resume Screener
            </Typography>

            {/* Navigation Links */}
            <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: { xs: 'flex-end', md: 'flex-start'} }}> {/* Adjust layout */}
              <Button
                component={NavLink}
                to="/"
                sx={{ color: 'text.secondary', mr: 1, '&.active': { color: 'primary.main', fontWeight: 'bold' } }}
              >
                Job List
              </Button>
              <Button
                component={NavLink}
                to="/create-job"
                sx={{ color: 'text.secondary', '&.active': { color: 'primary.main', fontWeight: 'bold' } }}
              >
                Create Job
              </Button>
            </Box>
            {/* Future Auth Button can go here */}
          </Toolbar>
        </Container>
      </AppBar>

      {/* Offset content below AppBar */}
      <Toolbar />

      {/* Main content area */}
      <Container component="main" maxWidth="lg" sx={{ mt: 4, mb: 6 }}>
        <Routes>
          <Route path="/" element={<JobListPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/create-job" element={<CreateJobPage />} />
          <Route path="*" element={<Box sx={{ p: 3 }}><Typography variant="h4">404 Page Not Found</Typography></Box>} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;

// Import Typography if not already imported
import { Typography } from '@mui/material';