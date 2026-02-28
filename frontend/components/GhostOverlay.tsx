"use client";

import { Ghost, Eye, Skull, Shield } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { seedToColor } from "@/components/CharacterCard";

export default function GhostOverlay() {
  const { isGhostMode, playerRole, revealedCharacters, session } = useGameState();

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

      {/* Role badges on roster (rendered in CharacterRoster via ghost mode) */}

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
  const { isGhostMode, revealedCharacters, session } = useGameState();

  if (!isGhostMode || revealedCharacters.length === 0) return null;

  const revealed = revealedCharacters.find((c) => c.id === characterId);
  if (!revealed) return null;

  // Determine if evil
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
