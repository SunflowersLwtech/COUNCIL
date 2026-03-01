"use client";

import { useState, useRef, useEffect } from "react";
import { Crosshair, Search, ShieldPlus, Moon, Send } from "lucide-react";
import { useGameState, type GameChatMessage } from "@/hooks/useGameState";
import { seedToColor } from "@/components/CharacterCard";

const ACTION_CONFIG: Record<string, {
  title: string;
  subtitle: string;
  icon: typeof Crosshair;
  accentColor: string;
}> = {
  kill: {
    title: "Choose Your Kill Target",
    subtitle: "Select a council member to eliminate tonight",
    icon: Crosshair,
    accentColor: "#ef4444",
  },
  investigate: {
    title: "Choose Who to Investigate",
    subtitle: "Learn the true faction of one council member",
    icon: Search,
    accentColor: "#8b5cf6",
  },
  protect: {
    title: "Choose Who to Protect",
    subtitle: "Shield a council member from tonight's kill",
    icon: ShieldPlus,
    accentColor: "#22c55e",
  },
  save: {
    title: "Use Save Potion",
    subtitle: "Protect someone from tonight's kill (one-time use)",
    icon: ShieldPlus,
    accentColor: "#10b981",
  },
  poison: {
    title: "Use Poison Potion",
    subtitle: "Eliminate an additional person tonight (one-time use)",
    icon: Crosshair,
    accentColor: "#a855f7",
  },
};

export default function NightActionPanel() {
  const {
    nightActionRequired, submitNightAction, isChatStreaming,
    chatMessages, sendNightChat, session,
  } = useGameState();
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [nightInput, setNightInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const nightChatStartRef = useRef<number>(0);

  // Track the index where night chat messages start
  useEffect(() => {
    if (nightActionRequired) {
      // When night action prompt appears, record current message count
      // Subtract a few to capture ally auto-suggestions that came just before
      nightChatStartRef.current = Math.max(0, chatMessages.length - (nightActionRequired.allies?.length || 0) * 2 - 2);
    }
  }, [!!nightActionRequired]); // Only run when nightActionRequired changes from null to non-null

  // Auto-scroll chat area
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages.length]);

  if (!nightActionRequired) return null;

  const config = ACTION_CONFIG[nightActionRequired.actionType] || ACTION_CONFIG.kill;
  const Icon = config.icon;
  const allies = nightActionRequired.allies;
  const isKillAction = nightActionRequired.actionType === "kill";

  // Filter night chat messages (from the start index onward)
  const nightMessages = chatMessages.slice(nightChatStartRef.current).filter(
    (m) => m.role === "character" || m.role === "user"
  );

  const handleSendNightChat = () => {
    const trimmed = nightInput.trim();
    if (!trimmed || isChatStreaming) return;
    setNightInput("");
    sendNightChat(trimmed);
  };

  return (
    <div className="night-action-panel animate-fade-in-up">
      <div className="night-action-header">
        <div className="night-action-icon-row">
          <Moon size={16} style={{ color: "#a78bfa" }} />
          <Icon size={20} style={{ color: config.accentColor }} />
        </div>
        <h2 className="night-action-title" style={{ color: config.accentColor }}>
          {config.title}
        </h2>
        <p className="night-action-subtitle">{config.subtitle}</p>
        {allies && allies.length > 0 && (
          <div style={{
            marginTop: 8,
            padding: "6px 12px",
            borderRadius: 8,
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            fontSize: 13,
            color: "#fca5a5",
          }}>
            Your allies: {allies.map(a => a.name).join(", ")}
          </div>
        )}
      </div>

      {/* Night chat area — only for evil kill action */}
      {isKillAction && allies && allies.length > 0 && (
        <div className="night-chat-section">
          <div className="night-chat-messages">
            {nightMessages.length === 0 && (
              <div className="night-chat-empty">
                Your allies are whispering...
              </div>
            )}
            {nightMessages.map((msg, i) => (
              <div
                key={i}
                className={`night-chat-bubble ${msg.role === "user" ? "night-chat-bubble-user" : "night-chat-bubble-ally"}`}
              >
                {msg.role === "character" && msg.characterName && (
                  <span className="night-chat-sender">{msg.characterName}</span>
                )}
                <span className="night-chat-text">
                  {msg.content}
                  {msg.isStreaming && <span className="night-chat-cursor" />}
                </span>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div className="night-chat-input-row">
            <input
              type="text"
              className="night-chat-input"
              placeholder="Whisper to allies..."
              value={nightInput}
              onChange={(e) => setNightInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendNightChat();
                }
              }}
              disabled={isChatStreaming}
            />
            <button
              className="night-chat-send"
              onClick={handleSendNightChat}
              disabled={!nightInput.trim() || isChatStreaming}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}

      <div className="night-action-grid">
        {nightActionRequired.targets.map((target) => {
          const color = seedToColor(target.avatar_seed || target.id);
          const initial = target.name.charAt(0).toUpperCase();
          const isSelected = selectedTarget === target.id;

          return (
            <button
              key={target.id}
              className={`night-action-target ${isSelected ? "night-action-target-selected" : ""}`}
              onClick={() => setSelectedTarget(target.id)}
              disabled={isChatStreaming}
              style={{
                borderColor: isSelected ? config.accentColor : undefined,
                boxShadow: isSelected ? `0 0 16px ${config.accentColor}40` : undefined,
              }}
            >
              <div
                className="night-action-avatar"
                style={{
                  backgroundColor: color,
                  boxShadow: isSelected ? `0 0 12px ${color}80` : undefined,
                }}
              >
                {initial}
              </div>
              <span className="night-action-name">{target.name}</span>
              <span className="night-action-role">{target.public_role}</span>
            </button>
          );
        })}
      </div>

      <button
        className="demo-btn night-action-confirm"
        disabled={!selectedTarget || isChatStreaming}
        onClick={() => selectedTarget && submitNightAction(selectedTarget)}
        style={{
          background: selectedTarget
            ? `linear-gradient(135deg, ${config.accentColor}, ${config.accentColor}cc)`
            : undefined,
        }}
      >
        {isChatStreaming ? "Resolving..." : "Confirm Action"}
      </button>
    </div>
  );
}
