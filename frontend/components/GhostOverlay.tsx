"use client";

import { Ghost, Eye, Skull, Shield, Brain } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { seedToColor } from "@/components/CharacterCard";

export default function GhostOverlay() {
  const { isGhostMode, playerRole, revealedCharacters, aiThoughts } = useGameState();

  if (!isGhostMode || !playerRole) return null;

  return (
    <>
      {/* Ghost banner at top */}
      <div className="ghost-banner animate-fade-in">
        <Ghost size={16} style={{ color: "rgba(255,255,255,0.7)" }} />
        <span>
          Ghost Mode — You were {playerRole.eliminated_by === "vote" ? "voted out" : "killed at night"}.
          You were a <strong style={{ color: "#a78bfa" }}>{playerRole.hidden_role}</strong> of the{" "}
          <strong>{playerRole.faction}</strong>.
        </span>
      </div>

      {/* Full role reveal grid */}
      {revealedCharacters.length > 0 && (
        <div className="ghost-role-grid">
          {revealedCharacters.map((char) => {
            const isEvil =
              char.faction.toLowerCase().includes("werewolf") ||
              char.faction.toLowerCase().includes("evil") ||
              char.faction.toLowerCase().includes("mafia");
            const color = seedToColor(char.avatar_seed || char.id);

            return (
              <div
                key={char.id}
                className={`ghost-role-card ${char.is_eliminated ? "ghost-role-card-dead" : ""}`}
                style={{
                  borderColor: isEvil ? "rgba(239, 68, 68, 0.3)" : "rgba(59, 130, 246, 0.3)",
                }}
              >
                <div
                  className="ghost-role-card-avatar"
                  style={{ backgroundColor: color, opacity: char.is_eliminated ? 0.4 : 1 }}
                >
                  {char.name.charAt(0).toUpperCase()}
                </div>
                <div className="ghost-role-card-info">
                  <span className="ghost-role-card-name">{char.name}</span>
                  <span
                    className="ghost-role-card-role"
                    style={{ color: isEvil ? "#ef4444" : "#3b82f6" }}
                  >
                    {isEvil ? <Skull size={10} /> : <Shield size={10} />}
                    {char.hidden_role}
                  </span>
                  <span className="ghost-role-card-faction">{char.faction}</span>
                </div>
                {char.is_eliminated && (
                  <span className="ghost-role-card-eliminated">Eliminated</span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* AI Thinking panel visible in ghost mode */}
      {aiThoughts.length > 0 && (
        <div className="ghost-thoughts-section">
          <div className="ghost-thoughts-header">
            <Brain size={14} />
            <span>AI Inner Thoughts</span>
          </div>
          <div className="ghost-thoughts-list">
            {aiThoughts.slice(-8).map((thought, i) => (
              <div key={i} className="ghost-thought-entry">
                <strong style={{ color: "#c4b5fd" }}>{thought.characterName}:</strong>{" "}
                <span style={{ opacity: 0.7, fontStyle: "italic" }}>{thought.content}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Spectating indicator replacing input bar */}
      <div className="ghost-spectating-bar">
        <Eye size={12} style={{ color: "rgba(255,255,255,0.4)" }} />
        <span>Spectating... You can see all hidden roles and night actions.</span>
      </div>
    </>
  );
}

/** Small badge showing a character's hidden role in ghost mode */
export function GhostRoleBadge({
  characterId,
}: {
  characterId: string;
}) {
  const { isGhostMode, revealedCharacters } = useGameState();

  if (!isGhostMode || revealedCharacters.length === 0) return null;

  const revealed = revealedCharacters.find((c) => c.id === characterId);
  if (!revealed) return null;

  const isEvil = revealed.faction.toLowerCase().includes("werewolf") ||
    revealed.faction.toLowerCase().includes("evil") ||
    revealed.faction.toLowerCase().includes("mafia");

  return (
    <div
      className="ghost-role-badge"
      style={{
        backgroundColor: isEvil ? "rgba(239, 68, 68, 0.2)" : "rgba(59, 130, 246, 0.2)",
        borderColor: isEvil ? "rgba(239, 68, 68, 0.4)" : "rgba(59, 130, 246, 0.4)",
        color: isEvil ? "#ef4444" : "#3b82f6",
      }}
      title={`${revealed.hidden_role} (${revealed.faction})`}
    >
      {isEvil ? <Skull size={8} /> : <Shield size={8} />}
      <span>{revealed.hidden_role}</span>
    </div>
  );
}
