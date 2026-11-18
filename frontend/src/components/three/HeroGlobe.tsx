import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { PALETTE } from '@/lib/theme-colors';

function LatitudeRing({ y, radius }: { y: number; radius: number }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.08;
  });
  return (
    <mesh ref={ref} position={[0, y, 0]} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[radius, 0.006, 6, 96]} />
      <meshBasicMaterial color={PALETTE.orbit} transparent opacity={0.22} />
    </mesh>
  );
}

function Globe() {
  const groupRef = useRef<THREE.Group>(null);
  const reducedMotion = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, []);

  useFrame((state, delta) => {
    if (!groupRef.current || reducedMotion) return;
    groupRef.current.rotation.y += delta * 0.13;
    groupRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.18) * 0.025;
  });

  return (
    <group ref={groupRef}>
      <mesh>
        <icosahedronGeometry args={[1.5, 3]} />
        <meshBasicMaterial color={PALETTE.water} wireframe transparent opacity={0.46} />
      </mesh>
      <mesh scale={1.012}>
        <icosahedronGeometry args={[1.5, 2]} />
        <meshBasicMaterial color={PALETTE.vegetation} wireframe transparent opacity={0.12} />
      </mesh>
      <mesh scale={1.06}>
        <icosahedronGeometry args={[1.5, 3]} />
        <meshBasicMaterial color={PALETTE.water} wireframe transparent opacity={0.08} />
      </mesh>
      <LatitudeRing y={0.55} radius={1.38} />
      <LatitudeRing y={-0.55} radius={1.38} />
    </group>
  );
}

function Orbit({ tilt, speed, color, distance }: { tilt: number; speed: number; color: string; distance: number }) {
  const ref = useRef<THREE.Group>(null);
  const reducedMotion = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, []);
  useFrame((state) => {
    if (!ref.current || reducedMotion) return;
    ref.current.rotation.z = tilt + state.clock.elapsedTime * speed;
  });

  return (
    <group ref={ref} rotation={[0.42, 0.15, tilt]}>
      <mesh position={[distance, 0, 0]}>
        <boxGeometry args={[0.12, 0.12, 0.12]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <mesh position={[distance, 0, 0]}>
        <boxGeometry args={[0.28, 0.045, 0.045]} />
        <meshBasicMaterial color={color} transparent opacity={0.8} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[distance, 0.008, 4, 96]} />
        <meshBasicMaterial color={color} transparent opacity={0.22} />
      </mesh>
    </group>
  );
}

function ScanArc() {
  const ref = useRef<THREE.Mesh>(null);
  const reducedMotion = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, []);
  useFrame((state) => {
    if (!ref.current || reducedMotion) return;
    ref.current.rotation.z = state.clock.elapsedTime * 0.45;
    const scale = 1 + Math.sin(state.clock.elapsedTime * 2.4) * 0.035;
    ref.current.scale.setScalar(scale);
  });
  return (
    <mesh ref={ref} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[1.72, 0.012, 5, 128, Math.PI * 0.48]} />
      <meshBasicMaterial color={PALETTE.thermal} transparent opacity={0.7} />
    </mesh>
  );
}

function StarField() {
  const positions = useMemo(() => {
    const arr = new Float32Array(150 * 3);
    for (let i = 0; i < 150; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 7;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 5;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 4 - 1;
    }
    return arr;
  }, []);
  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color={PALETTE.water} size={0.018} transparent opacity={0.5} />
    </points>
  );
}

export function HeroGlobe() {
  return (
    <div className="h-64 w-full sm:h-72" aria-label="Animated 3D satellite Earth visualization">
      <Canvas camera={{ position: [0, 0, 5.2], fov: 43 }} gl={{ alpha: true, antialias: true }} dpr={[1, 1.5]}>
        <StarField />
        <Globe />
        <Orbit tilt={0.3} speed={0.42} color={PALETTE.thermal} distance={2.15} />
        <Orbit tilt={-0.75} speed={-0.27} color={PALETTE.orbit} distance={1.95} />
        <ScanArc />
      </Canvas>
    </div>
  );
}
