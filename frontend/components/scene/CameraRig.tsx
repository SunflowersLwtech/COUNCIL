"use client";

import { useRef, useEffect, useCallback } from "react";
import { CameraControls } from "@react-three/drei";
import { useThree } from "@react-three/fiber";
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
  const userInteractedRef = useRef(false);
  const interactTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { gl } = useThree();

  // Track user interaction to suppress auto-focus temporarily
  const handleUserInteraction = useCallback(() => {
    userInteractedRef.current = true;
    if (interactTimeoutRef.current) clearTimeout(interactTimeoutRef.current);
    interactTimeoutRef.current = setTimeout(() => {
      userInteractedRef.current = false;
    }, 5000);
  }, []);

  // Listen for pointer events on the canvas
  useEffect(() => {
    const canvas = gl.domElement;
    canvas.addEventListener("pointerdown", handleUserInteraction);
    canvas.addEventListener("wheel", handleUserInteraction);
    return () => {
      canvas.removeEventListener("pointerdown", handleUserInteraction);
      canvas.removeEventListener("wheel", handleUserInteraction);
      if (interactTimeoutRef.current) clearTimeout(interactTimeoutRef.current);
    };
  }, [gl, handleUserInteraction]);

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

  // Auto-focus on speaking agent (suppressed during user interaction)
  useEffect(() => {
    const controls = controlsRef.current;
    if (!controls || !autoFocusEnabled || !speakingAgentId) return;
    if (userInteractedRef.current) return;

    const agent = agents.find((a) => a.id === speakingAgentId);
    if (!agent) return;

    const pos = getSeatPosition(agent.seatIndex, agents.length);
    controls.setTarget(pos[0], 1.0, pos[2], true);
  }, [speakingAgentId, autoFocusEnabled, agents]);

  return (
    <CameraControls
      ref={controlsRef}
      enabled={true}
      makeDefault
      smoothTime={0.35}
      minDistance={1.5}
      maxDistance={15}
      minPolarAngle={0.1}
      maxPolarAngle={Math.PI / 2 - 0.05}
    />
  );
}
