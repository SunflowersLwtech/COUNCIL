"use client";

import { useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  Send,
  Loader2,
  MessageSquare,
  Mic,
  MicOff,
  Zap,
  Moon,
  Star,
  X,
  AlertTriangle,
} from "lucide-react";
import { useGameState, type GameChatMessage } from "@/hooks/useGameState";
import { useRoundtable } from "@/hooks/useRoundtable";
import { useVoice } from "@/hooks/useVoice";
import { useI18n } from "@/lib/i18n";
import { useMemo } from "react";
import { createAgent3DConfigs, AGENTS_3D } from "@/lib/scene-constants";
import PhaseIndicator from "@/components/PhaseIndicator";
import VotePanel from "@/components/VotePanel";
import CharacterReveal from "@/components/CharacterReveal";
import PlayerRoleCard from "@/components/PlayerRoleCard";
import NightActionPanel from "@/components/NightActionPanel";
import GhostOverlay, { GhostRoleBadge } from "@/components/GhostOverlay";
import { seedToColor } from "@/components/CharacterCard";

const RoundtableScene = dynamic(
  () => import("@/components/scene/RoundtableScene"),
  { ssr: false }
);

/* ── Tension Bar ─────────────────────────────────────────── */

function TensionBar({ tension }: { tension: number }) {
  const pct = Math.min(Math.max(tension, 0), 1) * 100;
  const isHigh = tension > 0.7;
  const isMedium = tension > 0.4;

  const color = isHigh
    ? "#ef4444"
    : isMedium
      ? "#f97316"
      : "#22c55e";

  const glow = isHigh
    ? "0 0 12px rgba(239, 68, 68, 0.6)"
    : isMedium
      ? "0 0 8px rgba(249, 115, 22, 0.4)"
      : "none";

  return (
    <div className="tension-bar-container">
      <Zap size={10} style={{ color, flexShrink: 0 }} />
      <div className="tension-bar-track">
        <div
          className="tension-bar-fill"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, #22c55e, #f97316, #ef4444)`,
            boxShadow: glow,
          }}
        />
      </div>
    </div>
  );
}

/* ── Character Roster (left side) ───────────────────────── */

function CharacterRoster() {
  const game = useGameState();
  const { t } = useI18n();

  if (!game.session) return null;

  const aliveChars = game.session.characters.filter((c) => !c.is_eliminated);
  const deadChars = game.session.characters.filter((c) => c.is_eliminated);

  return (
    <div className="character-roster">
      {aliveChars.map((char) => {
        const color = seedToColor(char.avatar_seed || char.id);
        const initial = char.name.charAt(0).toUpperCase();
        const isTarget = game.chatTarget === char.id;

        return (
          <button
            key={char.id}
            className={`roster-avatar ${isTarget ? "roster-avatar-targeted" : ""}`}
            style={{
              "--avatar-color": color,
              borderColor: isTarget ? "var(--accent)" : "transparent",
            } as React.CSSProperties}
            onClick={() =>
              game.setChatTarget(isTarget ? null : char.id)
            }
            title={`${char.name} - ${char.public_role}${isTarget ? " (targeted)" : ""}`}
          >
            <div
              className="roster-avatar-circle"
              style={{ backgroundColor: color }}
            >
              {initial}
            </div>
            <span className="roster-avatar-name">{char.name.split(" ")[0]}</span>
            <GhostRoleBadge characterId={char.id} />
          </button>
        );
      })}

      {deadChars.length > 0 && (
        <div className="roster-divider" />
      )}

      {deadChars.map((char) => {
        const color = seedToColor(char.avatar_seed || char.id);
        const initial = char.name.charAt(0).toUpperCase();

        return (
          <div key={char.id} className="roster-avatar roster-avatar-dead" title={`${char.name} - Eliminated`}>
            <div
              className="roster-avatar-circle"
              style={{ backgroundColor: color }}
            >
              {initial}
            </div>
            <span className="roster-avatar-name">{char.name.split(" ")[0]}</span>
            <GhostRoleBadge characterId={char.id} />
          </div>
        );
      })}
    </div>
  );
}

/* ── Night Overlay (cinematic) ──────────────────────────── */

