import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, NavLink } from 'react-router-dom';
import { AppBar, Toolbar, Button, Box, Typography, Container } from '@mui/material';
import { AnimatePresence } from 'framer-motion';

import HomePage from './pages/HomePage';
import JobListPage from './pages/JobListPage';
import JobDetailPage from './pages/JobDetailPage';
import CreateJobPage from './pages/CreateJobPage';




import PageWrapper from './components/PageWrapper';


function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageWrapper keyId="home"><HomePage /></PageWrapper>} />
        <Route path="/jobs" element={<PageWrapper keyId="jobs"><JobListPage /></PageWrapper>} />
        <Route path="/jobs/:jobId" element={<PageWrapper keyId="detail"><JobDetailPage /></PageWrapper>} />
        <Route path="/create-job" element={<PageWrapper keyId="create"><CreateJobPage /></PageWrapper>} />
        <Route path="*" element={<Typography variant="h4" align="center">404 Page Not Found</Typography>} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <Router>
    
       
      <AppBar position="fixed" sx={{ background: 'rgba(20,20,20,0.8)', backdropFilter: 'blur(10px)' }}>
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography
            variant="h6"
            component={NavLink}
            to="/"
            sx={{
              fontWeight: 700,
              fontFamily: 'monospace',
              letterSpacing: '.1rem',
              color: 'white',
              textDecoration: 'none',
            }}
          >
            Resume Screener
          </Typography>

          <Box>
            <Button component={NavLink} to="/jobs" sx={{ color: 'white', mx: 1 }}>Job List</Button>
            <Button component={NavLink} to="/create-job" sx={{ color: 'white', mx: 1 }}>Create Job</Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Toolbar /> {/* Spacer for AppBar */}
      <Container maxWidth="lg" sx={{ pt: 4 }}>
        <AnimatedRoutes />
      </Container>
    </Router>
  );
}

export default App;
