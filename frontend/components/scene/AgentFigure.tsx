"use client";

import { useRef, useMemo } from "react";
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
  const bodyRef = useRef<THREE.Mesh>(null);
  const beamRef = useRef<THREE.Mesh>(null);

  const pos = getSeatPosition(config.seatIndex, totalSeats);
  const facingAngle = Math.atan2(-pos[0], -pos[2]);
  const agentColor = useMemo(() => new THREE.Color(config.color), [config.color]);

  useFrame((state) => {
    const time = state.clock.elapsedTime;

    if (!groupRef.current || !headRef.current) return;

    // Gentle idle float for all states
    const floatY = Math.sin(time * 0.8 + config.seatIndex) * 0.015;

    if (isSpeaking) {
      // Speaking: head bob + body scale pulse + emissive oscillation
      headRef.current.position.y = 1.0 + Math.sin(time * 8) * 0.03;
      const speakScale = Math.sin(time * 6) * 0.02 + 1.0;
      groupRef.current.scale.set(speakScale, speakScale, speakScale);
      groupRef.current.position.y = floatY;

      // Animate body emissive intensity
      if (bodyRef.current) {
        const mat = bodyRef.current.material as THREE.MeshStandardMaterial;
        mat.emissiveIntensity = 0.2 + Math.sin(time * 4) * 0.15;
      }
    } else if (isThinking) {
      // Thinking: Y rotation micro-sway and slight Y bounce
      groupRef.current.rotation.y = facingAngle + Math.sin(time * 3) * 0.05;
      groupRef.current.position.y = Math.sin(time * 4) * 0.02 + floatY;
      headRef.current.position.y = 1.0;
      groupRef.current.scale.set(1, 1, 1);

      if (bodyRef.current) {
        const mat = bodyRef.current.material as THREE.MeshStandardMaterial;
        mat.emissiveIntensity = 0.15;
      }
    } else {
      // Idle: breathing effect + gentle float
      const idleScale = Math.sin(time * 1.5) * 0.01 + 1.0;
      groupRef.current.scale.set(idleScale, idleScale, idleScale);
      groupRef.current.rotation.y = facingAngle;
      groupRef.current.position.y = floatY;
      headRef.current.position.y = 1.0;

      if (bodyRef.current) {
        const mat = bodyRef.current.material as THREE.MeshStandardMaterial;
        mat.emissiveIntensity = 0.05;
      }
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

    // Animate speaking beam
    if (beamRef.current) {
      if (isSpeaking) {
        beamRef.current.visible = true;
        const beamMat = beamRef.current.material as THREE.MeshBasicMaterial;
        beamMat.opacity = 0.06 + Math.sin(time * 3) * 0.03;
      } else {
        beamRef.current.visible = false;
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

        {/* Body – tapered cylinder with improved materials */}
        <mesh ref={bodyRef} position={[0, 0.45, 0]} castShadow>
          <cylinderGeometry args={[0.18, 0.24, 0.85, 16]} />
          <meshStandardMaterial
            color={config.color}
            emissive={config.color}
            emissiveIntensity={isSpeaking ? 0.35 : isThinking ? 0.15 : 0.05}
            metalness={0.5}
            roughness={0.4}
          />
        </mesh>

        {/* Body segmentation ring – lower */}
        <mesh position={[0, 0.35, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.235, 0.245, 32]} />
          <meshBasicMaterial
            color={config.color}
            transparent
            opacity={0.15}
            side={THREE.DoubleSide}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>

        {/* Body segmentation ring – upper */}
        <mesh position={[0, 0.55, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.21, 0.22, 32]} />
          <meshBasicMaterial
            color={config.color}
            transparent
            opacity={0.15}
            side={THREE.DoubleSide}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
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
            metalness={0.3}
            roughness={0.5}
          />
        </mesh>

        {/* Visor ring across head */}
        <mesh position={[0, 1.02, 0.02]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.16, 0.012, 8, 32]} />
          <meshBasicMaterial
            color={config.color}
            transparent
            opacity={isSpeaking ? 0.9 : 0.5}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>

        {/* Head glow halo (visible when speaking) */}
        <mesh position={[0, 1.0, 0]} visible={isSpeaking}>
          <sphereGeometry args={[0.25, 16, 16]} />
          <meshBasicMaterial
            color={config.color}
            transparent
            opacity={0.08}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>

        {/* Vertical light beam above speaking agent */}
        <mesh
          ref={beamRef}
          position={[0, 2.2, 0]}
          visible={false}
        >
          <cylinderGeometry args={[0.03, 0.06, 2.0, 8]} />
          <meshBasicMaterial
            color={config.color}
            transparent
            opacity={0.06}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
      </group>
    </group>
  );
}
