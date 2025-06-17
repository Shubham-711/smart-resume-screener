// frontend/src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx'; // Your main App component
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
// import './index.css'; // Optional: only if you have truly global overrides not handled by MUI

// Define the dark theme for the entire application
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#7f5af0', // Main purple for buttons, active links
      light: '#9d81f5', // Lighter purple for hover states
      contrastText: '#ffffff', // Text on primary colored elements
    },
    secondary: {
      main: '#72ccaF', // Teal/green for secondary actions
      light: '#83d9c3',
      contrastText: '#000000', // Text on secondary colored elements
    },
    background: {
      default: '#16181d', // Main page background
      paper: '#1f232c',   // Background for cards, AppBar, Paper components
    },
    text: {
      primary: '#f0f2f5',    // Main text color (light gray/off-white)
      secondary: '#adb5bd', // Secondary text color (softer gray)
    },
    divider: 'rgba(255, 255, 255, 0.12)',
    action: {
        hover: 'rgba(255, 255, 255, 0.08)',
        selected: 'rgba(255, 255, 255, 0.16)',
        disabledBackground: 'rgba(255, 255, 255, 0.12)',
        disabled: 'rgba(255, 255, 255, 0.3)',
        focus: 'rgba(255, 255, 255, 0.12)',
    }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif', // Clean sans-serif
    h1: { fontWeight: 700, letterSpacing: '-0.025em', fontSize: '2.8rem' },
    h2: { fontWeight: 700, letterSpacing: '-0.02em', fontSize: '2.2rem' },
    h3: { fontWeight: 600, letterSpacing: '-0.015em', fontSize: '1.8rem' },
    h4: { fontWeight: 600, fontSize: '1.5rem' }, // For page titles like "Create New Job Posting"
    h5: { fontWeight: 500, fontSize: '1.25rem' }, // For section titles
    h6: { fontWeight: 500, fontSize: '1.1rem' },  // For card titles
    button: {
      textTransform: 'none', // Keep button text case as typed
      fontWeight: 600,
    }
  },
  shape: {
    borderRadius: 10, // Consistent rounded corners (less "pill-shaped")
  },
  components: {
    MuiPaper: { // Default styling for Paper (which Card uses)
      styleOverrides: {
        root: ({ theme }) => ({ // Can access theme here
          backgroundColor: theme.palette.background.paper,
        }),
      },
      defaultProps: {
        elevation: 2, // Subtle elevation for cards by default
      }
    },
    MuiButton: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: theme.shape.borderRadius * 0.8, // Slightly less than cards
                paddingTop: theme.spacing(1),
                paddingBottom: theme.spacing(1),
            }),
            containedPrimary : { // Specific style for variant="contained" color="primary"
                 // Example: add more glow if needed, but glowButtonSx is better for that
            }
        }
    },
    MuiAppBar: {
        styleOverrides: {
            root: ({ theme }) => ({
                backgroundColor: alpha(theme.palette.background.paper, 0.85), // Use alpha from MUI
                backdropFilter: 'blur(8px)',
                WebkitBackdropFilter: 'blur(8px)',
                boxShadow: theme.shadows[1], // Subtle shadow
                borderBottom: `1px solid ${theme.palette.divider}`,
            }),
        },
        defaultProps: {
            elevation: 0, // Let border/backdrop define depth
        }
    },
    MuiTextField: { // Global styles for TextFields
        defaultProps: {
            variant: 'filled', // Filled variant often looks good on dark themes
            InputLabelProps: {
                shrink: true, // Always shrink label
            }
        },
        styleOverrides: {
            root: ({theme}) => ({
                '& .MuiFilledInput-root': {
                    backgroundColor: alpha(theme.palette.common.white, 0.09), // Lighter input bg
                    '&:hover': {
                        backgroundColor: alpha(theme.palette.common.white, 0.13),
                    },
                    '&.Mui-focused': {
                        backgroundColor: alpha(theme.palette.common.white, 0.13),
                    },
                },
            }),
        }
    }
  }
});

// Import alpha for use in theme
import { alpha } from '@mui/material/styles';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);