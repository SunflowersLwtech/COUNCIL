"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { TABLE_RADIUS, TABLE_HEIGHT } from "@/lib/scene-constants";

export function Table() {
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (glowRef.current) {
      const mat = glowRef.current.material as THREE.MeshBasicMaterial;
      mat.opacity = 0.06 + Math.sin(state.clock.elapsedTime * 0.8) * 0.02;
    }
  });

  return (
    <group position={[0, TABLE_HEIGHT, 0]}>
      {/* Tabletop */}
      <mesh receiveShadow>
        <cylinderGeometry args={[TABLE_RADIUS, TABLE_RADIUS, 0.06, 48]} />
        <meshStandardMaterial
          color="#141428"
          metalness={0.6}
          roughness={0.3}
          emissive="#1a1a3a"
          emissiveIntensity={0.1}
        />
      </mesh>

      {/* Tabletop edge glow ring */}
      <mesh position={[0, 0.035, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[TABLE_RADIUS - 0.02, TABLE_RADIUS + 0.01, 64]} />
        <meshBasicMaterial
          color="#ff6b35"
          transparent
          opacity={0.15}
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
    </group>
  );
}
