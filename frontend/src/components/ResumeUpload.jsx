// frontend/src/components/ResumeUpload.jsx

import React, { useState, useRef } from 'react';
import { uploadResumes } from '../api/apiService'; // Adjust path if needed

// Basic Styling
const uploadContainerStyle = { border: '2px dashed #555', padding: '20px', textAlign: 'center', marginBottom: '20px', backgroundColor: '#3a3f47' };
const buttonStyle = { padding: '10px 15px', marginLeft: '10px', cursor: 'pointer' };
const buttonDisabledStyle = { ...buttonStyle, backgroundColor: '#555', cursor: 'not-allowed' };
const messageStyle = { marginTop: '15px', padding: '10px', borderRadius: '4px' };
const errorStyle = { ...messageStyle, color: 'red', border: '1px solid red', backgroundColor: '#442222' };
const successStyle = { ...messageStyle, color: 'lightgreen', border: '1px solid lightgreen', backgroundColor: '#224422' };
const fileListStyle = { textAlign: 'left', marginTop: '10px', fontSize: '0.9em', maxHeight: '100px', overflowY: 'auto'};

// Accept jobId and an optional callback function as props
function ResumeUpload({ jobId, onUploadSuccess }) {
  const [selectedFiles, setSelectedFiles] = useState([]); // Use FileList object directly
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const fileInputRef = useRef(null); // Ref to access the file input element

  const handleFileChange = (event) => {
    setSelectedFiles(event.target.files); // Store the FileList object
    // Clear previous messages when new files are selected
    setError(null);
    setSuccessMessage('');
  };

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setError('Please select one or more resume files first.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMessage('');

    // Convert FileList to an array to use forEach
    const filesArray = Array.from(selectedFiles);

    try {
      const response = await uploadResumes(jobId, filesArray); // Pass array of files

      let successMsg = `${response.data.uploaded?.length || 0} file(s) successfully queued.`;
      if (response.data.errors && Object.keys(response.data.errors).length > 0) {
          successMsg += ` ${Object.keys(response.data.errors).length} file(s) had errors.`;
          // Optionally display specific file errors from response.data.errors
          console.warn("Upload errors:", response.data.errors);
      }
      setSuccessMessage(successMsg);

      // Clear the file input and state after successful upload
      if (fileInputRef.current) {
          fileInputRef.current.value = ""; // Reset file input
      }
      setSelectedFiles([]);

      // Call the callback function passed from the parent, if it exists
      if (onUploadSuccess) {
        onUploadSuccess();
      }

    } catch (err) {
      console.error(`Error uploading resumes for job ${jobId}:`, err);
       if (err.response && err.response.data && err.response.data.error) {
         setError(`Upload failed: ${err.response.data.error}` + (err.response.data.details ? ` - ${JSON.stringify(err.response.data.details)}` : ''));
      } else if (err.request) {
          setError('Upload failed: No response from server.');
      } else {
          setError(`Upload failed: ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={uploadContainerStyle}>
      <input
        type="file"
        multiple // Allow multiple file selection
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" // Specify allowed types
        onChange={handleFileChange}
        ref={fileInputRef} // Assign ref to the input
        style={{ display: 'block', margin: '10px auto' }}
        disabled={isLoading}
      />

      {/* Display names of selected files */}
      {selectedFiles.length > 0 && (
        <div style={fileListStyle}>
          <strong>Selected files:</strong>
          <ul>
            {Array.from(selectedFiles).map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={isLoading || selectedFiles.length === 0}
        style={(isLoading || selectedFiles.length === 0) ? buttonDisabledStyle : buttonStyle}
      >
        {isLoading ? 'Uploading...' : `Upload ${selectedFiles.length} File(s)`}
      </button>

      {/* Display Success or Error Messages */}
      {successMessage && <div style={successStyle}>{successMessage}</div>}
      {error && <div style={errorStyle}>Error: {error}</div>}
    </div>
  );
}

export default ResumeUpload;