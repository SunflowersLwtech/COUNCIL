"use client";

import { useState } from "react";
import { Shield, Target, Swords, Clock, Eye } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import type { CharacterRevealed } from "@/lib/game-types";
import { seedToColor } from "@/components/CharacterCard";

interface CharacterRevealProps {
  character: CharacterRevealed;
  onDismiss: () => void;
}

export default function CharacterReveal({
  character,
  onDismiss,
}: CharacterRevealProps) {
  const { t } = useI18n();
  const [flipped, setFlipped] = useState(false);
  const color = seedToColor(character.avatar_seed || character.id);
  const initial = character.name.charAt(0).toUpperCase();

  return (
    <div className="reveal-overlay" onClick={onDismiss}>
      <div
        className="max-w-md w-full mx-4 animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="glass-card p-8 space-y-6 animate-reveal-glow"
          style={{ cursor: "pointer" }}
          onClick={() => setFlipped(!flipped)}
        >
          {/* Avatar */}
          <div className="flex flex-col items-center gap-3">
            <div
              className="flex items-center justify-center rounded-full font-bold text-white text-2xl"
              style={{
                width: 64,
                height: 64,
                backgroundColor: color,
                boxShadow: `0 0 20px ${color}60`,
              }}
            >
              {initial}
            </div>
            <h2
              className="text-xl font-bold"
              style={{ color: "var(--text-primary)" }}
            >
              {character.name}
            </h2>
          </div>

          {!flipped ? (
            /* Front: Public role */
            <div className={`text-center space-y-2 ${flipped ? "animate-card-flip" : ""}`}>
              <p
                className="text-sm"
                style={{ color: "var(--text-muted)" }}
              >
                {character.public_role}
              </p>
              <p
                className="text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                (Click to reveal)
              </p>
            </div>
          ) : (
            /* Back: Hidden role */
            <div className="space-y-4 animate-fade-in">
              {/* True Role */}
              <div className="flex items-center gap-2">
                <Shield size={14} style={{ color: "var(--accent)" }} />
                <span
                  className="text-xs font-semibold uppercase tracking-wider"
                  style={{ color: "var(--text-muted)" }}
                >
                  {t("game.reveal.trueRole")}
                </span>
              </div>
              <p
                className="text-lg font-bold"
                style={{ color: "var(--accent)" }}
              >
                {character.hidden_role}
              </p>

              {/* Faction */}
              <div className="flex items-center gap-2">
                <Swords size={14} style={{ color: "var(--accent)" }} />
                <span
                  className="text-xs font-semibold uppercase tracking-wider"
                  style={{ color: "var(--text-muted)" }}
                >
                  {t("game.reveal.faction")}
                </span>
              </div>
              <p
                className="text-sm font-medium"
                style={{ color: "var(--text-primary)" }}
              >
                {character.faction}
              </p>

              {/* Win Condition */}
              <div className="flex items-center gap-2">
                <Target size={14} style={{ color: "var(--accent)" }} />
                <span
                  className="text-xs font-semibold uppercase tracking-wider"
                  style={{ color: "var(--text-muted)" }}
                >
                  {t("game.reveal.winCondition")}
                </span>
              </div>
              <p
                className="text-sm"
                style={{ color: "var(--text-secondary)" }}
              >
                {character.win_condition}
              </p>

              {/* Hidden Knowledge */}
              {character.hidden_knowledge && character.hidden_knowledge.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Eye size={14} style={{ color: "#8b5cf6" }} />
                    <span
                      className="text-xs font-semibold uppercase tracking-wider"
                      style={{ color: "var(--text-muted)" }}
                    >
                      Hidden Knowledge
                    </span>
                  </div>
                  <div className="space-y-1">
                    {character.hidden_knowledge.map((k, i) => (
                      <p
                        key={i}
                        className="text-xs p-2 rounded-lg"
                        style={{
                          background: "rgba(139, 92, 246, 0.08)",
                          border: "1px solid rgba(139, 92, 246, 0.15)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {k}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Lie Timeline */}
              {character.lie_timeline && character.lie_timeline.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Clock size={14} style={{ color: "var(--critical)" }} />
                    <span
                      className="text-xs font-semibold uppercase tracking-wider"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {t("game.reveal.lies")}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {character.lie_timeline.map((lie, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg text-xs"
                        style={{
                          background: "rgba(239, 68, 68, 0.08)",
                          border: "1px solid rgba(239, 68, 68, 0.15)",
                        }}
                      >
                        <p style={{ color: "var(--text-secondary)" }}>
                          <strong style={{ color: "var(--critical)" }}>
                            R{lie.round}:
                          </strong>{" "}
                          &ldquo;{lie.statement}&rdquo;
                        </p>
                        <p
                          className="mt-1"
                          style={{ color: "var(--positive)" }}
                        >
                          Truth: {lie.truth}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Continue button */}
          {flipped && (
            <button
              className="demo-btn w-full mt-4"
              onClick={(e) => {
                e.stopPropagation();
                onDismiss();
              }}
            >
              {t("game.reveal.continue")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
