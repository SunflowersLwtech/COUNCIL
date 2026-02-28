"use client";

import { Html } from "@react-three/drei";

interface AgentNameplateProps {
  name: string;
  color: string;
  initial: string;
  isSpeaking: boolean;
  position: [number, number, number];
}

export function AgentNameplate({
  name,
  color,
  initial,
  isSpeaking,
  position,
}: AgentNameplateProps) {
  return (
    <Html
      position={[position[0], position[1] + 1.45, position[2]]}
      center
      distanceFactor={6}
      style={{ pointerEvents: "none", userSelect: "none" }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "5px",
          padding: "3px 10px",
          background: isSpeaking
            ? "rgba(15, 15, 26, 0.92)"
            : "rgba(15, 15, 26, 0.75)",
          borderRadius: "10px",
          border: `1px solid ${isSpeaking ? color : "rgba(255,255,255,0.08)"}`,
          whiteSpace: "nowrap",
          fontSize: "11px",
          color: "#e4e4e7",
          backdropFilter: "blur(8px)",
          boxShadow: isSpeaking
            ? `0 0 12px ${color}40, 0 2px 8px rgba(0,0,0,0.4)`
            : "0 2px 8px rgba(0,0,0,0.3)",
          transition: "all 0.3s ease",
          transform: isSpeaking ? "scale(1.05)" : "scale(1)",
        }}
      >
        <span
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: color,
            display: "inline-block",
            boxShadow: isSpeaking ? `0 0 8px ${color}` : "none",
            animation: isSpeaking
              ? "pulse-dot 1.5s ease-in-out infinite"
              : "none",
          }}
        />
        <span style={{ fontWeight: 700, color }}>{initial}</span>
        <span style={{ opacity: 0.8, fontWeight: 500 }}>{name}</span>
      </div>
    </Html>
  );
}
