// frontend/src/components/ResumeList.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { fetchResumesForJob } from '../api/apiService'; // Adjust path if needed

// Basic Styling (Replace with UI library later)
const listContainerStyle = { marginTop: '15px' };
const resumeItemStyle = {
  border: '1px solid #444',
  borderRadius: '4px',
  padding: '10px 15px',
  marginBottom: '10px',
  backgroundColor: '#3a3f47',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center'
};
const statusStyle = (status) => ({
  fontWeight: 'bold',
  padding: '3px 8px',
  borderRadius: '10px',
  fontSize: '0.85em',
  color: 'white',
  backgroundColor:
    status === 'COMPLETED' ? 'green' :
    status === 'PROCESSING' ? 'orange' :
    status === 'PENDING' ? 'gray' :
    status === 'FAILED' ? 'red' :
    'black',
});
const scoreStyle = { fontWeight: 'bold', color: '#a0d8ef' };
const filenameStyle = { marginRight: '15px', wordBreak: 'break-all' }; // Allow long names to wrap
const buttonStyle = { marginLeft: '10px', padding: '5px 10px', cursor: 'pointer' };
const refreshButtonStyle = { marginBottom: '15px', padding: '8px 12px', cursor: 'pointer' };
const errorStyle = { color: 'red', marginTop: '10px'};

// Helper to format score
const formatScore = (score) => {
  if (score === null || score === undefined) {
    return '--';
  }
  // Multiply by 100 and show 1 decimal place for percentage feel
  return `${(score * 100).toFixed(1)}%`;
};


function ResumeList({ jobId }) { // Accept jobId as a prop
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false); // State to track polling

  // useCallback to memoize the fetch function - prevents redefining on every render
  const loadResumes = useCallback(async () => {
    if (!jobId) return; // Don't fetch if jobId isn't valid
    setLoading(true);
    setError(null);
    try {
      const response = await fetchResumesForJob(jobId);
      setResumes(response.data || []);

      // Check if any resumes are still processing to decide if polling should continue
      const stillProcessing = response.data?.some(r => r.status === 'PENDING' || r.status === 'PROCESSING');
      setIsPolling(stillProcessing); // Update polling status

    } catch (err) {
      console.error(`Error fetching resumes for job ${jobId}:`, err);
      setError(err.message || 'Failed to fetch resumes.');
      setIsPolling(false); // Stop polling on error
    } finally {
      setLoading(false);
    }
  }, [jobId]); // Dependency: re-create function only if jobId changes

  // Initial fetch and polling setup
  useEffect(() => {
    loadResumes(); // Fetch initially when component mounts or jobId changes

    // Set up polling if needed
    let intervalId = null;
    if (isPolling) {
      intervalId = setInterval(() => {
        console.log(`Polling resumes for Job ID: ${jobId}...`);
        loadResumes(); // Fetch again periodically
      }, 5000); // Poll every 5 seconds
    }

    // Cleanup function: clear interval when component unmounts or polling stops
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [jobId, loadResumes, isPolling]); // Dependencies for the effect


  // --- Render Logic ---
  return (
    <div style={listContainerStyle}>

      <button
           onClick={loadResumes} // <<< ADD THIS onClick HANDLER
           disabled={loading}
            style={refreshButtonStyle}
            >
               {loading ? 'Refreshing...' : 'Refresh List'}
      </button>
      {error && <p style={errorStyle}>Error loading resumes: {error}</p>}

      {!loading && resumes.length === 0 && !error && <p>No resumes uploaded for this job yet.</p>}

      {resumes.map((resume) => (
        <div key={resume.id} style={resumeItemStyle}>
          <div>
            <span style={filenameStyle}>{resume.filename}</span><br />
            <span style={{fontSize: '0.8em', color: '#aaa'}}>Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}</span>
          </div>
          <div>
            <span style={scoreStyle}>Score: {resume.status === 'COMPLETED' ? formatScore(resume.score) : '--'}</span>
            <span style={{ marginLeft: '15px', ...statusStyle(resume.status) }}>
              {resume.status}
            </span>
             {/* Basic download link - opens in new tab */}
            <a
              href={`${import.meta.env.VITE_API_BASE_URL}/api/resumes/${resume.id}/download`}
              target="_blank" // Open in new tab
              rel="noopener noreferrer" // Security best practice
            >
               <button style={buttonStyle} title="Download Original">Download</button>
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}

export default ResumeList;