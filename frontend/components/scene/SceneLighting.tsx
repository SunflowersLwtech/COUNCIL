"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { getSeatPosition, type Agent3DConfig } from "@/lib/scene-constants";
import type { GamePhase } from "@/lib/game-types";

interface SceneLightingProps {
  speakingAgentId: string | null;
  agents: Agent3DConfig[];
  gamePhase?: GamePhase;
  round?: number;
}

/* ── Phase lighting presets ──────────────────────────────────────── */
interface LightPreset {
  ambient: number;
  tableGlowColor: THREE.Color;
  tableGlowIntensity: number;
  underglowColor: THREE.Color;
  underglowIntensity: number;
}

const LIGHT_PRESETS: Record<string, LightPreset> = {
  discussion: {
    ambient: 0.25,
    tableGlowColor: new THREE.Color("#ff9060"),
    tableGlowIntensity: 0.3,
    underglowColor: new THREE.Color("#6644cc"),
    underglowIntensity: 0.2,
  },
  voting: {
    ambient: 0.08,
    tableGlowColor: new THREE.Color("#cc2244"),
    tableGlowIntensity: 0.45,
    underglowColor: new THREE.Color("#882244"),
    underglowIntensity: 0.3,
  },
  reveal: {
    ambient: 0.05,
    tableGlowColor: new THREE.Color("#ffffff"),
    tableGlowIntensity: 0.6,
    underglowColor: new THREE.Color("#6644cc"),
    underglowIntensity: 0.15,
  },
  night: {
    ambient: 0.05,
    tableGlowColor: new THREE.Color("#6644cc"),
    tableGlowIntensity: 0.2,
    underglowColor: new THREE.Color("#4422aa"),
    underglowIntensity: 0.35,
  },
};

const DEFAULT_LIGHT = LIGHT_PRESETS.discussion;

export function SceneLighting({ speakingAgentId, agents, gamePhase = "discussion", round = 1 }: SceneLightingProps) {
  const spotlightRef = useRef<THREE.SpotLight>(null);
  const ambientRef = useRef<THREE.AmbientLight>(null);
  const tableGlowRef = useRef<THREE.PointLight>(null);
  const underglowRef = useRef<THREE.PointLight>(null);
  const targetPos = useRef(new THREE.Vector3(0, 0, 0));
  const currentColor = useRef(new THREE.Color("#ff9060"));
  const currentUnderColor = useRef(new THREE.Color("#6644cc"));

  useFrame((state, delta) => {
    // Camera follow spotlight
    if (spotlightRef.current) {
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
    }

    // Phase-reactive lighting transitions
    const preset = LIGHT_PRESETS[gamePhase] || DEFAULT_LIGHT;
    const lerpSpeed = 1.5 * delta; // ~2.5s transition

    // Escalating darkness per round: ambient drops 0.03/round
    const roundDrop = Math.max(0, (round - 1) * 0.03);
    const targetAmbient = Math.max(0.02, preset.ambient - roundDrop);

    if (ambientRef.current) {
      ambientRef.current.intensity += (targetAmbient - ambientRef.current.intensity) * lerpSpeed;
    }

    if (tableGlowRef.current) {
      tableGlowRef.current.intensity += (preset.tableGlowIntensity - tableGlowRef.current.intensity) * lerpSpeed;
      currentColor.current.lerp(preset.tableGlowColor, lerpSpeed);
      tableGlowRef.current.color.copy(currentColor.current);

      // Subtle pulse during voting (faster) and discussion (slow)
      const pulseSpeed = gamePhase === "voting" ? 3.0 : 1.0;
      const pulseAmp = gamePhase === "voting" ? 0.08 : 0.03;
      tableGlowRef.current.intensity += Math.sin(state.clock.elapsedTime * pulseSpeed) * pulseAmp;
    }

    if (underglowRef.current) {
      underglowRef.current.intensity += (preset.underglowIntensity - underglowRef.current.intensity) * lerpSpeed;
      currentUnderColor.current.lerp(preset.underglowColor, lerpSpeed);
      underglowRef.current.color.copy(currentUnderColor.current);
    }
  });

  return (
    <>
      {/* Base ambient – phase-reactive */}
      <ambientLight ref={ambientRef} intensity={0.25} color="#8888cc" />

      {/* Main directional – cool tone key light */}
      <directionalLight
        position={[5, 8, 5]}
        intensity={0.5}
        color="#c8d8ff"
      />

      {/* Warm overhead fill from table area – phase-reactive */}
      <pointLight
        ref={tableGlowRef}
        position={[0, 3.5, 0]}
        intensity={0.3}
        color="#ff9060"
        distance={8}
        decay={2}
      />

      {/* Under-table glow – phase-reactive */}
      <pointLight
        ref={underglowRef}
        position={[0, 0.3, 0]}
        intensity={0.2}
        color="#6644cc"
        distance={5}
        decay={2}
      />

      {/* Cyan rim light – left-front */}
      <pointLight
        position={[-4, 2, 3]}
        intensity={0.1}
        color="#00ccff"
        distance={10}
        decay={2}
      />

      {/* Magenta rim light – right-back */}
      <pointLight
        position={[4, 2, -3]}
        intensity={0.08}
        color="#cc44ff"
        distance={10}
        decay={2}
      />

      {/* Blue rim light from behind */}
      <pointLight
        position={[0, 2, -5]}
        intensity={0.15}
        color="#4466ff"
        distance={10}
        decay={2}
      />

      {/* Spotlight follows speaking agent */}
      <spotLight
        ref={spotlightRef}
        position={[0, 6, 0]}
        angle={0.3}
        penumbra={0.6}
        intensity={speakingAgentId ? 1.5 : 0.3}
        color="#fff5e6"
        distance={12}
        decay={2}
      />
    </>
  );
}
