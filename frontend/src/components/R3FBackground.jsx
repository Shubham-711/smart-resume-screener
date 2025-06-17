// src/components/R3FBackground.jsx
import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';

// Helper function to generate points in a curve
function generateCurvePoints(amplitude = 1, frequency = 1, count = 100) {
  const points = [];
  for (let i = 0; i < count; i++) {
    const x = (i / count) * 10 - 5;
    const y = Math.sin(i * 0.3 * frequency) * amplitude;
    const z = Math.cos(i * 0.3 * frequency) * amplitude;
    points.push([x, y, z]);
  }
  return points;
}

function AnimatedLines() {
  const groupRef = useRef();

  // Rotate the group continuously
  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      {[...Array(6)].map((_, i) => (
        <Line
          key={i}
          points={generateCurvePoints(1, i + 1)}
          color={`hsl(${i * 60}, 100%, 70%)`}
          lineWidth={0.8}
          dashed={false}
        />
      ))}
    </group>
  );
}

export default function R3FBackground() {
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: -1 }}>
      <Canvas camera={{ position: [0, 0, 10], fov: 75 }}>
        <ambientLight intensity={0.5} />
        <AnimatedLines />
      </Canvas>
    </div>
  );
}
