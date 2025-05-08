import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchJobs } from '../api/apiService'; // Import API function

// Basic placeholder styling
const listStyle = { listStyleType: 'none', padding: 0 };
const listItemStyle = { border: '1px solid #ccc', margin: '0.5rem 0', padding: '0.5rem' };

function JobListPage() {
  const [jobs, setJobs] = useState([]); // State to hold the list of jobs
  const [loading, setLoading] = useState(true); // State for loading indicator
  const [error, setError] = useState(null); // State for error messages

  // useEffect hook to fetch data when the component mounts
  useEffect(() => {
    const loadJobs = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchJobs(); // Call the API service function
        setJobs(response.data); // Update state with data from API response
      } catch (err) {
        console.error("Error fetching jobs:", err);
        setError(err.message || 'Failed to fetch jobs. Is the backend running?');
      } finally {
        setLoading(false); // Set loading to false regardless of success/error
      }
    };

    loadJobs(); // Call the function to load data
  }, []); // Empty dependency array means this runs only once when component mounts

  // --- Render Logic ---
  if (loading) {
    return <div>Loading jobs...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }

  return (
    <div>
      <h2>Job Postings</h2>
      {jobs.length === 0 ? (
        <p>No jobs found. <Link to="/create-job">Create one?</Link></p>
      ) : (
        <ul style={listStyle}>
          {jobs.map((job) => (
            <li key={job.id} style={listItemStyle}>
              {/* Link to the detail page for each job */}
              <Link to={`/jobs/${job.id}`}>
                <h3>{job.title || 'Untitled Job'}</h3>
              </Link>
              <p>Created: {new Date(job.created_at).toLocaleDateString()}</p>
              {/* Display other job info if needed */}
            </li>
          ))}
        </ul>
      )}
       <Link to="/create-job">
          <button>Create New Job</button>
       </Link>
    </div>
  );
}

export default JobListPage;