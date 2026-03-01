"use client";

import { useState, useEffect, useCallback } from "react";
import { Shield, Swords, Target, Users } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { seedToColor } from "@/components/CharacterCard";
import { useI18n } from "@/lib/i18n";

type IntroStage = "narration" | "role-reveal";

export default function GameIntro() {
  const { t } = useI18n();
  const { introNarration, playerRole, completeIntro, session } = useGameState();
  const [stage, setStage] = useState<IntroStage>("narration");
  const [cardFlipped, setCardFlipped] = useState(false);
  const [narrationVisible, setNarrationVisible] = useState(false);

  // Fade in narration text after mount
  useEffect(() => {
    const timer = setTimeout(() => setNarrationVisible(true), 300);
    return () => clearTimeout(timer);
  }, []);

  const advanceFromNarration = useCallback(() => {
    if (stage !== "narration") return;
    if (playerRole) {
      setStage("role-reveal");
    } else {
      completeIntro();
    }
  }, [stage, playerRole, completeIntro]);

  // ESC to skip entire intro
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        completeIntro();
      }
      // Click or Enter advances narration stage
      if (stage === "narration" && (e.key === "Enter" || e.key === " ")) {
        advanceFromNarration();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [stage, completeIntro, advanceFromNarration]);

  const handleFlipCard = () => {
    if (!cardFlipped) setCardFlipped(true);
  };

  const factionColor = playerRole?.faction === "evil"
    ? "var(--critical)"
    : "var(--positive)";

  const playerChar = session?.characters.find(c =>
    c.public_role === "Player" || c.name === "You"
  );
  const avatarColor = playerChar
    ? seedToColor(playerChar.avatar_seed || playerChar.id)
    : "var(--accent)";

  return (
    <div className="game-intro-container" onClick={stage === "narration" ? advanceFromNarration : undefined}>
      {/* Letterbox bars */}
      <div className="phase-transition-bar game-intro-bar-top" />
      <div className="phase-transition-bar game-intro-bar-bottom" />

      {/* Stage 1: Narration */}
      {stage === "narration" && (
        <div className="game-intro-narration">
          <div className={`game-intro-narration-text ${narrationVisible ? "game-intro-narration-visible" : ""}`}>
            {introNarration || "The council has assembled..."}
          </div>
          <p className="game-intro-continue-hint">{t("game.intro.clickToContinue")}</p>
          <p className="game-intro-skip-hint">{t("game.intro.skipHint")}</p>
        </div>
      )}

      {/* Stage 2: Role Reveal */}
      {stage === "role-reveal" && playerRole && (
        <div className="game-intro-reveal">
          <h2 className="game-intro-reveal-title animate-fade-in-up">
            {t("game.intro.secretIdentity")}
          </h2>

          <div
            className={`game-intro-card ${cardFlipped ? "game-intro-card-flipped" : ""}`}
            onClick={handleFlipCard}
          >
            {/* Card back */}
            <div className="game-intro-card-face game-intro-card-back glass-card">
              <Shield size={48} className="game-intro-card-icon" />
              <p className="game-intro-card-hint">{t("game.intro.clickToReveal")}</p>
            </div>

            {/* Card front */}
            <div className="game-intro-card-face game-intro-card-front glass-card">
              <div className="game-intro-role-header">
                <div
                  className="game-intro-role-avatar"
                  style={{ backgroundColor: avatarColor, boxShadow: `0 0 16px ${avatarColor}40` }}
                >
                  <Swords size={24} />
                </div>
                <h3 className="game-intro-role-name">{playerRole.hidden_role}</h3>
              </div>

              <div className="game-intro-role-details">
                <div className="game-intro-role-row">
                  <Target size={14} style={{ color: factionColor }} />
                  <span className="game-intro-role-label">{t("game.intro.faction")}</span>
                  <span className="game-intro-role-value" style={{ color: factionColor }}>
                    {playerRole.faction}
                  </span>
                </div>
                <div className="game-intro-role-row">
                  <Shield size={14} style={{ color: "var(--accent)" }} />
                  <span className="game-intro-role-label">{t("game.intro.winCondition")}</span>
                  <span className="game-intro-role-value">{playerRole.win_condition}</span>
                </div>
                {playerRole.allies && playerRole.allies.length > 0 && (
                  <div className="game-intro-role-row">
                    <Users size={14} style={{ color: "var(--critical)" }} />
                    <span className="game-intro-role-label">{t("game.intro.allies")}</span>
                    <span className="game-intro-role-value">
                      {playerRole.allies.map(a => a.name).join(", ")}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {cardFlipped && (
            <button
              className="demo-btn game-intro-enter-btn animate-fade-in-up"
              onClick={(e) => { e.stopPropagation(); completeIntro(); }}
            >
              {t("game.intro.enterCouncil")}
            </button>
          )}

          <p className="game-intro-skip-hint">{t("game.intro.skipHint")}</p>
        </div>
      )}
    </div>
  );
}
