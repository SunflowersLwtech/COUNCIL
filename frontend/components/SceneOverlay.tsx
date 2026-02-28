"use client";

import { useState, useRef, useEffect } from "react";
import {
  Eye,
  User,
  Rotate3d,
  Focus,
  X,
  Send,
  Mic,
  MicOff,
  MessageSquare,
  Loader2,
} from "lucide-react";
import { useRoundtable, type CameraView } from "@/hooks/useRoundtable";
import { useI18n } from "@/lib/i18n";

const AGENT_COLORS: Record<string, string> = {
  architecture: "#4ECDC4",
  "code-quality": "#45B7D1",
  documentation: "#96CEB4",
  security: "#FF6B6B",
};

const AGENT_NAME_KEYS: Record<string, string> = {
  architecture: "agents.Architecture Analyst",
  "code-quality": "agents.Code Quality Analyst",
  documentation: "agents.Documentation Analyst",
  security: "agents.Security Analyst",
};

const AGENT_ID_FROM_ROLE: Record<string, string> = {
  "Architecture Analyst": "architecture",
  "Code Quality Analyst": "code-quality",
  "Documentation Analyst": "documentation",
  "Security Analyst": "security",
};

interface SceneOverlayProps {
  messages: Array<{ role: string; content: string; agentRole?: string }>;
  onSend: (text: string) => void;
  isListening: boolean;
  onStartListening: () => void;
  onStopListening: () => void;
  transcript: string;
  voiceStatus: string;
  isStreaming?: boolean;
}

