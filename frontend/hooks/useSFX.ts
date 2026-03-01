"use client";

import { useEffect, useRef, useCallback, useState } from "react";

const MUTE_KEY = "council-audio-muted";
const AUDIO_EVENT = "council-audio-mute-changed";

function getIsMuted(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(MUTE_KEY) === "true";
}

const SFX_PATHS = {
  vote: "/audio/sfx-vote.mp3",
  eliminate: "/audio/sfx-eliminate.mp3",
  phaseTransition: "/audio/sfx-phase-transition.mp3",
  gameStart: "/audio/sfx-game-start.mp3",
  gameEnd: "/audio/sfx-game-end.mp3",
  tension: "/audio/sfx-tension.mp3",
} as const;

type SFXKey = keyof typeof SFX_PATHS;

export function useSFX() {
  const poolRef = useRef<Record<string, HTMLAudioElement>>({});
  const [isMuted, setIsMuted] = useState(getIsMuted);

  // Pre-load audio files on mount
  useEffect(() => {
    const pool: Record<string, HTMLAudioElement> = {};
    for (const [key, path] of Object.entries(SFX_PATHS)) {
      const audio = new Audio(path);
      audio.preload = "auto";
      pool[key] = audio;
    }
    poolRef.current = pool;

    return () => {
      for (const audio of Object.values(pool)) {
        audio.pause();
        audio.src = "";
      }
      poolRef.current = {};
    };
  }, []);

  // Listen for mute changes from other components
  useEffect(() => {
    const handler = () => setIsMuted(getIsMuted());
    window.addEventListener(AUDIO_EVENT, handler);
    return () => window.removeEventListener(AUDIO_EVENT, handler);
  }, []);

  const play = useCallback(
    (key: SFXKey) => {
      if (getIsMuted()) return;

      const source = poolRef.current[key];
      if (!source) return;

      // Clone for overlapping playback
      const clone = source.cloneNode(true) as HTMLAudioElement;
      clone.volume = 0.5;
      clone.play().catch(() => {});
    },
    []
  );

  const playVote = useCallback(() => play("vote"), [play]);
  const playEliminate = useCallback(() => play("eliminate"), [play]);
  const playPhaseTransition = useCallback(() => play("phaseTransition"), [play]);
  const playGameStart = useCallback(() => play("gameStart"), [play]);
  const playGameEnd = useCallback(() => play("gameEnd"), [play]);
  const playTension = useCallback(() => play("tension"), [play]);

  return {
    isMuted,
    playVote,
    playEliminate,
    playPhaseTransition,
    playGameStart,
    playGameEnd,
    playTension,
  };
}
