import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom'; // Import hook for navigation
import { createJob } from '../api/apiService'; // Import the API function

// Basic placeholder styling
const pageContainerStyle = { padding: '20px' };
const formGroupStyle = { marginBottom: '15px' };
const labelStyle = { display: 'block', marginBottom: '5px', fontWeight: 'bold' };
const inputStyle = { width: '90%', maxWidth: '600px', padding: '8px', marginBottom: '5px', border: '1px solid #555', borderRadius: '4px', backgroundColor: '#333', color: 'white' };
const textareaStyle = { ...inputStyle, height: '150px', resize: 'vertical' }; // Allow vertical resize
const buttonStyle = { padding: '10px 20px', cursor: 'pointer', backgroundColor: '#61dafb', border: 'none', borderRadius: '4px', color: '#282c34', fontWeight: 'bold' };
const buttonDisabledStyle = { ...buttonStyle, backgroundColor: '#555', cursor: 'not-allowed' };
const messageStyle = { marginTop: '15px', padding: '10px', borderRadius: '4px' };
const errorStyle = { ...messageStyle, color: 'red', border: '1px solid red', backgroundColor: '#442222' };
const successStyle = { ...messageStyle, color: 'lightgreen', border: '1px solid lightgreen', backgroundColor: '#224422' };


function CreateJobPage() {
  // --- State Variables ---
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  // Store years as string to handle empty input, convert to number on submit
  const [requiredYears, setRequiredYears] = useState('');
  const [isLoading, setIsLoading] = useState(false); // For loading indicator on button
  const [error, setError] = useState(null); // To display API errors
  const [successMessage, setSuccessMessage] = useState(''); // To display success message

  // Hook to programmatically navigate
  const navigate = useNavigate();

  // --- Event Handlers ---
  const handleTitleChange = (event) => {
    setTitle(event.target.value);
  };

  const handleDescriptionChange = (event) => {
    setDescription(event.target.value);
  };

  const handleYearsChange = (event) => {
    setRequiredYears(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevent default browser form submission
    setIsLoading(true); // Show loading state
    setError(null); // Clear previous errors
    setSuccessMessage(''); // Clear previous success message

    // Basic validation
    if (!title.trim() || !description.trim()) {
      setError('Job Title and Description cannot be empty.');
      setIsLoading(false);
      return;
    }

    // Prepare data for API - convert years to integer or null
    const jobData = {
      title: title.trim(),
      description: description.trim(),
      // Convert string to integer, handle empty string as null (optional field)
      required_years: requiredYears ? parseInt(requiredYears, 10) : null,
    };

    // Input validation for years (ensure it's a non-negative integer if provided)
    if (requiredYears && (isNaN(jobData.required_years) || jobData.required_years < 0)) {
         setError('Required Years must be a valid non-negative number.');
         setIsLoading(false);
         return;
    }


    try {
      // Call the API service function
      const response = await createJob(jobData);

      // Handle success
      setSuccessMessage(`Job "${response.data.title}" created successfully! ID: ${response.data.id}`);
      console.info(`Job created successfully: ${response.data.id}`)
      // Clear the form
      setTitle('');
      setDescription('');
      setRequiredYears('');

      // Optionally navigate away after a short delay
      setTimeout(() => {
        navigate('/'); // Navigate back to the job list page
        // Or navigate(`/jobs/${response.data.id}`); // Navigate to the new job's detail page
      }, 2000); // Wait 2 seconds

    } catch (err) {
      // Handle errors from the API call
      console.error("Error creating job:", err);
      if (err.response && err.response.data && err.response.data.error) {
         // Use error message from backend if available
         setError(`Failed to create job: ${err.response.data.error}` + (err.response.data.messages ? ` - ${JSON.stringify(err.response.data.messages)}` : ''));
      } else if (err.request) {
          setError('Failed to create job: No response from server. Is the backend running?');
      } else {
          setError(`Failed to create job: ${err.message}`);
      }
    } finally {
      // Stop loading indicator regardless of success/error
      setIsLoading(false);
    }
  };

  // --- Render Logic ---
  return (
    <div style={pageContainerStyle}>
      <h2>Create New Job Posting</h2>

      <form onSubmit={handleSubmit}>
        <div style={formGroupStyle}>
          <label htmlFor="title" style={labelStyle}>Job Title:</label>
          <input
            type="text"
            id="title"
            name="title"
            value={title}
            onChange={handleTitleChange}
            style={inputStyle}
            required // HTML5 required validation
            disabled={isLoading}
          />
        </div>

        <div style={formGroupStyle}>
          <label htmlFor="description" style={labelStyle}>Job Description:</label>
          <textarea
            id="description"
            name="description"
            value={description}
            onChange={handleDescriptionChange}
            rows="10"
            style={textareaStyle}
            required // HTML5 required validation
            disabled={isLoading}
          />
        </div>

        <div style={formGroupStyle}>
          <label htmlFor="required_years" style={labelStyle}>Required Years of Experience (Optional):</label>
          <input
            type="number"
            id="required_years"
            name="required_years"
            value={requiredYears}
            onChange={handleYearsChange}
            min="0" // HTML5 validation
            step="1" // Allow only whole numbers
            style={{ ...inputStyle, width: '150px' }} // Make year input smaller
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          style={isLoading ? buttonDisabledStyle : buttonStyle}
          disabled={isLoading} // Disable button while loading
        >
          {isLoading ? 'Creating...' : 'Create Job'}
        </button>
      </form>

      {/* Display Success or Error Messages */}
      {successMessage && <div style={successStyle}>{successMessage}</div>}
      {error && <div style={errorStyle}>Error: {error}</div>}

    </div>
  );
}

export default CreateJobPage;