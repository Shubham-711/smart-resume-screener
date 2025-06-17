// src/components/AnimatedBackground.jsx
import React from 'react';
import { Box } from '@mui/material';

function AnimatedBackground() {
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -1,
        overflow: 'hidden',
        background: 'radial-gradient(ellipse at center, #1a1a1a 0%, #0d0d0d 100%)',
        '::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\"100%\" height=\"100%\" viewBox=\"0 0 1440 800\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cg fill=\"%23ffffff11\"%3E%3Ccircle cx=\"100\" cy=\"200\" r=\"1.5\" /%3E%3Ccircle cx=\"400\" cy=\"600\" r=\"1.2\" /%3E%3Ccircle cx=\"900\" cy=\"300\" r=\"2\" /%3E%3Ccircle cx=\"1300\" cy=\"500\" r=\"1.7\" /%3E%3C/g%3E%3C/svg%3E")',
          animation: 'floatDots 60s linear infinite',
        },
        '@keyframes floatDots': {
          '0%': { transform: 'translateY(0)' },
          '100%': { transform: 'translateY(-100px)' },
        }
      }}
    />
  );
}

export default AnimatedBackground;
