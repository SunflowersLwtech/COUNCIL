"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Stars, Environment } from "@react-three/drei";
import * as THREE from "three";
import { SceneLighting } from "./SceneLighting";
import { Table } from "./Table";
import { AgentFigure } from "./AgentFigure";
import { AgentNameplate } from "./AgentNameplate";
import { CameraRig } from "./CameraRig";
import { PostProcessing } from "./PostProcessing";
import {
  getSeatPosition,
  type CameraView,
  type Agent3DConfig,
} from "@/lib/scene-constants";
import type { GamePhase } from "@/lib/game-types";

interface RoundtableCanvasProps {
  speakingAgentId: string | null;
  thinkingAgentIds: string[];
  cameraView: CameraView;
  autoFocusEnabled: boolean;
  agents: Agent3DConfig[];
  gamePhase?: GamePhase;
  round?: number;
}

/* ── Floating particles (firefly effect) ─────────────────────────── */
function FloatingParticles({ count = 100 }: { count?: number }) {
  const meshRef = useRef<THREE.Points>(null);

  const [positions, velocities, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    const sz = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 14;
      pos[i * 3 + 1] = Math.random() * 5 + 0.5;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 14;
      vel[i * 3] = (Math.random() - 0.5) * 0.003;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.002;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.003;
      sz[i] = 0.02 + Math.random() * 0.06;
    }
    return [pos, vel, sz];
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
        <bufferAttribute
          attach="attributes-size"
          args={[sizes, 1]}
          count={count}
          itemSize={1}
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
  const spinRingRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (spinRingRef.current) {
      spinRingRef.current.rotation.z = state.clock.elapsedTime * 0.12;
    }
  });

  return (
    <group>
      {/* Reflective dark floor */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        receiveShadow
      >
        <circleGeometry args={[12, 64]} />
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

      {/* Concentric floor rings for grid effect */}
      {[4, 6, 8].map((r) => (
        <mesh key={r} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 0]}>
          <ringGeometry args={[r - 0.01, r + 0.01, 64]} />
          <meshBasicMaterial
            color="#4466ff"
            transparent
            opacity={0.02}
            side={THREE.DoubleSide}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
      ))}

      {/* Slowly rotating accent ring */}
      <mesh
        ref={spinRingRef}
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0.008, 0]}
      >
        <ringGeometry args={[3.4, 3.5, 64]} />
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
  gamePhase = "discussion",
  round = 1,
}: RoundtableCanvasProps) {
  const totalSeats = agents.length;
  return (
    <>
      <SceneLighting speakingAgentId={speakingAgentId} agents={agents} gamePhase={gamePhase} round={round} />

      {/* Environment map for reflections on metallic surfaces */}
      <Environment preset="night" background={false} />

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

      {/* Atmosphere – enhanced stars */}
      <Stars
        radius={20}
        depth={40}
        count={2500}
        factor={3}
        saturation={0}
        fade
        speed={0.5}
      />
      {/* Blue accent stars at closer range */}
      <Stars
        radius={8}
        depth={20}
        count={500}
        factor={5}
        saturation={0.8}
        fade
        speed={0.3}
      />

      <FloatingParticles count={100} />
      <SciFiFloor />

      {/* Post-processing effects (bloom + vignette) — phase-reactive */}
      <PostProcessing gamePhase={gamePhase} round={round} />
    </>
  );
}
