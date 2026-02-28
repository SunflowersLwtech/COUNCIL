"use client";

import { useState } from "react";
import { Eye, EyeOff, Shield, Swords, Target, Users } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { seedToColor } from "@/components/CharacterCard";

export default function PlayerRoleCard() {
  const { playerRole, session, isGhostMode } = useGameState();
  const [isOpen, setIsOpen] = useState(false);

  if (!playerRole || !session) return null;

  const isEvil = playerRole.allies.length > 0;
  const accentColor = isEvil ? "#ef4444" : "#3b82f6";

  return (
    <>
      {/* Floating peek button */}
      <button
        className="role-card-peek-btn"
        onClick={() => setIsOpen(true)}
        title="Peek at your identity"
        style={{
          borderColor: isGhostMode ? "rgba(255,255,255,0.2)" : `${accentColor}40`,
          boxShadow: `0 0 12px ${accentColor}20`,
        }}
      >
        <Eye size={16} style={{ color: accentColor }} />
      </button>

      {/* Modal overlay */}
      {isOpen && (
        <div className="role-card-modal-overlay" onClick={() => setIsOpen(false)}>
          <div
            className="role-card-modal glass-card animate-fade-in-up"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="role-card-header">
              <EyeOff size={14} style={{ color: accentColor }} />
              <span className="role-card-label">Your Secret Identity</span>
            </div>

            {/* Role */}
            <div className="role-card-section">
              <div className="role-card-field-label">
                <Shield size={12} style={{ color: accentColor }} />
                <span>Hidden Role</span>
              </div>
              <p className="role-card-value" style={{ color: accentColor }}>
                {playerRole.hidden_role}
              </p>
            </div>

            {/* Faction */}
            <div className="role-card-section">
              <div className="role-card-field-label">
                <Swords size={12} style={{ color: accentColor }} />
                <span>Faction</span>
              </div>
              <p className="role-card-value">
                {playerRole.faction}
              </p>
            </div>

            {/* Win Condition */}
            <div className="role-card-section">
              <div className="role-card-field-label">
                <Target size={12} style={{ color: accentColor }} />
                <span>Win Condition</span>
              </div>
              <p className="role-card-win-condition">
                {playerRole.win_condition}
              </p>
            </div>

            {/* Allies (for wolves) */}
            {playerRole.allies.length > 0 && (
              <div className="role-card-section">
                <div className="role-card-field-label">
                  <Users size={12} style={{ color: "#ef4444" }} />
                  <span style={{ color: "#ef4444" }}>Your Allies</span>
                </div>
                <div className="role-card-allies">
                  {playerRole.allies.map((ally) => {
                    const char = session.characters.find((c) => c.id === ally.id);
                    const color = char ? seedToColor(char.avatar_seed || char.id) : "#ef4444";
                    return (
                      <div key={ally.id} className="role-card-ally">
                        <div
                          className="role-card-ally-dot"
                          style={{ backgroundColor: color }}
                        />
                        <span>{ally.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Role power hint */}
            <div className="role-card-hint">
              {isEvil
                ? "You can kill a target during the night phase."
                : playerRole.hidden_role.toLowerCase().includes("seer")
                  ? "You can investigate one player each night to learn their faction."
                  : playerRole.hidden_role.toLowerCase().includes("doctor")
                    ? "You can protect one player each night from being killed."
                    : "You have no special night power. Use your wits during discussion."
              }
            </div>

            <button
              className="demo-btn role-card-close-btn"
              onClick={() => setIsOpen(false)}
            >
              Hide
            </button>
          </div>
        </div>
      )}
    </>
  );
}
