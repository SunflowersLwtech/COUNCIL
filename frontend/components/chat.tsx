"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import AgentAvatar from "./agent-avatar";
import MicButton from "./mic-button";
import TTSPlayButton from "./tts-play-button";
import { sendChatMulti } from "@/lib/api";
import { useVoice } from "@/hooks/useVoice";
import { useI18n } from "@/lib/i18n";

export interface ChatMessage {
  role: "user" | "assistant";
  agentRole?: string;
  content: string;
}

interface ChatProps {
  isAnalysisComplete: boolean;
  isLoading: boolean;
  initialMessages?: ChatMessage[];
}

const CyberDecodeText = ({ text }: { text: string }) => {
  const [displayText, setDisplayText] = useState("");
  const [isDecoding, setIsDecoding] = useState(true);

  useEffect(() => {
    let iter = 0;
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#%&*";
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split("")
          .map((char, index) => {
            if (index < iter || char === " " || char === "\n") return char;
            return chars[Math.floor(Math.random() * chars.length)];
          })
          .join("")
      );
      // Decrease divisor to slow down, increase to speed up 
      iter += Math.max(1, text.length / 15);
      if (iter >= text.length) {
        setIsDecoding(false);
        setDisplayText(text);
        clearInterval(interval);
      }
    }, 40);
    return () => clearInterval(interval);
  }, [text]);

  return isDecoding ? (
    <span className="font-mono text-sm opacity-80" style={{ color: "var(--accent)" }}>{displayText}</span>
  ) : (
    <ReactMarkdown>{text}</ReactMarkdown>
  );
};

export default function Chat({
  isAnalysisComplete,
  isLoading,
  initialMessages = [],
}: ChatProps) {
  const { t } = useI18n();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Refs to break the circular dependency between handleSendWithText and voice
  const queueAgentResponsesRef = useRef<
    (items: Array<{ text: string; agentRole: string }>) => void
  >(() => { });

  // ── Core send logic (shared by keyboard + voice) ──────────────────

  const handleSendWithText = useCallback(
    async (text: string) => {
      const question = text.trim();
      if (!question || sending) return;

      setMessages((prev) => [...prev, { role: "user", content: question }]);
      setSending(true);

      try {
        const res = await sendChatMulti(question);

        // Add each agent response to messages
        const newMessages: ChatMessage[] = res.responses.map((r) => ({
          role: "assistant" as const,
          agentRole: r.agent_role,
          content: r.response,
        }));
        setMessages((prev) => [...prev, ...newMessages]);

        // Queue all responses for TTS playback
        const ttsItems = res.responses.map((r) => ({
          text: r.response,
          agentRole: r.agent_role,
        }));
        queueAgentResponsesRef.current(ttsItems);
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            agentRole: "System",
            content: t("chat.error", {
              message: err instanceof Error ? err.message : t("chat.unknownError"),
            }),
          },
        ]);
      } finally {
        setSending(false);
      }
    },
    [sending, t]
  );

  // ── Voice hook ────────────────────────────────────────────────────

  const voice = useVoice({
    onTranscript: (text) => handleSendWithText(text),
  });

  // Sync latest ref on every render (breaks closure dependency)
  queueAgentResponsesRef.current = voice.queueAgentResponses;

  // ── Scroll & initial messages ─────────────────────────────────────

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (initialMessages.length > 0) {
      setMessages((prev) => {
        const newMessages = initialMessages.filter(
          (m) => !prev.some((p) => p.content === m.content)
        );
        return newMessages.length > 0 ? [...prev, ...newMessages] : prev;
      });
    }
  }, [initialMessages]);

  // ── Keyboard send ─────────────────────────────────────────────────

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    const question = input.trim();
    setInput("");
    await handleSendWithText(question);
  };

  const isRecording = voice.status === "listening";

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full gap-6 animate-fade-in">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2 welcome-gradient-text">
                {t("chat.welcome")}
              </h2>
              <p style={{ color: "var(--text-secondary)" }}>
                {t("chat.welcomeDesc")}
              </p>
            </div>
          </div>
        )}

        {isLoading && messages.length === 0 && (
          <div
            className="flex items-center gap-3 p-4 rounded-lg animate-fade-in"
            style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
          >
            <div
              className="w-5 h-5 rounded-full border-2 animate-spin-custom"
              style={{
                borderColor: "var(--accent)",
                borderTopColor: "transparent",
              }}
            />
            <span style={{ color: "var(--text-secondary)" }}>
              {t("chat.analyzing")}
            </span>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 animate-fade-in-up ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            {msg.role === "assistant" && (
              <AgentAvatar role={msg.agentRole || "Orchestrator"} />
            )}
            <div
              className={`max-w-[80%] p-3 text-sm ${msg.role === "user" ? "chat-bubble-user ml-auto" : "chat-bubble-agent"
                }`}
            >
              {msg.role === "assistant" && msg.agentRole && (
                <div
                  className="text-xs font-bold mb-1 flex items-center gap-1"
                  style={{ color: "var(--accent)" }}
                >
                  {t(`agents.${msg.agentRole}`)}
                  <TTSPlayButton text={msg.content} agentRole={msg.agentRole} />
                </div>
              )}
              {msg.role === "assistant" ? (
                <div className="chat-markdown">
                  <CyberDecodeText text={msg.content} />
                </div>
              ) : (
                <span className="whitespace-pre-wrap">{msg.content}</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4" style={{ borderTop: "1px solid var(--border)" }}>
        <div className="flex gap-2">
          <input
            type="text"
            value={isRecording ? voice.partialTranscript || t("chat.listening") : input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={
              isAnalysisComplete
                ? t("chat.inputPlaceholder")
                : t("chat.inputDisabled")
            }
            disabled={!isAnalysisComplete || sending || isRecording}
            readOnly={isRecording}
            className="flex-1 px-4 py-2.5 rounded-lg text-sm outline-none disabled:opacity-50"
            style={{
              background: "var(--bg-secondary)",
              border: `1px solid ${isRecording ? "var(--critical)" : "var(--border)"}`,
              color: "var(--text-primary)",
            }}
          />
          <MicButton
            status={voice.status}
            partialTranscript={voice.partialTranscript}
            onStart={voice.startListening}
            onStop={voice.stopListening}
          />
          <button
            onClick={handleSend}
            disabled={!isAnalysisComplete || sending || !input.trim() || isRecording}
            className="px-4 py-2.5 rounded-lg font-medium text-sm text-white disabled:opacity-50 transition-colors"
            style={{ background: "var(--accent)" }}
          >
            {sending ? "..." : t("chat.send")}
          </button>
        </div>
      </div>
    </div>
  );
}