function NightOverlay() {
  return (
    <div className="night-overlay">
      {/* Animated stars */}
      <div className="night-stars">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="night-star"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 60}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${2 + Math.random() * 2}s`,
            }}
          />
        ))}
      </div>

      {/* Moon */}
      <div className="night-moon">
        <Moon size={48} strokeWidth={1.5} />
      </div>

      {/* Text */}
      <div className="night-text">
        <p className="night-title animate-fade-in-up">
          Night falls...
        </p>
        <p className="night-subtitle animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
          The hidden forces move in darkness
        </p>
      </div>
    </div>
  );
}

/* ── Main GameBoard ─────────────────────────────────────── */

export default function GameBoard() {
  const { t } = useI18n();
  const game = useGameState();
  const roundtable = useRoundtable();

  const voice = useVoice({
    onTranscript: (text) => {
      game.sendMessage(text);
    },
  });

  useEffect(() => {
    roundtable.setSpeakingAgent(voice.speakingAgentId);
  }, [voice.speakingAgentId]);

  // Build 3D agent configs from actual game characters (player + AI characters)
  const sceneAgents = useMemo(() => {
    if (game.session?.characters?.length) {
      return createAgent3DConfigs(game.session.characters);
    }
    return AGENTS_3D; // fallback
  }, [game.session?.characters]);

  const [inputText, setInputText] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  const visibleMessages = game.chatMessages.slice(-60);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [visibleMessages.length]);

  const handleSend = () => {
    const text = inputText.trim();
    if (!text || game.isChatStreaming) return;
    game.sendMessage(text);
    setInputText("");
  };

  useEffect(() => {
    const thinkingIds = game.chatMessages
      .filter((m) => m.isThinking && m.characterId)
      .map((m) => m.characterId!);
    roundtable.setThinkingAgents(thinkingIds);
  }, [game.chatMessages]);

  const displayInput =
    voice.isListening && voice.partialTranscript
      ? voice.partialTranscript
      : inputText;

  const isVoting = game.phase === "voting";
  const isNight = game.phase === "night";
  const showInput = game.phase === "discussion" && !game.isGhostMode;
  const hasNightAction = isNight && game.nightActionRequired !== null;

  // Get targeted character name for input indicator
  const targetChar = game.chatTarget && game.session
    ? game.session.characters.find((c) => c.id === game.chatTarget)
    : null;

  return (
    <div className="scene-container">
      {/* 3D Scene background */}
      <RoundtableScene
        speakingAgentId={roundtable.speakingAgentId}
        thinkingAgentIds={roundtable.thinkingAgentIds}
        cameraView={roundtable.cameraView}
        autoFocusEnabled={roundtable.autoFocusEnabled}
        agents={sceneAgents}
      />

      {/* Overlay UI */}
      <div className="scene-overlay">
        {/* ── Top Bar ──────────────────────────────────────── */}
        <div className="game-top-bar">
          <PhaseIndicator phase={game.phase} round={game.round} />
          <TensionBar tension={game.tension} />
        </div>

        {/* ── Left: Character Roster ──────────────────────── */}
        <CharacterRoster />

        {/* ── Right: Chat Panel ───────────────────────────── */}
        <div className="chat-panel">
          <div className="chat-panel-header">
            <MessageSquare size={12} />
            <span>
              {isVoting
                ? t("game.board.voting")
                : isNight
                  ? "Night"
                  : t("game.board.discussion")}
            </span>
            {game.isChatStreaming && (
              <Loader2
                size={11}
                className="animate-spin-custom"
                style={{ color: "var(--accent)" }}
              />
            )}
            <span className="chat-panel-count">
              {game.chatMessages.length}
            </span>
          </div>

          <div className="chat-panel-messages">
            {visibleMessages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}
            <div ref={chatEndRef} />
          </div>
        </div>

        {/* ── Player Role Card (floating, always visible during game) ── */}
        {game.playerRole && <PlayerRoleCard />}

        {/* ── Ghost Mode Overlay ──────────────────────────── */}
        {game.isGhostMode && <GhostOverlay />}

        {/* ── Center: Vote Overlay ────────────────────────── */}
        {isVoting && !game.isGhostMode && (
          <div className="vote-overlay">
            <VotePanel />
          </div>
        )}

        {/* ── Night: Action Panel or Cinematic Overlay ───── */}
        {isNight && hasNightAction && !game.isGhostMode && (
          <div className="vote-overlay">
            <NightActionPanel />
          </div>
        )}
        {isNight && !hasNightAction && <NightOverlay />}

        {/* ── Investigation Result Modal ──────────────────── */}
        {game.investigationResult && (
          <div className="investigation-reveal-overlay" onClick={game.dismissInvestigation}>
            <div
              className="investigation-reveal glass-card animate-fade-in-up"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="investigation-reveal-header">
                <span className="investigation-reveal-label">Investigation Result</span>
              </div>
              <p className="investigation-reveal-name">{game.investigationResult.name}</p>
              <p className="investigation-reveal-faction">
                is aligned with the{" "}
                <strong
                  style={{
                    color: game.investigationResult.faction.toLowerCase().includes("evil") ||
                      game.investigationResult.faction.toLowerCase().includes("werewolf")
                      ? "#ef4444"
                      : "#22c55e",
                  }}
                >
                  {game.investigationResult.faction}
                </strong>
              </p>
              <button
                className="demo-btn"
                onClick={game.dismissInvestigation}
                style={{ marginTop: "16px", width: "100%" }}
              >
                Understood
              </button>
            </div>
          </div>
        )}

        {/* ── Bottom: Input Bar ───────────────────────────── */}
        {showInput && (
          <div className="scene-input-bar">
            {/* Player identity label */}
            {game.playerRole && (
              <div className="input-player-label">
                <span className="input-player-you">YOU</span>
                <span className="input-player-dot" style={{
                  backgroundColor: game.playerRole.allies.length > 0 ? "#ef4444" : "#3b82f6"
                }} />
                <span className="input-player-role" style={{
                  color: game.playerRole.allies.length > 0 ? "#ef4444" : "#3b82f6"
                }}>
                  {game.playerRole.hidden_role}
                </span>
              </div>
            )}
            {/* Target indicator */}
            {targetChar && (
              <div className="input-target-indicator animate-fade-in-up">
                <span style={{ color: seedToColor(targetChar.avatar_seed || targetChar.id) }}>
                  @{targetChar.name}
                </span>
                <button
                  className="input-target-clear"
                  onClick={() => game.setChatTarget(null)}
                >
                  <X size={10} />
                </button>
              </div>
            )}
            <div className="scene-input-row">
              <input
                type="text"
                className="scene-input"
                placeholder={
                  voice.isListening
                    ? "Listening..."
                    : game.isChatStreaming
                      ? t("game.board.thinking")
                      : targetChar
                        ? `Message ${targetChar.name}...`
                        : t("game.board.inputPlaceholder")
                }
                value={displayInput}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                disabled={game.isChatStreaming || voice.isListening}
              />
              <button
                onClick={() =>
                  voice.isListening
                    ? voice.stopListening()
                    : voice.startListening()
                }
                className={`scene-mic-btn ${voice.isListening ? "scene-mic-btn-active" : ""}`}
                title={
                  voice.isListening ? "Stop listening" : "Start voice input"
                }
                disabled={game.isChatStreaming}
              >
                {voice.isListening ? <MicOff size={14} /> : <Mic size={14} />}
              </button>
              <button
                onClick={handleSend}
                className="scene-send-btn"
                title={t("chat.send")}
                disabled={game.isChatStreaming || !inputText.trim()}
              >
                <Send size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Error toast */}
        {game.error && (
          <div className="voice-toast voice-toast-error">{game.error}</div>
        )}
      </div>

      {/* Character reveal overlay */}
      {game.revealedCharacter && (
        <CharacterReveal
          character={game.revealedCharacter}
          onDismiss={game.dismissReveal}
        />
      )}
    </div>
  );
}

/* ── Chat Message ───────────────────────────────────────── */

function ChatMessage({ message }: { message: GameChatMessage }) {
  const { playerRole } = useGameState();
  const isUser = message.role === "user";
  const isNarrator = message.role === "narrator";
  const isSystem = message.role === "system";
  const isComplication = message.isComplication;

  let color = "#888";
  let name = "";

  if (isUser) {
    color = "#ff6b35";
    name = playerRole ? `You (${playerRole.hidden_role})` : "You";
  } else if (isNarrator) {
    color = "#FFD700";
    name = "Narrator";
  } else if (isSystem) {
    color = "#6b7280";
    name = "System";
  } else if (message.characterName) {
    color = seedToColor(message.characterId || message.characterName);
    name = message.characterName;
  }

  const msgClass = [
    "chat-panel-msg",
    isUser && "chat-panel-msg-user",
    message.isThinking && "chat-panel-msg-thinking",
    isComplication && "chat-panel-msg-complication",
    "animate-fade-in-up",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={msgClass}>
      <div className="chat-msg-header">
        {isComplication ? (
          <AlertTriangle
            size={10}
            style={{ color: "#f59e0b", flexShrink: 0 }}
          />
        ) : (
          <span
            className={`chat-msg-dot ${message.isThinking ? "animate-pulse-dot" : ""}`}
            style={{
              backgroundColor: color,
              boxShadow: `0 0 6px ${color}50`,
            }}
          />
        )}
        <span className="chat-msg-name" style={{ color: isComplication ? "#f59e0b" : color }}>
          {isComplication ? "Event" : name}
        </span>
      </div>
      {message.isThinking ? (
        <div className="thinking-dots">
          <span style={{ backgroundColor: color }} />
          <span style={{ backgroundColor: color }} />
          <span style={{ backgroundColor: color }} />
        </div>
      ) : (
        <p
          className="chat-msg-content"
          style={
            isNarrator
              ? { color: "#FFD700", fontStyle: "italic" }
              : isComplication
                ? { color: "#fbbf24", fontStyle: "italic" }
                : undefined
          }
        >
          {message.content}
        </p>
      )}
    </div>
  );
}
