// frontend/src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
// import './index.css'; // Optional: only if you have truly global overrides not handled by MUI

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#7f5af0', // A good purple for primary actions
      light: '#9d81f5', // Lighter shade for hover/active
    },
    secondary: {
      main: '#72ccaF', // A teal/green for secondary actions
    },
    background: {
      default: '#16181d', // Main dark background for the body
      paper: '#1f232c',   // Background for cards, appbar, paper elements
    },
    text: {
      primary: '#ffffff',    // Main text color (white)
      secondary: '#adb5bd', // Lighter gray for secondary text
    },
    action: { // For button states, hovers
        hover: 'rgba(255, 255, 255, 0.08)',
        disabledBackground: '#4a4a5a',
        disabled: '#888'
    }
  },
  typography: {
    fontFamily: 'Roboto, "Helvetica Neue", Arial, sans-serif', // Example font stack
    h4: {
      fontWeight: 700,
    },
    h5: {
        fontWeight: 600,
    },
    h6: {
        fontWeight: 500,
    }
  },
  components: { // Optional: Global component overrides
    MuiButton: {
        styleOverrides: {
            root: {
                textTransform: 'none', // Prevent buttons from being all caps
            }
        }
    }
  }
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline /> {/* Applies theme background and base styles */}
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);