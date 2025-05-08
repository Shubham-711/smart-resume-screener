import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchJobs } from '../api/apiService';

function JobListPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { /* ... keep existing useEffect logic ... */
    const loadJobs = async () => { try { setLoading(true); setError(null); const response = await fetchJobs(); setJobs(response.data || []); } catch (err) { console.error("Error fetching jobs:", err); if (err.response) { setError(`Failed to fetch jobs: ${err.response.status} ${err.response.statusText}`); } else if (err.request) { setError('Failed to fetch jobs: No response from server. Is the backend running?');} else { setError(`Failed to fetch jobs: ${err.message}`); } } finally { setLoading(false); } }; loadJobs();
  }, []);

  if (loading) return <div>Loading jobs...</div>; // Centered by page-container

  return (
    // Container already provided by App.jsx's <main>
    <>
      <h2>Job Postings</h2>
      {error && <div className="message message-error">Error: {error}</div>}

      {jobs.length === 0 && !error ? (
        <p>No jobs found. <Link to="/create-job">Create one?</Link></p>
      ) : (
        // Remove ul styling, rely on card margin
        <div>
          {jobs.map((job) => (
            <div key={job.id} className="glass-card"> {/* Use div with class */}
              <Link to={`/jobs/${job.id}`}>
                <h3>{job.title || 'Untitled Job'}</h3>
              </Link>
              <p>Created: {new Date(job.created_at).toLocaleDateString()} | Required Years: {job.required_years ?? 'N/A'}</p>
              <p>{job.description ? `${job.description.substring(0, 150)}...` : 'No description.'}</p> {/* Increased snippet length */}
            </div>
          ))}
        </div>
      )}
       <Link to="/create-job" style={{display: 'inline-block', marginTop: '1rem'}}>
          <button className="glow-button">Create New Job</button>
       </Link>
    </>
  );
}

export default JobListPage;