"use client";

import { useState, useRef, useEffect, useMemo } from "react";
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
  ChevronUp,
  ChevronDown,
  MessageCircle,
  Minus,
} from "lucide-react";
import { useGameState, type GameChatMessage } from "@/hooks/useGameState";
import { useRoundtable } from "@/hooks/useRoundtable";
import { useVoice } from "@/hooks/useVoice";
import { useI18n } from "@/lib/i18n";
import { createAgent3DConfigs, AGENTS_3D } from "@/lib/scene-constants";
import PhaseIndicator from "@/components/PhaseIndicator";
import VotePanel from "@/components/VotePanel";
import CharacterReveal from "@/components/CharacterReveal";
import PlayerRoleCard from "@/components/PlayerRoleCard";
import NightActionPanel from "@/components/NightActionPanel";
import GhostOverlay, { GhostRoleBadge } from "@/components/GhostOverlay";
import PhaseTransition from "@/components/PhaseTransition";
import { seedToColor } from "@/components/CharacterCard";

const RoundtableScene = dynamic(
  () => import("@/components/scene/RoundtableScene"),
  {
    ssr: false,
    loading: () => (
      <div style={{ width: "100%", height: "100%", background: "#060612" }} />
    ),
  }
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

/* ── Emotion Emoji Map ──────────────────────────────────── */

const EMOTION_EMOJI: Record<string, string> = {
  angry: "\uD83D\uDE20",
  fearful: "\uD83D\uDE1F",
  happy: "\uD83D\uDE0A",
  suspicious: "\uD83E\uDD28",
  curious: "\uD83E\uDD14",
  neutral: "",
};

/* ── Status tag helpers ────────────────────────────────── */

const ACCUSATION_PATTERNS = ["suspect", "suspicious", "accuse", "liar", "lying", "traitor", "blame", "guilty", "vote out", "eliminate"];

function useCharacterStatuses(
  messages: GameChatMessage[],
  characters: { id: string; name: string }[]
) {
  return useMemo(() => {
    const statuses: Record<string, { label: string; color: string }[]> = {};

    // Count accusations per character from recent messages
    const accusationCounts: Record<string, number> = {};
    const recentMsgs = messages.slice(-30);

    for (const msg of recentMsgs) {
      if (msg.role !== "character" && msg.role !== "user") continue;
      const lower = msg.content.toLowerCase();
      const hasAccusation = ACCUSATION_PATTERNS.some((p) => lower.includes(p));
      if (!hasAccusation) continue;

      for (const char of characters) {
        if (char.name && lower.includes(char.name.toLowerCase())) {
          // Don't count self-accusations
          if (msg.characterId !== char.id) {
            accusationCounts[char.id] = (accusationCounts[char.id] || 0) + 1;
          }
        }
      }
    }

    // Find the most accused character (threshold: at least 2 accusations)
    let maxAccused = "";
    let maxCount = 0;
    for (const [id, count] of Object.entries(accusationCounts)) {
      if (count > maxCount) {
        maxCount = count;
        maxAccused = id;
      }
    }

    if (maxAccused && maxCount >= 2) {
      statuses[maxAccused] = [
        ...(statuses[maxAccused] || []),
        { label: "Under Suspicion", color: "#f97316" },
      ];
    }

    return statuses;
  }, [messages, characters]);
}

/* ── Character Roster (left side) ───────────────────────── */

function CharacterRoster() {
  const game = useGameState();
  const roundtable = useRoundtable();
  const { t } = useI18n();

  // Find the latest emotion for each character from chat messages
  const characterEmotions = useMemo(() => {
    const emotions: Record<string, string> = {};
    // Scan from newest to oldest, keep first (latest) per character
    for (let i = game.chatMessages.length - 1; i >= 0; i--) {
      const msg = game.chatMessages[i];
      if (msg.characterId && msg.emotion && !emotions[msg.characterId]) {
        emotions[msg.characterId] = msg.emotion;
      }
    }
    return emotions;
  }, [game.chatMessages]);

  const charStatuses = useCharacterStatuses(
    game.chatMessages,
    game.session?.characters || []
  );

  if (!game.session) return null;

  const aliveChars = game.session.characters.filter((c) => !c.is_eliminated);
  const deadChars = game.session.characters.filter((c) => c.is_eliminated);

  return (
    <div className="character-roster">
      {aliveChars.map((char) => {
        const color = seedToColor(char.avatar_seed || char.id);
        const initial = char.name.charAt(0).toUpperCase();
        const isTarget = game.chatTarget === char.id;
        const isSpeaking = roundtable.speakingAgentId === char.id;
        const emotion = characterEmotions[char.id] || "neutral";
        const emoji = EMOTION_EMOJI[emotion] || "";
        const tags = charStatuses[char.id] || [];

        return (
          <button
            key={char.id}
            className={`roster-avatar ${isTarget ? "roster-avatar-targeted" : ""} ${isSpeaking ? "roster-avatar-speaking" : ""}`}
            style={{
              "--avatar-color": color,
              borderColor: isTarget ? "var(--accent)" : "transparent",
            } as React.CSSProperties}
            onClick={() =>
              game.setChatTarget(isTarget ? null : char.id)
            }
            title={`${char.name} - ${char.public_role}${isTarget ? " (targeted)" : ""}`}
          >
            <div className="roster-avatar-circle-wrap">
              <div
                className="roster-avatar-circle"
                style={{ backgroundColor: color }}
              >
                {initial}
              </div>
              {emoji && (
                <span className="roster-emotion-emoji">{emoji}</span>
              )}
            </div>
            <span className="roster-avatar-name">{char.name.split(" ")[0]}</span>
            {tags.map((tag, idx) => (
              <span
                key={idx}
                className="roster-status-tag"
                style={{ backgroundColor: tag.color }}
              >
                {tag.label}
              </span>
            ))}
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

  // Camera follow: driven by chat messages (works even without TTS)
  const speakingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastMsgCountRef = useRef(0);

  useEffect(() => {
    const msgs = game.chatMessages;
    if (msgs.length <= lastMsgCountRef.current) {
      lastMsgCountRef.current = msgs.length;
      return;
    }
    lastMsgCountRef.current = msgs.length;

    // Find the latest character message (non-thinking)
    const latest = msgs[msgs.length - 1];
    if (!latest || latest.isThinking) return;

    const charId = latest.characterId;
    if (!charId) return; // skip user/narrator/system

    // Set speaking agent for camera follow
    roundtable.setSpeakingAgent(charId);

    // Clear after estimated "speaking" time based on text length
    if (speakingTimerRef.current) clearTimeout(speakingTimerRef.current);
    const duration = Math.max(2000, Math.min((latest.content?.length || 0) * 40, 8000));
    speakingTimerRef.current = setTimeout(() => {
      roundtable.setSpeakingAgent(null);
    }, duration);
  }, [game.chatMessages]);

  // Also sync from TTS voice (when TTS is available, it overrides)
  useEffect(() => {
    if (voice.speakingAgentId) {
      roundtable.setSpeakingAgent(voice.speakingAgentId);
      if (speakingTimerRef.current) clearTimeout(speakingTimerRef.current);
    }
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

  // Chat drawer state: "minimized" | "expanded" | "hidden"
  const [drawerState, setDrawerState] = useState<"minimized" | "expanded" | "hidden">("minimized");

  // Track unread messages when drawer is hidden
  const [unreadCount, setUnreadCount] = useState(0);
  const prevMsgCountRef = useRef(game.chatMessages.length);

  const visibleMessages = game.chatMessages.slice(-60);

  useEffect(() => {
    if (drawerState === "expanded") {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [visibleMessages.length, drawerState]);

  // Track unread when drawer is hidden
  useEffect(() => {
    const newCount = game.chatMessages.length;
    if (drawerState === "hidden" && newCount > prevMsgCountRef.current) {
      setUnreadCount((prev) => prev + (newCount - prevMsgCountRef.current));
    }
    prevMsgCountRef.current = newCount;
  }, [game.chatMessages.length, drawerState]);

  // Clear unread when drawer opens
  useEffect(() => {
    if (drawerState !== "hidden") {
      setUnreadCount(0);
    }
  }, [drawerState]);

  // Auto-expand on new character response during discussion (if minimized)
  useEffect(() => {
    if (drawerState !== "minimized") return;
    const latest = game.chatMessages[game.chatMessages.length - 1];
    if (latest && (latest.role === "character" || latest.role === "narrator") && !latest.isThinking) {
      setDrawerState("expanded");
    }
  }, [game.chatMessages.length]);

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
        gamePhase={game.phase}
        round={game.round}
      />

      {/* Cinematic phase transition overlay */}
      <PhaseTransition phase={game.phase} round={game.round} />

      {/* Overlay UI */}
      <div className="scene-overlay">
        {/* ── Top Bar ──────────────────────────────────────── */}
        <div className="game-top-bar">
          <PhaseIndicator phase={game.phase} round={game.round} />
          <TensionBar tension={game.tension} />
        </div>

        {/* ── Left: Character Roster ──────────────────────── */}
        <CharacterRoster />

        {/* ── Player Role Card (floating, always visible during game) ── */}
        {game.playerRole && <PlayerRoleCard />}

        {/* ── Ghost Mode Overlay ──────────────────────────── */}
        {game.isGhostMode && <GhostOverlay />}

        {/* ── Night: Cinematic Overlay (no action needed) ── */}
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

        {/* ── Bottom Drawer: Vote / Night Action / Chat ── */}
        {isVoting && !game.isGhostMode ? (
          /* Vote drawer — replaces chat during voting */
          <div className="action-drawer action-drawer-open">
            <VotePanel />
          </div>
        ) : isNight && hasNightAction && !game.isGhostMode ? (
          /* Night action drawer — replaces chat during night */
          <div className="action-drawer action-drawer-open">
            <NightActionPanel />
          </div>
        ) : drawerState === "hidden" ? (
          /* Floating bubble when fully hidden */
          <button
            className="chat-bubble-btn"
            onClick={() => setDrawerState("minimized")}
          >
            <MessageCircle size={20} />
            {unreadCount > 0 && (
              <span className="chat-bubble-badge">{unreadCount}</span>
            )}
          </button>
        ) : (
          <div className={`chat-drawer ${drawerState === "expanded" ? "chat-drawer-expanded" : ""}`}>
            {/* Drawer header / handle */}
            <div
              className="chat-drawer-handle"
              onClick={() =>
                setDrawerState((s) => (s === "expanded" ? "minimized" : "expanded"))
              }
            >
              <div className="chat-drawer-handle-bar" />
              <div className="chat-drawer-handle-info">
                <MessageSquare size={11} />
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
              <div className="chat-drawer-handle-actions">
                {drawerState === "expanded" ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronUp size={14} />
                )}
                <button
                  className="chat-drawer-hide-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDrawerState("hidden");
                  }}
                  title="Hide chat"
                >
                  <Minus size={12} />
                </button>
              </div>
            </div>

            {/* Messages area (visible when expanded) */}
            {drawerState === "expanded" && (
              <div className="chat-drawer-messages">
                {visibleMessages.map((msg, i) => (
                  <ChatMessage key={i} message={msg} />
                ))}
                <div ref={chatEndRef} />
              </div>
            )}

            {/* Input area (discussion phase only, not ghost) */}
            {showInput && (
              <div className="chat-drawer-input-area">
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
                            : "Address the council..."
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
                    title={voice.isListening ? "Stop listening" : "Start voice input"}
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

  const emotionEmoji = message.emotion ? (EMOTION_EMOJI[message.emotion] || "") : "";

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
        {emotionEmoji && (
          <span className="chat-msg-emotion">{emotionEmoji}</span>
        )}
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
