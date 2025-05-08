// frontend/src/pages/JobDetailPage.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchJobDetails } from '../api/apiService';

// Import the new components
import ResumeList from '../components/ResumeList';
import ResumeUpload from '../components/ResumeUpload';

const pageContainerStyle = { padding: '20px' };
const sectionStyle = { marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #555'};
const errorStyle = { color: 'red', border: '1px solid red', padding: '10px', marginTop: '10px' };
const buttonStyle = { padding: '10px 15px', marginTop: '15px', cursor: 'pointer', backgroundColor: '#61dafb', border: 'none', borderRadius: '4px', color: '#282c34', fontWeight: 'bold' };


function JobDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // State to trigger refresh of ResumeList after upload
  const [refreshCounter, setRefreshCounter] = useState(0);

  const loadJobDetails = useCallback(async () => {
    if (!jobId) return;
    try {
      setLoading(true); setError(null);
      const response = await fetchJobDetails(jobId);
      setJob(response.data);
    } catch (err) {
      console.error(`Error fetching job details for ID ${jobId}:`, err);
      if (err.response && err.response.status === 404) setError(`Job with ID ${jobId} not found.`);
      else if (err.request) setError('Failed to fetch job details: No response from server.');
      else setError(`Failed to fetch job details: ${err.message}`);
      setJob(null);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadJobDetails();
  }, [loadJobDetails]); // Fetch job details on mount/jobId change

  // Callback function for ResumeUpload component
  const handleUploadSuccess = () => {
    console.log('Upload successful, triggering resume list refresh...');
    // Increment the counter to change the key prop on ResumeList, forcing a re-render/re-fetch
    setRefreshCounter(prev => prev + 1);
  };

  // --- Render Logic ---
  if (loading) {
    return <div style={pageContainerStyle}>Loading job details...</div>;
  }

  if (error) {
    return <div style={pageContainerStyle}><div style={errorStyle}>Error: {error}</div></div>;
  }

  if (!job) {
    return <div style={pageContainerStyle}>Job data could not be loaded.</div>;
  }

  return (
    <div style={pageContainerStyle}>
      <h2>Job Details: {job.title}</h2>
      <p><strong>ID:</strong> {job.id}</p>
      <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
      <p><strong>Required Years:</strong> {job.required_years ?? 'N/A'}</p>
      <h3>Description:</h3>
      <p style={{ whiteSpace: 'pre-wrap', backgroundColor: '#282c34', padding: '10px', borderRadius: '5px' }}>
        {job.description}
      </p>

      <div style={sectionStyle}>
        <h3>Upload Resumes</h3>
        {/* Render ResumeUpload, passing jobId and the callback */}
        <ResumeUpload jobId={job.id} onUploadSuccess={handleUploadSuccess} />
      </div>

      <div style={sectionStyle}>
        <h3>Screening Results</h3>
         {/* Render ResumeList, passing jobId and the key */}
         {/* Changing the key forces React to recreate the component, triggering its useEffect */}
         <ResumeList jobId={job.id} key={refreshCounter} />
      </div>

       <Link to="/">
          <button style={buttonStyle}>Back to Job List</button>
       </Link>
    </div>
  );
}

export default JobDetailPage;