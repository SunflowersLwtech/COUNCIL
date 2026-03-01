"use client";

import { useEffect, useRef, useCallback, useState } from "react";

const MUTE_KEY = "council-audio-muted";
const AUDIO_EVENT = "council-audio-mute-changed";
export const DUCK_EVENT = "council-audio-duck";
export const UNDUCK_EVENT = "council-audio-unduck";

/** Phase → target volume mapping */
const PHASE_VOLUMES: Record<string, number> = {
  night: 0.15,
  discussion: 0.25,
  voting: 0.35,
  reveal: 0.20,
};
const DEFAULT_VOLUME = 0.25;
const DUCK_VOLUME = 0.08;
const FADE_MS = 500;
const FADE_STEP_MS = 20;

function getIsMuted(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(MUTE_KEY) === "true";
}

export function useBackgroundAudio(
  phase?: string,
  src = "/audio/vibe.mp3",
) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isMuted, setIsMuted] = useState(getIsMuted);
  const [isPlaying, setIsPlaying] = useState(false);
  const hasInteractedRef = useRef(false);

  // Current target volume (before ducking)
  const targetVolRef = useRef(DEFAULT_VOLUME);
  const isDuckedRef = useRef(false);
  const fadeTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Create audio element once
  useEffect(() => {
    const audio = new Audio(src);
    audio.loop = true;
    audio.volume = PHASE_VOLUMES[phase || ""] ?? DEFAULT_VOLUME;
    audio.preload = "auto";
    audioRef.current = audio;

    return () => {
      audio.pause();
      audio.src = "";
      audioRef.current = null;
    };
  }, [src]);

  // Smooth fade helper
  const fadeTo = useCallback((target: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    if (fadeTimerRef.current) clearInterval(fadeTimerRef.current);

    const steps = Math.max(1, Math.round(FADE_MS / FADE_STEP_MS));
    const diff = target - audio.volume;
    const stepSize = diff / steps;
    let step = 0;

    fadeTimerRef.current = setInterval(() => {
      step++;
      if (step >= steps) {
        audio.volume = Math.min(Math.max(target, 0), 1);
        if (fadeTimerRef.current) clearInterval(fadeTimerRef.current);
        fadeTimerRef.current = null;
      } else {
        audio.volume = Math.min(Math.max(audio.volume + stepSize, 0), 1);
      }
    }, FADE_STEP_MS);
  }, []);

  // Phase-based volume crossfade
  useEffect(() => {
    const vol = PHASE_VOLUMES[phase || ""] ?? DEFAULT_VOLUME;
    targetVolRef.current = vol;
    // Only fade to phase volume if not currently ducked
    if (!isDuckedRef.current) {
      fadeTo(vol);
    }
  }, [phase, fadeTo]);

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

  /** Duck volume down for TTS playback */
  const duck = useCallback(() => {
    isDuckedRef.current = true;
    fadeTo(DUCK_VOLUME);
  }, [fadeTo]);

  /** Restore volume after TTS playback */
  const unduck = useCallback(() => {
    isDuckedRef.current = false;
    fadeTo(targetVolRef.current);
  }, [fadeTo]);

  // Listen for global duck/unduck events (from useVoice in any component)
  useEffect(() => {
    const handleDuck = () => duck();
    const handleUnduck = () => unduck();
    window.addEventListener(DUCK_EVENT, handleDuck);
    window.addEventListener(UNDUCK_EVENT, handleUnduck);
    return () => {
      window.removeEventListener(DUCK_EVENT, handleDuck);
      window.removeEventListener(UNDUCK_EVENT, handleUnduck);
    };
  }, [duck, unduck]);

  return { isMuted, isPlaying, setVolume, duck, unduck };
}
