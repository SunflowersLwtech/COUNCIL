"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Stars } from "@react-three/drei";
import * as THREE from "three";
import { SceneLighting } from "./SceneLighting";
import { Table } from "./Table";
import { AgentFigure } from "./AgentFigure";
import { AgentNameplate } from "./AgentNameplate";
import { CameraRig } from "./CameraRig";
import {
  getSeatPosition,
  type CameraView,
  type Agent3DConfig,
} from "@/lib/scene-constants";

interface RoundtableCanvasProps {
  speakingAgentId: string | null;
  thinkingAgentIds: string[];
  cameraView: CameraView;
  autoFocusEnabled: boolean;
  agents: Agent3DConfig[];
}

/* ── Floating particles (firefly effect) ─────────────────────────── */
function FloatingParticles({ count = 80 }: { count?: number }) {
  const meshRef = useRef<THREE.Points>(null);

  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 14;
      pos[i * 3 + 1] = Math.random() * 5 + 0.5;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 14;
      vel[i * 3] = (Math.random() - 0.5) * 0.003;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.002;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.003;
    }
    return [pos, vel];
  }, [count]);

  useFrame(() => {
    if (!meshRef.current) return;
    const geo = meshRef.current.geometry;
    const posAttr = geo.getAttribute("position") as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    for (let i = 0; i < count; i++) {
      arr[i * 3] += velocities[i * 3];
      arr[i * 3 + 1] += velocities[i * 3 + 1];
      arr[i * 3 + 2] += velocities[i * 3 + 2];
      // Wrap around
      if (Math.abs(arr[i * 3]) > 7) velocities[i * 3] *= -1;
      if (arr[i * 3 + 1] > 5.5 || arr[i * 3 + 1] < 0.3)
        velocities[i * 3 + 1] *= -1;
      if (Math.abs(arr[i * 3 + 2]) > 7) velocities[i * 3 + 2] *= -1;
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.04}
        color="#ff6b35"
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}

/* ── Ground grid (sci-fi floor) ──────────────────────────────────── */
function SciFiFloor() {
  return (
    <group>
      {/* Reflective dark floor */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        receiveShadow
      >
        <circleGeometry args={[10, 64]} />
        <meshStandardMaterial
          color="#08081a"
          metalness={0.8}
          roughness={0.3}
        />
      </mesh>

      {/* Subtle radial glow on floor under table */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
        <ringGeometry args={[1.5, 3.2, 64]} />
        <meshBasicMaterial
          color="#ff6b35"
          transparent
          opacity={0.04}
          side={THREE.DoubleSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

export function RoundtableCanvas({
  speakingAgentId,
  thinkingAgentIds,
  cameraView,
  autoFocusEnabled,
  agents,
}: RoundtableCanvasProps) {
  const totalSeats = agents.length;
  return (
    <>
      <SceneLighting speakingAgentId={speakingAgentId} agents={agents} />
      <Table />
      {agents.map((agent) => {
        const pos = getSeatPosition(agent.seatIndex, totalSeats);
        return (
          <group key={agent.id}>
            <AgentFigure
              config={agent}
              isSpeaking={speakingAgentId === agent.id}
              isThinking={thinkingAgentIds.includes(agent.id)}
              totalSeats={totalSeats}
            />
            <AgentNameplate
              name={agent.displayName.split(" ")[0]}
              color={agent.color}
              initial={agent.initial}
              isSpeaking={speakingAgentId === agent.id}
              position={pos}
            />
          </group>
        );
      })}
      <CameraRig
        view={cameraView}
        speakingAgentId={speakingAgentId}
        autoFocusEnabled={autoFocusEnabled}
        agents={agents}
      />

      {/* Atmosphere */}
      <Stars
        radius={15}
        depth={40}
        count={1500}
        factor={3}
        saturation={0}
        fade
        speed={0.5}
      />
      <FloatingParticles count={60} />
      <SciFiFloor />
    </>
  );
}
