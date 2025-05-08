import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createJob } from '../api/apiService';

// Remove inline styles, use classes from index.css/App.css
const pageContainerStyle = { padding: '20px' };
const formGroupStyle = { marginBottom: '15px' };
const labelStyle = { display: 'block', marginBottom: '5px', fontWeight: 'bold' };
// Add input/textarea base styles if needed, or rely on browser defaults + overrides
const inputBaseStyle = { width: '90%', maxWidth: '600px', padding: '8px', marginBottom: '5px', border: '1px solid #555', borderRadius: '4px', backgroundColor: '#333', color: 'white' };
const textareaStyle = { ...inputBaseStyle, height: '150px', resize: 'vertical' };
const messageStyle = { marginTop: '15px', padding: '10px', borderRadius: '4px' };
const errorStyle = { ...messageStyle, color: 'red', border: '1px solid red', backgroundColor: '#442222' };
const successStyle = { ...messageStyle, color: 'lightgreen', border: '1px solid lightgreen', backgroundColor: '#224422' };

function CreateJobPage() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requiredYears, setRequiredYears] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault(); setIsLoading(true); setError(null); setSuccessMessage('');
    if (!title.trim() || !description.trim()) { setError('Job Title and Description cannot be empty.'); setIsLoading(false); return; }
    const jobData = { title: title.trim(), description: description.trim(), required_years: requiredYears ? parseInt(requiredYears, 10) : null, };
    if (requiredYears && (isNaN(jobData.required_years) || jobData.required_years < 0)) { setError('Required Years must be a valid non-negative number.'); setIsLoading(false); return; }

    try {
      const response = await createJob(jobData);
      setSuccessMessage(`Job "${response.data.title}" created successfully! ID: ${response.data.id}`);
      console.log(`Job created successfully: ${response.data.id}`);
      setTitle(''); setDescription(''); setRequiredYears('');
      setTimeout(() => { navigate('/'); }, 2000);
    } catch (err) {
      console.error("Error creating job:", err);
      // ... (keep error handling) ...
      if (err.response && err.response.data && err.response.data.error) { setError(`Failed to create job: ${err.response.data.error}` + (err.response.data.messages ? ` - ${JSON.stringify(err.response.data.messages)}` : '')); }
      else if (err.request) { setError('Failed to create job: No response from server.'); }
      else { setError(`Failed to create job: ${err.message}`); }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={pageContainerStyle}>
      <h2>Create New Job Posting</h2>
      <form onSubmit={handleSubmit}>
        <div style={formGroupStyle}>
          <label htmlFor="title" style={labelStyle}>Job Title:</label>
          <input type="text" id="title" value={title} onChange={(e) => setTitle(e.target.value)} style={inputBaseStyle} required disabled={isLoading} />
        </div>
        <div style={formGroupStyle}>
          <label htmlFor="description" style={labelStyle}>Job Description:</label>
          <textarea id="description" value={description} onChange={(e) => setDescription(e.target.value)} rows="10" style={textareaStyle} required disabled={isLoading} />
        </div>
        <div style={formGroupStyle}>
          <label htmlFor="required_years" style={labelStyle}>Required Years of Experience (Optional):</label>
          <input type="number" id="required_years" value={requiredYears} onChange={(e) => setRequiredYears(e.target.value)} min="0" step="1" style={{ ...inputBaseStyle, width: '150px' }} disabled={isLoading} />
        </div>
        {/* --- APPLY glow-button CLASS HERE --- */}
        <button type="submit" className="glow-button" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Create Job'}
        </button>
        {/* ------------------------------------ */}
      </form>
      {successMessage && <div style={successStyle}>{successMessage}</div>}
      {error && <div style={errorStyle}>Error: {error}</div>}
    </div>
  );
}

export default CreateJobPage;