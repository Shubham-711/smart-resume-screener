// frontend/src/App.jsx
import React from 'react';
import R3FBackground from './components/R3FBackground';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Container,
  Button,
  Box,
  Typography
} from '@mui/material';

// Pages
import HomePage from './pages/HomePage';
import JobListPage from './pages/JobListPage';
import JobDetailPage from './pages/JobDetailPage';
import CreateJobPage from './pages/CreateJobPage';



function App() {
  return (
    <Router>

      {/* Animated Background Div */}
      <div className="animated-background" />
      <R3FBackground />

      <AppBar
        position="fixed"
        elevation={1}
        sx={{
          backgroundColor: (theme) =>
            theme.palette.mode === 'dark'
              ? 'rgba(31, 35, 44, 0.85)'
              : 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          boxShadow: (theme) => theme.shadows[2]
        }}
      >
        <Container maxWidth="lg">
          <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography
              variant="h6"
              noWrap
              component={NavLink}
              to="/"
              sx={{
                mx: 'auto',
                fontWeight: 700,
                letterSpacing: '.12rem',
                fontFamily: 'monospace',
                color: 'white',
                textDecoration: 'none'
              }}
            >
              Resume Screener
            </Typography>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                component={NavLink}
                to="/jobs"
                sx={(theme) => ({
                  color: 'text.primary',
                  '&.active': {
                    color: theme.palette.primary.main,
                    fontWeight: 'bold'
                  }
                })}
              >
                Job List
              </Button>
              <Button
                component={NavLink}
                to="/create-job"
                sx={(theme) => ({
                  color: 'text.primary',
                  '&.active': {
                    color: theme.palette.primary.main,
                    fontWeight: 'bold'
                  }
                })}
              >
                Create Job
              </Button>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      <Toolbar /> {/* Spacer */}

      <Container component="main" maxWidth="lg" sx={{ mt: { xs: 2, sm: 3, md: 4 }, mb: 4 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/jobs" element={<JobListPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/create-job" element={<CreateJobPage />} />
          <Route
            path="*"
            element={
              <Typography variant="h4" align="center" sx={{ mt: 5 }}>
                404 Page Not Found
              </Typography>
            }
          />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;