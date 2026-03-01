"use client";

import { useCallback } from "react";
import { Trophy, RotateCcw, Shield, Skull, Heart } from "lucide-react";
import DocumentUpload from "@/components/DocumentUpload";
import GameLobby from "@/components/GameLobby";
import HowToPlay from "@/components/HowToPlay";
import GameBoard from "@/components/GameBoard";
import GameIntro from "@/components/GameIntro";
import StartingOverlay from "@/components/StartingOverlay";
import CharacterCard, { seedToColor } from "@/components/CharacterCard";
import LanguageToggle from "@/components/LanguageToggle";
import { GameStateProvider, useGameState } from "@/hooks/useGameState";
import { RoundtableProvider } from "@/hooks/useRoundtable";
import { useVoice } from "@/hooks/useVoice";
import { I18nProvider, useI18n, type Locale } from "@/lib/i18n";

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

  if (game.isRecovering) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#060612",
          color: "#888",
          fontSize: "0.875rem",
        }}
      >
        Restoring session...
      </div>
    );
  }

  // Show starting overlay with progress bar during game initialization
  if (game.isStarting) {
    return <StartingOverlay progress={game.startProgress} statusText={game.startStatusText} />;
  }

  // Game board manages its own language toggle in the top bar
  const isGamePhase = ["discussion", "voting", "reveal", "night"].includes(game.phase);

  const langToggle = !isGamePhase ? (
    <div className="global-lang-toggle">
      <LanguageToggle />
    </div>
  ) : null;

  let content;
  switch (game.phase) {
    case "upload":
    case "parsing":
      content = <DocumentUpload />;
      break;
    case "lobby":
      content = <GameLobby />;
      break;
    case "howtoplay":
      content = (
        <HowToPlay
          onStart={game.startGame}
          worldTitle={game.session?.world_title}
        />
      );
      break;
    case "intro":
      content = <GameIntro />;
      break;
    case "discussion":
    case "voting":
    case "reveal":
    case "night":
      content = <GameBoard />;
      break;
    case "ended":
      content = <GameEndScreen />;
      break;
    default:
      content = <DocumentUpload />;
  }

  return (
    <>
      {langToggle}
      {content}
    </>
  );
}

/* ── Home Inner ───────────────────────────────────────────────────── */

function HomeInner() {
  const gameVoice = useVoice({
    onTranscript: () => {}, // STT handled in GameBoard
  });

  const handleCharacterResponse = useCallback(
    (content: string, characterName: string, voiceId?: string, characterId?: string) => {
      // Use character_id (UUID) so backend can look up the correct voice
      const agentId = characterId || voiceId || characterName;
      gameVoice.queueSingleResponse(content, agentId);
    },
    [gameVoice.queueSingleResponse]
  );

  return (
    <GameStateProvider onCharacterResponse={handleCharacterResponse}>
      <RoundtableProvider>
        <div className="relative">
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
