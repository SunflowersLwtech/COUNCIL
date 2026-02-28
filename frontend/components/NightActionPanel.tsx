"use client";

import { useState } from "react";
import { Crosshair, Search, ShieldPlus, Moon } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { seedToColor } from "@/components/CharacterCard";

const ACTION_CONFIG: Record<string, {
  title: string;
  subtitle: string;
  icon: typeof Crosshair;
  accentColor: string;
}> = {
  kill: {
    title: "Choose Your Kill Target",
    subtitle: "Select a council member to eliminate tonight",
    icon: Crosshair,
    accentColor: "#ef4444",
  },
  investigate: {
    title: "Choose Who to Investigate",
    subtitle: "Learn the true faction of one council member",
    icon: Search,
    accentColor: "#8b5cf6",
  },
  protect: {
    title: "Choose Who to Protect",
    subtitle: "Shield a council member from tonight's kill",
    icon: ShieldPlus,
    accentColor: "#22c55e",
  },
};

export default function NightActionPanel() {
  const { nightActionRequired, submitNightAction, isChatStreaming } = useGameState();
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);

  if (!nightActionRequired) return null;

  const config = ACTION_CONFIG[nightActionRequired.actionType] || ACTION_CONFIG.kill;
  const Icon = config.icon;

  return (
    <div className="night-action-panel animate-fade-in-up">
      <div className="night-action-header">
        <div className="night-action-icon-row">
          <Moon size={16} style={{ color: "#a78bfa" }} />
          <Icon size={20} style={{ color: config.accentColor }} />
        </div>
        <h2 className="night-action-title" style={{ color: config.accentColor }}>
          {config.title}
        </h2>
        <p className="night-action-subtitle">{config.subtitle}</p>
      </div>

      <div className="night-action-grid">
        {nightActionRequired.targets.map((target) => {
          const color = seedToColor(target.avatar_seed || target.id);
          const initial = target.name.charAt(0).toUpperCase();
          const isSelected = selectedTarget === target.id;

          return (
            <button
              key={target.id}
              className={`night-action-target ${isSelected ? "night-action-target-selected" : ""}`}
              onClick={() => setSelectedTarget(target.id)}
              disabled={isChatStreaming}
              style={{
                borderColor: isSelected ? config.accentColor : undefined,
                boxShadow: isSelected ? `0 0 16px ${config.accentColor}40` : undefined,
              }}
            >
              <div
                className="night-action-avatar"
                style={{
                  backgroundColor: color,
                  boxShadow: isSelected ? `0 0 12px ${color}80` : undefined,
                }}
              >
                {initial}
              </div>
              <span className="night-action-name">{target.name}</span>
              <span className="night-action-role">{target.public_role}</span>
            </button>
          );
        })}
      </div>

      <button
        className="demo-btn night-action-confirm"
        disabled={!selectedTarget || isChatStreaming}
        onClick={() => selectedTarget && submitNightAction(selectedTarget)}
        style={{
          background: selectedTarget
            ? `linear-gradient(135deg, ${config.accentColor}, ${config.accentColor}cc)`
            : undefined,
        }}
      >
        {isChatStreaming ? "Resolving..." : "Confirm Action"}
      </button>
    </div>
  );
}
