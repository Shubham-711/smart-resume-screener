// frontend/src/main.jsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import './index.css'; // Import your base CSS if you kept any body styles

// Define the dark theme
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      // main: '#90caf9', // Light Blue
      main: '#7f5af0', // Purple from glow button example
    },
    secondary: {
      // main: '#f48fb1', // Pink
      main: '#72cca F', // Tealish color
    },
    background: {
      default: '#16181d', // Dark background
      paper: '#1f232c',   // Slightly lighter background for paper/cards
    },
    text: {
      primary: '#e1e1e1',
      secondary: '#a0a0c0',
    },
  },
  // Optional: Customize components globally
  // components: { ... }
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline /> {/* Apply base styling and dark mode background */}
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);