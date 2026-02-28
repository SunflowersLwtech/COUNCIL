"use client";

import { useRef, useEffect } from "react";
import { CameraControls } from "@react-three/drei";
import {
  CAMERA_PRESETS,
  getSeatPosition,
  type CameraView,
  type Agent3DConfig,
} from "@/lib/scene-constants";

interface CameraRigProps {
  view: CameraView;
  speakingAgentId: string | null;
  autoFocusEnabled: boolean;
  agents: Agent3DConfig[];
}

export function CameraRig({
  view,
  speakingAgentId,
  autoFocusEnabled,
  agents,
}: CameraRigProps) {
  const controlsRef = useRef<CameraControls>(null);

  // Switch camera preset when view changes
  useEffect(() => {
    const controls = controlsRef.current;
    if (!controls) return;

    const preset = CAMERA_PRESETS[view];
    controls.setLookAt(
      preset.position[0],
      preset.position[1],
      preset.position[2],
      preset.target[0],
      preset.target[1],
      preset.target[2],
      true
    );
  }, [view]);

  // Auto-focus on speaking agent
  useEffect(() => {
    const controls = controlsRef.current;
    if (!controls || !autoFocusEnabled || !speakingAgentId) return;

    const agent = agents.find((a) => a.id === speakingAgentId);
    if (!agent) return;

    const pos = getSeatPosition(agent.seatIndex, agents.length);
    controls.setTarget(pos[0], 1.0, pos[2], true);
  }, [speakingAgentId, autoFocusEnabled]);

  const isOrbit = view === "orbit";

  return (
    <CameraControls
      ref={controlsRef}
      enabled={isOrbit}
      makeDefault
      minDistance={2}
      maxDistance={15}
      minPolarAngle={0.2}
      maxPolarAngle={Math.PI / 2 - 0.1}
    />
  );
}
