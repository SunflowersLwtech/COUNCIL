"use client";

import { useCallback } from "react";
import { Globe, Trophy, RotateCcw, Shield, Skull, Heart } from "lucide-react";
import DocumentUpload from "@/components/DocumentUpload";
import GameLobby from "@/components/GameLobby";
import GameBoard from "@/components/GameBoard";
import CharacterCard, { seedToColor } from "@/components/CharacterCard";
import { GameStateProvider, useGameState } from "@/hooks/useGameState";
import { RoundtableProvider } from "@/hooks/useRoundtable";
import { useVoice } from "@/hooks/useVoice";
import { I18nProvider, useI18n, type Locale } from "@/lib/i18n";

function LanguageToggle() {
  const { locale, setLocale } = useI18n();
  const next: Locale = locale === "en" ? "zh" : "en";
  return (
    <button
      onClick={() => setLocale(next)}
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
      style={{
        background: "var(--bg-hover)",
        color: "var(--text-secondary)",
        border: "1px solid var(--border)",
      }}
      title={locale === "en" ? "Switch to Chinese" : "Switch to English"}
    >
      <Globe size={14} />
      {locale === "en" ? "EN" : "ZH"}
    </button>
  );
}

/* ── Game End Screen ──────────────────────────────────────────────── */

function GameEndScreen() {
  const { t } = useI18n();
  const game = useGameState();

  if (!game.session) return null;

  const aliveCount = game.session.characters.filter((c) => !c.is_eliminated).length;
  const eliminatedCount = game.session.characters.filter((c) => c.is_eliminated).length;

  return (
    <div className="game-end-screen">
      <div className="game-end-content">
        {/* Winner announcement */}
        <div className="game-end-hero animate-fade-in-up">
          <Trophy size={56} className="game-end-trophy" />
          <h1 className="game-end-title welcome-gradient-text">
            {t("game.end.title")}
          </h1>
          {game.gameEnd && (
            <p className="game-end-winner">
              {t("game.end.winner", { faction: game.gameEnd.winner })}
            </p>
          )}
        </div>

        {/* Game stats */}
        <div className="game-end-stats animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
          <div className="game-end-stat">
            <Shield size={16} style={{ color: "var(--accent)" }} />
            <span className="game-end-stat-value">{game.round}</span>
            <span className="game-end-stat-label">Rounds</span>
          </div>
          <div className="game-end-stat">
            <Skull size={16} style={{ color: "var(--critical)" }} />
            <span className="game-end-stat-value">{eliminatedCount}</span>
            <span className="game-end-stat-label">Eliminated</span>
          </div>
          <div className="game-end-stat">
            <Heart size={16} style={{ color: "var(--positive)" }} />
            <span className="game-end-stat-value">{aliveCount}</span>
            <span className="game-end-stat-label">Survived</span>
          </div>
        </div>

        {/* All characters with role reveals */}
        <div className="game-end-characters animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
          <p className="game-end-section-title">
            {t("game.end.allCharacters")}
          </p>
          <div className="game-end-char-grid">
            {game.session.characters.map((char) => {
              const color = seedToColor(char.avatar_seed || char.id);
              const initial = char.name.charAt(0).toUpperCase();

              return (
                <div
                  key={char.id}
                  className={`game-end-char-card ${char.is_eliminated ? "game-end-char-eliminated" : ""}`}
                >
                  <div
                    className="game-end-char-avatar"
                    style={{
                      backgroundColor: color,
                      boxShadow: `0 0 12px ${color}40`,
                    }}
                  >
                    {initial}
                  </div>
                  <div className="game-end-char-info">
                    <span className="game-end-char-name">{char.name}</span>
                    <span className="game-end-char-role">{char.public_role}</span>
                  </div>
                  {char.is_eliminated && (
                    <Skull size={12} className="game-end-char-skull" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Play again */}
        <div className="game-end-actions animate-fade-in-up" style={{ animationDelay: "0.6s" }}>
          <button
            className="demo-btn flex items-center gap-2"
            onClick={game.resetGame}
          >
            <RotateCcw size={16} />
            {t("game.end.playAgain")}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Game Router ──────────────────────────────────────────────────── */

function GameRouter() {
  const game = useGameState();

  switch (game.phase) {
    case "upload":
    case "parsing":
      return <DocumentUpload />;
    case "lobby":
      return <GameLobby />;
    case "discussion":
    case "voting":
    case "reveal":
    case "night":
      return <GameBoard />;
    case "ended":
      return <GameEndScreen />;
    default:
      return <DocumentUpload />;
  }
}

/* ── Home Inner ───────────────────────────────────────────────────── */

function HomeInner() {
  const gameVoice = useVoice({
    onTranscript: () => {}, // STT handled in GameBoard
  });

  const handleCharacterResponse = useCallback(
    (content: string, characterName: string, voiceId?: string) => {
      // Use voice_id directly as the agent identifier for game characters
      const agentId = voiceId || characterName;
      gameVoice.queueSingleResponse(content, agentId);
    },
    [gameVoice.queueSingleResponse]
  );

  return (
    <GameStateProvider onCharacterResponse={handleCharacterResponse}>
      <RoundtableProvider>
        <div className="relative">
          <div
            style={{
              position: "fixed",
              top: 16,
              right: 16,
              zIndex: 50,
            }}
          >
            <LanguageToggle />
          </div>
          <GameRouter />
        </div>
      </RoundtableProvider>
    </GameStateProvider>
  );
}

export default function Home() {
  return (
    <I18nProvider defaultLocale="zh">
      <HomeInner />
    </I18nProvider>
  );
}
