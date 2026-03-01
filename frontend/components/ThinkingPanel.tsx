"use client";

import { useState } from "react";
import { Brain, ChevronDown, ChevronUp } from "lucide-react";
import { useGameState, type AIThought } from "@/hooks/useGameState";
import { seedToColor } from "@/components/CharacterCard";

export default function ThinkingPanel() {
  const { aiThoughts, session } = useGameState();
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!aiThoughts.length) return null;

  const characters = session?.characters || [];
  const getAvatarSeed = (charId: string) => {
    const c = characters.find((ch) => ch.id === charId);
    return c?.avatar_seed || charId;
  };

  return (
    <div className="thinking-panel">
      <button
        className="thinking-panel-header"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="thinking-panel-title">
          <Brain size={16} />
          <span>Inner Thoughts</span>
          {isCollapsed && (
            <span className="thinking-panel-badge">{aiThoughts.length}</span>
          )}
        </div>
        {isCollapsed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {!isCollapsed && (
        <div className="thinking-panel-body">
          {aiThoughts.map((thought, i) => {
            const color = seedToColor(getAvatarSeed(thought.characterId));
            return (
              <div key={i} className="thinking-panel-entry">
                <div
                  className="thinking-panel-avatar"
                  style={{ backgroundColor: color }}
                >
                  {thought.characterName.charAt(0).toUpperCase()}
                </div>
                <div className="thinking-panel-content">
                  <span className="thinking-panel-name">
                    {thought.characterName}
                  </span>
                  <span className="thinking-panel-text">{thought.content}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
