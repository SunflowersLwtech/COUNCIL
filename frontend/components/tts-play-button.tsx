"use client";

import { Volume2 } from "lucide-react";
import { useState } from "react";
import { generateTTS } from "@/lib/api";
import { agentRoleToId } from "@/lib/agent-utils";
import { playManagedAudio } from "@/lib/audio-manager";
import { useI18n } from "@/lib/i18n";

interface TTSPlayButtonProps {
  text: string;
  agentRole: string;
}

export default function TTSPlayButton({ text, agentRole }: TTSPlayButtonProps) {
  const { t } = useI18n();
  const [playing, setPlaying] = useState(false);

  const handlePlay = async () => {
    if (playing) return;
    setPlaying(true);

    try {
      const agentId = agentRoleToId(agentRole);
      const blob = await generateTTS(text, agentId);
      if (!blob) {
        setPlaying(false);
        return;
      }

      const audio = playManagedAudio(blob, () => setPlaying(false));
      await audio.play();
    } catch {
      setPlaying(false);
    }
  };

  return (
    <button
      onClick={handlePlay}
      disabled={playing}
      title={playing ? t("tts.playing") : t("tts.play")}
      className="inline-flex items-center justify-center w-5 h-5 rounded transition-colors disabled:opacity-50"
      style={{ color: playing ? "var(--positive)" : "var(--text-muted)" }}
    >
      <Volume2 size={12} />
    </button>
  );
}
