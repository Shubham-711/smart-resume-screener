import React from 'react';
// Use NavLink for automatic active class styling
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import JobListPage from './pages/JobListPage';
import JobDetailPage from './pages/JobDetailPage';
import CreateJobPage from './pages/CreateJobPage';

// Import the CSS - make sure the path is correct
import './index.css'; // Or './App.css'

function App() {
  return (
    <Router>
      {/* Use semantic nav element and specific class */}
      <nav className="app-nav">
        {/* Use NavLink for automatic 'active' class */}
        <NavLink
          to="/"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          Job List
        </NavLink>
        <NavLink
          to="/create-job"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          Create Job
        </NavLink>
      </nav>

      {/* Add a main content container for centering and padding */}
      <main className="page-container">
        <Routes>
          <Route path="/" element={<JobListPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/create-job" element={<CreateJobPage />} />
          {/* <Route path="*" element={<div>404 Page Not Found</div>} /> */}
        </Routes>
      </main>

    </Router>
  );
}

export default App;