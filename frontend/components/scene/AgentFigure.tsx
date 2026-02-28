"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { getSeatPosition } from "@/lib/scene-constants";
import type { Agent3DConfig } from "@/lib/scene-constants";

interface AgentFigureProps {
  config: Agent3DConfig;
  isSpeaking: boolean;
  isThinking: boolean;
  totalSeats?: number;
}

export function AgentFigure({
  config,
  isSpeaking,
  isThinking,
  totalSeats,
}: AgentFigureProps) {
  const groupRef = useRef<THREE.Group>(null);
  const headRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const pulseRingRef = useRef<THREE.Mesh>(null);

  const pos = getSeatPosition(config.seatIndex, totalSeats);
  const facingAngle = Math.atan2(-pos[0], -pos[2]);
  const color = new THREE.Color(config.color);

  useFrame((state) => {
    const time = state.clock.elapsedTime;

    if (!groupRef.current || !headRef.current) return;

    if (isSpeaking) {
      // Speaking: head bob + body scale pulse
      headRef.current.position.y = 1.0 + Math.sin(time * 8) * 0.03;
      const speakScale = Math.sin(time * 6) * 0.02 + 1.0;
      groupRef.current.scale.set(speakScale, speakScale, speakScale);
    } else if (isThinking) {
      // Thinking: Y rotation micro-sway and slight Y bounce
      groupRef.current.rotation.y = facingAngle + Math.sin(time * 3) * 0.05;
      groupRef.current.position.y = Math.sin(time * 4) * 0.02;
      headRef.current.position.y = 1.0;
      groupRef.current.scale.set(1, 1, 1);
    } else {
      // Idle: breathing effect
      const idleScale = Math.sin(time * 1.5) * 0.01 + 1.0;
      groupRef.current.scale.set(idleScale, idleScale, idleScale);
      groupRef.current.rotation.y = facingAngle;
      groupRef.current.position.y = 0;
      headRef.current.position.y = 1.0;
    }

    // Animate base ring rotation
    if (ringRef.current) {
      ringRef.current.rotation.z = time * 0.5;
    }

    // Animate pulse ring (speaking effect)
    if (pulseRingRef.current) {
      if (isSpeaking) {
        const pulseScale = 1 + Math.sin(time * 4) * 0.3;
        pulseRingRef.current.scale.set(pulseScale, pulseScale, 1);
        (
          pulseRingRef.current.material as THREE.MeshBasicMaterial
        ).opacity = 0.4 - Math.sin(time * 4) * 0.2;
        pulseRingRef.current.visible = true;
      } else {
        pulseRingRef.current.visible = false;
      }
    }
  });

  return (
    <group position={pos}>
      <group ref={groupRef} rotation={[0, facingAngle, 0]}>
        {/* Base glow ring */}
        <mesh
          ref={ringRef}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, 0.02, 0]}
        >
          <ringGeometry args={[0.28, 0.35, 32]} />
          <meshBasicMaterial
            color={config.color}
            transparent
            opacity={isSpeaking ? 0.6 : 0.2}
            side={THREE.DoubleSide}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>

        {/* Speaking pulse ring */}
        <mesh
          ref={pulseRingRef}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, 0.03, 0]}
          visible={false}
        >
          <ringGeometry args={[0.35, 0.55, 32]} />
          <meshBasicMaterial
            color={config.color}
            transparent
            opacity={0.3}
            side={THREE.DoubleSide}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>

        {/* Body – tapered cylinder */}
        <mesh position={[0, 0.45, 0]} castShadow>
          <cylinderGeometry args={[0.18, 0.24, 0.85, 16]} />
          <meshStandardMaterial
            color={config.color}
            emissive={config.color}
            emissiveIntensity={isSpeaking ? 0.35 : isThinking ? 0.15 : 0.05}
            metalness={0.3}
            roughness={0.6}
          />
        </mesh>

        {/* Shoulder accent */}
        <mesh position={[0, 0.88, 0]}>
          <cylinderGeometry args={[0.2, 0.18, 0.06, 16]} />
          <meshStandardMaterial
            color={config.color}
            emissive={config.color}
            emissiveIntensity={isSpeaking ? 0.5 : 0.1}
            metalness={0.5}
            roughness={0.4}
          />
        </mesh>

        {/* Head */}
        <mesh ref={headRef} position={[0, 1.0, 0]} castShadow>
          <sphereGeometry args={[0.18, 16, 16]} />
          <meshStandardMaterial
            color={config.color}
            emissive={config.color}
            emissiveIntensity={isSpeaking ? 0.5 : isThinking ? 0.2 : 0.05}
            metalness={0.2}
            roughness={0.5}
          />
        </mesh>

        {/* Head glow halo (visible when speaking) */}
        {isSpeaking && (
          <mesh position={[0, 1.0, 0]}>
            <sphereGeometry args={[0.25, 16, 16]} />
            <meshBasicMaterial
              color={config.color}
              transparent
              opacity={0.08}
              blending={THREE.AdditiveBlending}
              depthWrite={false}
            />
          </mesh>
        )}
      </group>
    </group>
  );
}
