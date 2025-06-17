import React from 'react';
import { Box } from '@mui/material';

function FlowLinesBackground() {
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -2,
        pointerEvents: 'none',
        overflow: 'hidden',
        background: '#0d0d0d', // Base dark background
      }}
    >
      <svg
        viewBox="0 0 1920 1080"
        preserveAspectRatio="none"
        style={{
          width: '100%',
          height: '100%',
        }}
      >
        <defs>
          <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(128,0,255,0.4)" />
            <stop offset="100%" stopColor="rgba(0,200,255,0.2)" />
          </linearGradient>
        </defs>

        <path
          d="M0,300 C600,100 1320,500 1920,300"
          stroke="url(#gradient1)"
          strokeWidth="2.5"
          fill="none"
          style={{
            strokeDasharray: 4000,
            strokeDashoffset: 0,
            animation: 'flow 15s linear infinite',
          }}
        />

        <path
          d="M0,500 C800,400 1100,700 1920,500"
          stroke="url(#gradient1)"
          strokeWidth="1.8"
          fill="none"
          style={{
            strokeDasharray: 4000,
            strokeDashoffset: 2000,
            animation: 'flow 22s linear infinite',
          }}
        />
      </svg>

      {/* Keyframe animation in global CSS */}
      <style>
        {`
          @keyframes flow {
            0% { stroke-dashoffset: 4000; }
            100% { stroke-dashoffset: 0; }
          }
        `}
      </style>
    </Box>
  );
}

export default FlowLinesBackground;
