import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function ScanCore({ color, active }: { color: string; active: boolean }) {
  const coreRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const sweepRef = useRef<THREE.Mesh>(null);
  const reducedMotion = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, []);

  useFrame((state, delta) => {
    if (reducedMotion) return;
    if (coreRef.current) {
      coreRef.current.rotation.y += delta * (active ? 1.1 : 0.18);
      coreRef.current.rotation.x += delta * (active ? 0.35 : 0.06);
    }
    if (ringRef.current) {
      const pulse = active ? 1 + Math.sin(state.clock.elapsedTime * 5) * 0.09 : 1;
      ringRef.current.scale.setScalar(pulse);
      ringRef.current.rotation.z += delta * (active ? 0.8 : 0.12);
    }
    if (sweepRef.current) sweepRef.current.rotation.z = state.clock.elapsedTime * (active ? 2.4 : 0.35);
  });

  return (
    <group>
      <mesh ref={coreRef}>
        <icosahedronGeometry args={[1.05, 2]} />
        <meshBasicMaterial color={color} wireframe transparent opacity={active ? 0.72 : 0.48} />
      </mesh>
      <mesh scale={1.01}>
        <sphereGeometry args={[1.02, 20, 20]} />
        <meshBasicMaterial color={color} transparent opacity={active ? 0.045 : 0.02} />
      </mesh>
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.32, 0.018, 5, 72]} />
        <meshBasicMaterial color={color} transparent opacity={active ? 0.7 : 0.35} />
      </mesh>
      <mesh ref={sweepRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.46, 0.01, 4, 72, Math.PI * 0.32]} />
        <meshBasicMaterial color={color} transparent opacity={active ? 0.9 : 0.35} />
      </mesh>
    </group>
  );
}

export function ScanningGlobe({ color, active }: { color: string; active: boolean }) {
  return (
    <div className="h-28 w-28 shrink-0">
      <Canvas camera={{ position: [0, 0, 3.5], fov: 44 }} gl={{ alpha: true, antialias: true }}>
        <ScanCore color={color} active={active} />
      </Canvas>
    </div>
  );
}
