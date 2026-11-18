import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useTheme } from '@/context/ThemeContext';

function WireGlobe({ color }: { color: string }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const reducedMotion = useMemo(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  );

  useFrame((_, delta) => {
    if (!meshRef.current || reducedMotion) return;
    meshRef.current.rotation.y += delta * 0.05;
    meshRef.current.rotation.x += delta * 0.012;
  });

  return (
    <mesh ref={meshRef} position={[2.4, 0.6, -2]}>
      <icosahedronGeometry args={[2.1, 2]} />
      <meshBasicMaterial color={color} wireframe transparent opacity={0.16} />
    </mesh>
  );
}

function ParticleField({ color, count = 260 }: { color: string; count?: number }) {
  const pointsRef = useRef<THREE.Points>(null);
  const reducedMotion = useMemo(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  );

  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 16;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 10;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 10 - 2;
    }
    return arr;
  }, [count]);

  useFrame((_, delta) => {
    if (!pointsRef.current || reducedMotion) return;
    pointsRef.current.rotation.y += delta * 0.008;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color={color} size={0.028} transparent opacity={0.5} sizeAttenuation />
    </points>
  );
}

export function AmbientBackground({ accent }: { accent: string }) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <div
      className="pointer-events-none fixed inset-0 -z-10"
      style={{ opacity: isDark ? 1 : 0.55 }}
      aria-hidden="true"
    >
      <Canvas
        camera={{ position: [0, 0, 6], fov: 50 }}
        gl={{ alpha: true, antialias: true }}
        dpr={[1, 1.5]}
      >
        <WireGlobe color={accent} />
        <ParticleField color={accent} />
      </Canvas>
    </div>
  );
}
