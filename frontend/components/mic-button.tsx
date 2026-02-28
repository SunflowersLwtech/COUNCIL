"use client";

import { Mic, Square, Volume2, Loader2 } from "lucide-react";
import type { VoiceStatus } from "@/hooks/useVoice";
import { useI18n } from "@/lib/i18n";

interface MicButtonProps {
  status: VoiceStatus;
  partialTranscript: string;
  onStart: () => void;
  onStop: () => void;
}

export default function MicButton({
  status,
  partialTranscript,
  onStart,
  onStop,
}: MicButtonProps) {
  const { t } = useI18n();

  const handleClick = () => {
    if (status === "idle") onStart();
    else if (status === "listening") onStop();
  };

  const disabled = status === "connecting" || status === "processing";

  let icon: React.ReactNode;
  let color: string;
  let title: string;

  switch (status) {
    case "connecting":
      icon = <Loader2 size={18} className="animate-spin-custom" />;
      color = "var(--accent)";
      title = t("voice.connecting");
      break;
    case "listening":
      icon = <Square size={14} fill="currentColor" />;
      color = "var(--critical)";
      title = t("voice.stopRecording");
      break;
    case "processing":
      icon = <Mic size={18} />;
      color = "var(--text-muted)";
      title = t("voice.processing");
      break;
    case "speaking":
      icon = <Volume2 size={18} />;
      color = "var(--positive)";
      title = t("voice.agentSpeaking");
      break;
    default:
      icon = <Mic size={18} />;
      color = "var(--accent)";
      title = t("voice.startRecording");
  }

  return (
    <div className="flex items-center gap-2">
      {status === "listening" && partialTranscript && (
        <span
          className="text-xs max-w-[200px] truncate"
          style={{ color: "var(--text-secondary)" }}
        >
          {partialTranscript}
        </span>
      )}
      <button
        onClick={handleClick}
        disabled={disabled}
        title={title}
        className={`p-2.5 rounded-lg transition-colors disabled:opacity-50 ${
          status === "listening" ? "recording-pulse" : ""
        }`}
        style={{ color, background: "var(--bg-secondary)", border: "1px solid var(--border)" }}
      >
        {icon}
      </button>
    </div>
  );
}