export default function SceneOverlay({
  messages,
  onSend,
  isListening,
  onStartListening,
  onStopListening,
  transcript,
  isStreaming,
}: SceneOverlayProps) {
  const { t } = useI18n();
  const {
    cameraView,
    setCameraView,
    autoFocusEnabled,
    toggleAutoFocus,
    toggleScene,
    speakingAgentId,
    thinkingAgentIds,
  } = useRoundtable();

  const [inputText, setInputText] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  const visibleMessages = messages.slice(-40);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [visibleMessages.length]);

  const handleSend = () => {
    const text = inputText.trim();
    if (!text) return;
    onSend(text);
    setInputText("");
  };

  const cameraButtons: {
    view: CameraView;
    icon: React.ReactNode;
    label: string;
  }[] = [
    {
      view: "birds-eye",
      icon: <Eye size={14} />,
      label: t("scene.overview"),
    },
    {
      view: "first-person",
      icon: <User size={14} />,
      label: t("scene.focus"),
    },
    {
      view: "orbit",
      icon: <Rotate3d size={14} />,
      label: t("scene.orbit"),
    },
  ];

  return (
    <div className="scene-overlay">
      {/* Top-left: Camera controls */}
      <div className="camera-controls">
        {cameraButtons.map(({ view, icon, label }) => (
          <button
            key={view}
            onClick={() => setCameraView(view)}
            className={`camera-btn ${cameraView === view ? "camera-btn-active" : ""}`}
            title={label}
          >
            {icon}
            <span className="text-[10px]">{label}</span>
          </button>
        ))}
      </div>

      {/* Top-right: Auto-focus toggle + Exit 3D */}
      <div className="top-right-controls">
        <button
          onClick={toggleAutoFocus}
          className={`glass-btn ${autoFocusEnabled ? "glass-btn-active" : ""}`}
          title={t("scene.autoFocus")}
        >
          <Focus size={14} />
          <span className="text-[10px]">
            {autoFocusEnabled ? t("scene.on") : t("scene.off")}
          </span>
        </button>
        <button
          onClick={toggleScene}
          className="glass-btn glass-btn-exit"
          title={t("scene.exitScene")}
        >
          <X size={14} />
        </button>
      </div>

      {/* Right side: Chat panel */}
      <div className="chat-panel">
        <div className="chat-panel-header">
          <MessageSquare size={12} />
          <span>{t("scene.chatTitle")}</span>
          {isStreaming && (
            <Loader2 size={11} className="animate-spin-custom" style={{ color: "var(--accent)" }} />
          )}
          <span className="chat-panel-count">{messages.length}</span>
        </div>
        <div className="chat-panel-messages">
          {visibleMessages.map((msg, i) => {
            const agentId = msg.agentRole
              ? AGENT_ID_FROM_ROLE[msg.agentRole]
              : null;
            const color = agentId ? AGENT_COLORS[agentId] : undefined;
            const nameKey = agentId ? AGENT_NAME_KEYS[agentId] : null;
            const isUser = msg.role === "user";
            const name = nameKey
              ? t(nameKey)
              : isUser
                ? t("scene.you")
                : msg.agentRole || t("scene.agent");

            return (
              <div
                key={i}
                className={`chat-panel-msg ${isUser ? "chat-panel-msg-user" : ""} animate-fade-in-up`}
              >
                <div className="chat-msg-header">
                  <span
                    className="chat-msg-dot"
                    style={{
                      backgroundColor: color || (isUser ? "#ff6b35" : "#888"),
                      boxShadow: `0 0 6px ${color || (isUser ? "#ff6b35" : "#888")}50`,
                    }}
                  />
                  <span
                    className="chat-msg-name"
                    style={{ color: color || (isUser ? "#ff6b35" : "#888") }}
                  >
                    {name}
                  </span>
                </div>
                <p className="chat-msg-content">
                  {msg.content}
                </p>
              </div>
            );
          })}

          {/* Thinking indicators for agents currently processing */}
          {thinkingAgentIds.map((agentId) => {
            const nameKey = AGENT_NAME_KEYS[agentId];
            if (!nameKey) return null;
            const color = AGENT_COLORS[agentId] || "#888";
            return (
              <div key={`thinking-${agentId}`} className="chat-panel-msg chat-panel-msg-thinking animate-fade-in">
                <div className="chat-msg-header">
                  <span
                    className="chat-msg-dot animate-pulse-dot"
                    style={{
                      backgroundColor: color,
                      boxShadow: `0 0 6px ${color}50`,
                    }}
                  />
                  <span className="chat-msg-name" style={{ color }}>
                    {t(nameKey)}
                  </span>
                </div>
                <div className="thinking-dots">
                  <span style={{ backgroundColor: color }} />
                  <span style={{ backgroundColor: color }} />
                  <span style={{ backgroundColor: color }} />
                </div>
              </div>
            );
          })}

          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Bottom-left: Speaker indicator */}
      {speakingAgentId && AGENT_NAME_KEYS[speakingAgentId] && (
        <div className="speaker-indicator">
          <span
            className="speaker-dot"
            style={{
              backgroundColor: AGENT_COLORS[speakingAgentId] || "#fff",
              boxShadow: `0 0 8px ${AGENT_COLORS[speakingAgentId] || "#fff"}`,
            }}
          />
          <span className="text-sm text-white font-medium">
            {t(AGENT_NAME_KEYS[speakingAgentId])}
          </span>
        </div>
      )}

      {/* Bottom center: Input bar */}
      <div className="scene-input-bar">
        {transcript && (
          <div className="scene-transcript">
            <span className="text-xs text-white/60">{transcript}</span>
          </div>
        )}
        <div className="scene-input-row">
          <input
            type="text"
            className="scene-input"
            placeholder={
              isStreaming
                ? t("scene.agentsThinking") || "Agents are responding..."
                : t("scene.inputPlaceholder")
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={isStreaming}
          />
          <button
            onClick={handleSend}
            className="scene-send-btn"
            title={t("chat.send")}
            disabled={isStreaming}
          >
            <Send size={14} />
          </button>
          <button
            onClick={isListening ? onStopListening : onStartListening}
            className={`scene-mic-btn ${isListening ? "scene-mic-btn-active" : ""}`}
            title={
              isListening
                ? t("voice.stopRecording")
                : t("voice.startRecording")
            }
          >
            {isListening ? <MicOff size={14} /> : <Mic size={14} />}
          </button>
        </div>
      </div>
    </div>
  );
}
