import axios from 'axios';

// Get the base URL from the environment variable set in .env
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'; // Fallback

console.log('FROM apiService.js -> VITE_API_BASE_URL:', API_BASE_URL);
// Create an Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // Add other headers like Authorization if needed later
  },
  // withCredentials: true, // Uncomment if using cookies/sessions for auth later
});

// --- Job API Calls ---
export const fetchJobs = () => {
  return apiClient.get('/api/jobs');
};

export const fetchJobDetails = (jobId) => {
  return apiClient.get(`/api/jobs/${jobId}`);
};

export const createJob = (jobData) => {
  // jobData should be { title: "...", description: "...", required_years: ... }
  return apiClient.post('/api/jobs', jobData);
};

// --- Resume API Calls ---
export const fetchResumesForJob = (jobId) => {
  return apiClient.get(`/api/jobs/${jobId}/resumes`);
};

export const uploadResumes = (jobId, files) => {
  const formData = new FormData();
  // Important: Append each file with the key 'files[]'
  files.forEach((file) => {
    formData.append('files[]', file);
  });

  return apiClient.post(`/api/jobs/${jobId}/resumes`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data', // Override for file uploads
    },
    // Optional: Add upload progress handler here if needed
    // onUploadProgress: progressEvent => { ... }
  });
};

// Add other API calls (get resume status, download, update job etc.) as needed

export default apiClient; // Export default instance if preferred