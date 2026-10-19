import axios from 'axios';

// Vite proxy forwards /api to backend http://127.0.0.1:5000 in dev mode
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30s timeout for AI generation
});

// Helper for standardized error messages
export const getErrorMessage = (error, defaultMsg = 'Something went wrong. Please try again.') => {
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  if (error.message === 'Network Error') {
    return 'Unable to connect to the backend server. Please verify backend is running on port 5000.';
  }
  return error.message || defaultMsg;
};

export default apiClient;
