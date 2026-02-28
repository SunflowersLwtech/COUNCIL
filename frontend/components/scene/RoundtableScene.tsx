"use client";

import { Component, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import * as THREE from "three";
import { RoundtableCanvas } from "./RoundtableCanvas";
import type { CameraView, Agent3DConfig } from "@/lib/scene-constants";
import type { GamePhase } from "@/lib/game-types";

const BG_COLOR = new THREE.Color("#060612");

interface RoundtableSceneProps {
  speakingAgentId: string | null;
  thinkingAgentIds: string[];
  cameraView: CameraView;
  autoFocusEnabled: boolean;
  agents: Agent3DConfig[];
  gamePhase?: GamePhase;
  round?: number;
}

class SceneErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: string }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: "" };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: "#060612",
            color: "#e4e4e7",
            gap: "16px",
          }}
        >
          <p style={{ fontSize: "18px", fontWeight: 600 }}>3D Scene Failed</p>
          <p style={{ fontSize: "14px", color: "#71717a" }}>
            {this.state.error}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: "" })}
            style={{
              padding: "8px 20px",
              borderRadius: "8px",
              background: "#ff6b35",
              color: "white",
              border: "none",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function RoundtableScene(props: RoundtableSceneProps) {
  return (
    <SceneErrorBoundary>
      <Canvas
        style={{ background: "#060612" }}
        camera={{ position: [0, 1.6, -2.5], fov: 60 }}
        shadows
        gl={{
          antialias: true,
          alpha: false,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.1,
        }}
        onCreated={({ gl, scene }) => {
          gl.setClearColor("#060612", 1);
          scene.background = BG_COLOR;
          scene.fog = new THREE.Fog("#060612", 10, 30);
        }}
      >
        <RoundtableCanvas
          speakingAgentId={props.speakingAgentId}
          thinkingAgentIds={props.thinkingAgentIds}
          cameraView={props.cameraView}
          autoFocusEnabled={props.autoFocusEnabled}
          agents={props.agents}
          gamePhase={props.gamePhase}
          round={props.round}
        />
      </Canvas>
    </SceneErrorBoundary>
  );
}
