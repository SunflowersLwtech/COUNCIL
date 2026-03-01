"use client";

import { useState, useCallback, useEffect } from "react";
import { Volume2, VolumeX } from "lucide-react";

const MUTE_KEY = "council-audio-muted";
const AUDIO_EVENT = "council-audio-mute-changed";

function getIsMuted(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(MUTE_KEY) === "true";
}

export default function AudioControls() {
  const [isMuted, setIsMuted] = useState(false);

  // Initialize from localStorage after mount
  useEffect(() => {
    setIsMuted(getIsMuted());
  }, []);

  // Listen for changes from other components
  useEffect(() => {
    const handler = () => setIsMuted(getIsMuted());
    window.addEventListener(AUDIO_EVENT, handler);
    return () => window.removeEventListener(AUDIO_EVENT, handler);
  }, []);

  const toggle = useCallback(() => {
    const next = !getIsMuted();
    localStorage.setItem(MUTE_KEY, String(next));
    setIsMuted(next);
    window.dispatchEvent(new Event(AUDIO_EVENT));
  }, []);

  return (
    <button
      onClick={toggle}
      className="audio-toggle-btn"
      title={isMuted ? "Unmute audio" : "Mute audio"}
      aria-label={isMuted ? "Unmute audio" : "Mute audio"}
    >
      {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
    </button>
  );
}
