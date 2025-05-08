import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchJobDetails } from '../api/apiService';
import ResumeList from '../components/ResumeList'; // Assuming these exist
import ResumeUpload from '../components/ResumeUpload'; // Assuming these exist

// Remove inline styles, use classes
const pageContainerStyle = { padding: '20px' };
const sectionStyle = { marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #555'};
const errorStyle = { color: 'red', border: '1px solid red', padding: '10px', marginTop: '10px' };
const descriptionStyle = { whiteSpace: 'pre-wrap', backgroundColor: '#282c34', padding: '10px', borderRadius: '5px', border: '1px solid #444' }; // Added border

function JobDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshCounter, setRefreshCounter] = useState(0);

  const loadJobDetails = useCallback(async () => {
      // ... (keep existing fetch logic) ...
       if (!jobId) return; try { setLoading(true); setError(null); const response = await fetchJobDetails(jobId); setJob(response.data); } catch (err) { console.error(`Error fetching job details for ID ${jobId}:`, err); if (err.response && err.response.status === 404) setError(`Job with ID ${jobId} not found.`); else if (err.request) setError('Failed to fetch job details: No response from server.'); else setError(`Failed to fetch job details: ${err.message}`); setJob(null); } finally { setLoading(false); }
  }, [jobId]);

  useEffect(() => { loadJobDetails(); }, [loadJobDetails]);

  const handleUploadSuccess = () => { setRefreshCounter(prev => prev + 1); };

  if (loading) { return <div style={pageContainerStyle}>Loading job details...</div>; }
  if (error) { return <div style={pageContainerStyle}><div style={errorStyle}>Error: {error}</div></div>; }
  if (!job) { return <div style={pageContainerStyle}>Job data could not be loaded.</div>; }

  return (
    <div style={pageContainerStyle}>
      {/* --- APPLY glass-card TO JOB DETAILS --- */}
      <div className="glass-card">
        <h2>Job Details: {job.title}</h2>
        <p><strong>ID:</strong> {job.id}</p>
        <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
        <p><strong>Required Years:</strong> {job.required_years ?? 'N/A'}</p>
        <h3>Description:</h3>
        <p style={descriptionStyle}> {/* Keep specific style for pre-wrap */}
          {job.description}
        </p>
      </div>
      {/* -------------------------------------- */}

      <div style={sectionStyle}>
        <h3>Upload Resumes</h3>
         {/* Assume ResumeUpload might have its own card styling or apply glass-card */}
        <ResumeUpload jobId={job.id} onUploadSuccess={handleUploadSuccess} />
      </div>

      <div style={sectionStyle}>
        <h3>Screening Results</h3>
         {/* Assume ResumeList handles its item styling or apply glass-card to container */}
         <ResumeList jobId={job.id} key={refreshCounter} />
      </div>

       <Link to="/">
          {/* --- APPLY glow-button CLASS HERE --- */}
          <button className="glow-button" style={{ marginTop: '20px' }}>Back to Job List</button>
          {/* ------------------------------------ */}
       </Link>
    </div>
  );
}

export default JobDetailPage;