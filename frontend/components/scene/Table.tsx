"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { TABLE_RADIUS, TABLE_HEIGHT } from "@/lib/scene-constants";

export function Table() {
  const glowRef = useRef<THREE.Mesh>(null);
  const ringsGroupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    const time = state.clock.elapsedTime;

    if (glowRef.current) {
      const mat = glowRef.current.material as THREE.MeshBasicMaterial;
      mat.opacity = 0.06 + Math.sin(time * 0.8) * 0.02;
    }

    // Slowly rotate concentric rings
    if (ringsGroupRef.current) {
      ringsGroupRef.current.rotation.z = time * 0.08;
    }
  });

  const ringRadii = [0.5, 0.9, 1.3, 1.6];

  return (
    <group position={[0, TABLE_HEIGHT, 0]}>
      {/* Tabletop – glass-like holographic surface */}
      <mesh receiveShadow>
        <cylinderGeometry args={[TABLE_RADIUS, TABLE_RADIUS, 0.06, 48]} />
        <meshStandardMaterial
          color="#0a0a2a"
          emissive="#111133"
          emissiveIntensity={0.2}
          metalness={0.1}
          roughness={0.1}
          transparent
          opacity={0.85}
        />
      </mesh>

      {/* Concentric ring lines on surface */}
      <group
        ref={ringsGroupRef}
        position={[0, 0.04, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        {ringRadii.map((r, i) => (
          <mesh key={i}>
            <ringGeometry args={[r - 0.008, r + 0.008, 64]} />
            <meshBasicMaterial
              color="#ff6b35"
              transparent
              opacity={0.04 + i * 0.005}
              side={THREE.DoubleSide}
              blending={THREE.AdditiveBlending}
              depthWrite={false}
            />
          </mesh>
        ))}
      </group>

      {/* Tabletop edge glow ring – wider */}
      <mesh position={[0, 0.035, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[TABLE_RADIUS - 0.03, TABLE_RADIUS + 0.02, 64]} />
        <meshBasicMaterial
          color="#ff6b35"
          transparent
          opacity={0.2}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* Outer soft glow ring */}
      <mesh position={[0, 0.035, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[TABLE_RADIUS + 0.02, TABLE_RADIUS + 0.08, 64]} />
        <meshBasicMaterial
          color="#ff6b35"
          transparent
          opacity={0.05}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* Table surface glow */}
      <mesh
        ref={glowRef}
        position={[0, 0.04, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <circleGeometry args={[TABLE_RADIUS - 0.1, 48]} />
        <meshBasicMaterial
          color="#ff6b35"
          transparent
          opacity={0.06}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* Table leg */}
      <mesh position={[0, -0.38, 0]}>
        <cylinderGeometry args={[0.12, 0.18, 0.7, 16]} />
        <meshStandardMaterial
          color="#0e0e22"
          metalness={0.7}
          roughness={0.3}
        />
      </mesh>

      {/* Leg base accent ring */}
      <mesh position={[0, -0.72, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.16, 0.25, 32]} />
        <meshBasicMaterial
          color="#ff6b35"
          transparent
          opacity={0.08}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* Under-table glow light */}
      <pointLight
        position={[0, -0.3, 0]}
        intensity={0.15}
        color="#ff6b35"
        distance={3}
        decay={2}
      />
    </group>
  );
}
