"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { getSeatPosition, type Agent3DConfig } from "@/lib/scene-constants";

interface SceneLightingProps {
  speakingAgentId: string | null;
  agents: Agent3DConfig[];
}

export function SceneLighting({ speakingAgentId, agents }: SceneLightingProps) {
  const spotlightRef = useRef<THREE.SpotLight>(null);
  const targetPos = useRef(new THREE.Vector3(0, 0, 0));

  useFrame(() => {
    if (!spotlightRef.current) return;

    if (speakingAgentId) {
      const agent = agents.find((a) => a.id === speakingAgentId);
      if (agent) {
        const pos = getSeatPosition(agent.seatIndex, agents.length);
        targetPos.current.set(pos[0], 1.0, pos[2]);
      }
    } else {
      targetPos.current.set(0, 0, 0);
    }

    spotlightRef.current.target.position.lerp(targetPos.current, 0.05);
    spotlightRef.current.target.updateMatrixWorld();
  });

  return (
    <>
      {/* Base ambient – keep low for dramatic look */}
      <ambientLight intensity={0.25} color="#8888cc" />

      {/* Main directional – cool tone key light */}
      <directionalLight
        position={[5, 8, 5]}
        intensity={0.5}
        color="#c8d8ff"
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-camera-far={20}
        shadow-camera-near={1}
        shadow-camera-left={-6}
        shadow-camera-right={6}
        shadow-camera-top={6}
        shadow-camera-bottom={-6}
      />

      {/* Warm overhead fill from table area */}
      <pointLight
        position={[0, 3.5, 0]}
        intensity={0.3}
        color="#ff9060"
        distance={8}
        decay={2}
      />

      {/* Subtle rim light from behind */}
      <pointLight
        position={[0, 2, -5]}
        intensity={0.15}
        color="#4466ff"
        distance={10}
        decay={2}
      />

      {/* Spotlight follows speaking agent */}
      {speakingAgentId && (
        <spotLight
          ref={spotlightRef}
          position={[0, 6, 0]}
          angle={0.25}
          penumbra={0.6}
          intensity={1.2}
          color="#ffffff"
          castShadow
          distance={12}
          decay={2}
        />
      )}
    </>
  );
}
