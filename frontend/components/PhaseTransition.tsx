"use client";

import { useState, useEffect, useRef } from "react";
import type { GamePhase } from "@/lib/game-types";

interface PhaseTransitionProps {
  phase: GamePhase;
  round: number;
}

/* ── Phase transition text ────────────────────────────────────── */

const TRANSITION_TEXT: Record<string, (round: number) => string> = {
  voting: () => "The council deliberates...",
  reveal: () => "The truth is unveiled...",
  night: () => "Darkness descends...",
  discussion: (round) =>
    round <= 1 ? "The council convenes..." : "A new day dawns...",
};

/**
 * Cinematic phase transition overlay with letterboxing.
 * Shows for 3.5s on phase change, then auto-dismisses.
 */
export default function PhaseTransition({ phase, round }: PhaseTransitionProps) {
  const [visible, setVisible] = useState(false);
  const [text, setText] = useState("");
  const [fading, setFading] = useState(false);
  const prevPhase = useRef(phase);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Skip non-game phases and initial mount
    if (phase === "upload" || phase === "parsing" || phase === "lobby" || phase === "howtoplay" || phase === "intro" || phase === "ended") {
      prevPhase.current = phase;
      return;
    }

    // Only trigger on actual phase change
    if (phase === prevPhase.current) return;
    prevPhase.current = phase;

    const getTransition = TRANSITION_TEXT[phase];
    if (!getTransition) return;

    setText(getTransition(round));
    setVisible(true);
    setFading(false);

    // Start fade-out after 2.5s
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setFading(true);
      // Fully hide after fade animation (1s)
      timerRef.current = setTimeout(() => {
        setVisible(false);
        setFading(false);
      }, 1000);
    }, 2500);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [phase, round]);

  if (!visible) return null;

  return (
    <div className={`phase-transition-overlay ${fading ? "phase-transition-fading" : ""}`}>
      {/* Cinematic letterbox bars */}
      <div className="phase-transition-bar phase-transition-bar-top" />
      <div className="phase-transition-bar phase-transition-bar-bottom" />

      {/* Center text */}
      <div className="phase-transition-content">
        <p className="phase-transition-text animate-cinematic-reveal" style={{ textTransform: "uppercase" }}>{text}</p>
      </div>
    </div>
  );
}
