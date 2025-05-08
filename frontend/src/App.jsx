import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import JobListPage from './pages/JobListPage'; // Create this page next
import JobDetailPage from './pages/JobDetailPage'; // Create this page next
import CreateJobPage from './pages/CreateJobPage'; // Create this page next
// Optional: Import a layout component if you have one
// import MainLayout from './layouts/MainLayout';

// Basic styling (replace with proper CSS/UI library later)
const navStyle = {
  backgroundColor: '#333',
  padding: '1rem',
  marginBottom: '1rem',
};

const linkStyle = {
  color: 'white',
  margin: '0 1rem',
  textDecoration: 'none',
};

function App() {
  return (
    <Router>
      <div>
        {/* Simple Navigation */}
        <nav style={navStyle}>
          <Link to="/" style={linkStyle}>Job List</Link>
          <Link to="/create-job" style={linkStyle}>Create Job</Link>
          {/* Add other links as needed */}
        </nav>

        {/* Route Definitions */}
        {/* Optional: Wrap Routes in a Layout component */}
        {/* <MainLayout> */}
        <Routes>
          <Route path="/" element={<JobListPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/create-job" element={<CreateJobPage />} />
          {/* Add other routes */}
          {/* Example for a 404 page */}
          {/* <Route path="*" element={<NotFoundPage />} /> */}
        </Routes>
        {/* </MainLayout> */}

      </div>
    </Router>
  );
}

export default App;