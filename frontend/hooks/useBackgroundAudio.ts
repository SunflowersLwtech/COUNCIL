"use client";

import { useEffect, useRef, useCallback, useState } from "react";

const MUTE_KEY = "council-audio-muted";
const AUDIO_EVENT = "council-audio-mute-changed";

function getIsMuted(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(MUTE_KEY) === "true";
}

export function useBackgroundAudio(src = "/audio/ambient-loop.mp3") {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isMuted, setIsMuted] = useState(getIsMuted);
  const [isPlaying, setIsPlaying] = useState(false);
  const hasInteractedRef = useRef(false);

  // Create audio element once
  useEffect(() => {
    const audio = new Audio(src);
    audio.loop = true;
    audio.volume = 0.3;
    audio.preload = "auto";
    audioRef.current = audio;

    return () => {
      audio.pause();
      audio.src = "";
      audioRef.current = null;
    };
  }, [src]);

  // Start playback on first user interaction (autoplay policy)
  useEffect(() => {
    if (hasInteractedRef.current) return;

    const start = () => {
      if (hasInteractedRef.current) return;
      hasInteractedRef.current = true;

      const audio = audioRef.current;
      if (audio && !getIsMuted()) {
        audio.play().then(() => setIsPlaying(true)).catch(() => {});
      }

      document.removeEventListener("click", start);
      document.removeEventListener("keydown", start);
      document.removeEventListener("touchstart", start);
    };

    document.addEventListener("click", start, { once: false });
    document.addEventListener("keydown", start, { once: false });
    document.addEventListener("touchstart", start, { once: false });

    return () => {
      document.removeEventListener("click", start);
      document.removeEventListener("keydown", start);
      document.removeEventListener("touchstart", start);
    };
  }, []);

  // Sync mute state with audio
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isMuted) {
      audio.pause();
      setIsPlaying(false);
    } else if (hasInteractedRef.current) {
      audio.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [isMuted]);

  // Listen for mute changes from other components (via custom event)
  useEffect(() => {
    const handler = () => setIsMuted(getIsMuted());
    window.addEventListener(AUDIO_EVENT, handler);
    return () => window.removeEventListener(AUDIO_EVENT, handler);
  }, []);

  // Auto-pause when tab is hidden (Page Visibility API)
  useEffect(() => {
    const handler = () => {
      const audio = audioRef.current;
      if (!audio || isMuted) return;

      if (document.hidden) {
        audio.pause();
        setIsPlaying(false);
      } else if (hasInteractedRef.current) {
        audio.play().then(() => setIsPlaying(true)).catch(() => {});
      }
    };

    document.addEventListener("visibilitychange", handler);
    return () => document.removeEventListener("visibilitychange", handler);
  }, [isMuted]);

  const setVolume = useCallback((vol: number) => {
    const audio = audioRef.current;
    if (audio) audio.volume = Math.min(Math.max(vol, 0), 1);
  }, []);

  return { isMuted, isPlaying, setVolume };
}
