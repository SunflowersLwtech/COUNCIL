"use client";

import { useState, useEffect, useRef } from "react";
import { useI18n } from "@/lib/i18n";
import type { GamePhase } from "@/lib/game-types";

interface PhaseIndicatorProps {
  phase: GamePhase;
  round: number;
  onTimerExpire?: () => void;
}

const GAME_PHASES: GamePhase[] = ["discussion", "voting", "reveal", "night"];

const PHASE_LABELS: Record<string, string> = {
  discussion: "Discussion",
  voting: "Voting",
  reveal: "Reveal",
  night: "Night",
};

const PHASE_SUBTITLES: Record<string, string> = {
  discussion: "Debate & accuse",
  voting: "Cast your vote",
  reveal: "Truth unveiled",
  night: "Use your ability",
};

/* ── Round-as-chapter data ─────────────────────────────────────── */

interface ChapterInfo {
  title: string;
  opener: string;
}

const CHAPTER_MAP: Record<number, ChapterInfo> = {
  1: { title: "First Impressions", opener: "The council convenes. Eight members take their seats..." },
  2: { title: "Seeds of Doubt", opener: "Suspicion grows as the council reconvenes..." },
  3: { title: "The Accusation", opener: "Powers awaken. The truth demands to be found..." },
  4: { title: "Reckoning", opener: "Few remain. Every word carries weight..." },
};

function getChapter(round: number): ChapterInfo {
  if (round <= 4) return CHAPTER_MAP[round];
  return { title: "Final Judgment", opener: "This ends now. The council must decide..." };
}

/* ── Discussion timer (escalating per round) ──────────────────── */

const DISCUSSION_MINUTES: Record<number, number> = {
  1: 3, 2: 4, 3: 5, 4: 4, 5: 3, 6: 2,
};

function getTimerMinutes(round: number): number {
  return DISCUSSION_MINUTES[round] ?? 2;
}

function DiscussionTimer({ round, phase, onTimerExpire }: { round: number; phase: GamePhase; onTimerExpire?: () => void }) {
  const totalSeconds = getTimerMinutes(round) * 60;
  const [remaining, setRemaining] = useState(totalSeconds);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasFiredRef = useRef(false);

  // Reset when round/phase changes
  useEffect(() => {
    setRemaining(getTimerMinutes(round) * 60);
    hasFiredRef.current = false;
  }, [round, phase]);

  // Tick down during discussion
  useEffect(() => {
    if (phase !== "discussion") {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }
    intervalRef.current = setInterval(() => {
      setRemaining((r) => Math.max(0, r - 1));
    }, 1000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [phase]);

  // Fire onTimerExpire when timer reaches 0 (with 1.5s grace delay)
  useEffect(() => {
    if (remaining !== 0 || hasFiredRef.current || phase !== "discussion") return;
    hasFiredRef.current = true;
    const graceTimer = setTimeout(() => {
      onTimerExpire?.();
    }, 1500);
    return () => clearTimeout(graceTimer);
  }, [remaining, phase, onTimerExpire]);

  if (phase !== "discussion") return null;

  const pct = remaining / totalSeconds;
  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;

  // Color shifts green -> yellow -> red
  let timerColor = "#22c55e";
  if (pct < 0.25) timerColor = "#ef4444";
  else if (pct < 0.5) timerColor = "#f97316";
  else if (pct < 0.75) timerColor = "#eab308";

  return (
    <div className="discussion-timer" style={{ color: timerColor }}>
      <span className="discussion-timer-value">
        {remaining === 0 ? "TIME'S UP" : `${minutes}:${seconds.toString().padStart(2, "0")}`}
      </span>
      {pct < 0.25 && remaining > 0 && (
        <span className="discussion-timer-label" style={{ color: "#ef4444" }}>
          AUTO-VOTE
        </span>
      )}
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────────── */

export default function PhaseIndicator({ phase, round, onTimerExpire }: PhaseIndicatorProps) {
  const { t } = useI18n();
  const chapter = getChapter(round);
  const currentIndex = GAME_PHASES.indexOf(phase);
  const [showOpener, setShowOpener] = useState(false);

  // Flash opener text on round change
  useEffect(() => {
    if (phase === "discussion") {
      setShowOpener(true);
      const timer = setTimeout(() => setShowOpener(false), 5000);
      return () => clearTimeout(timer);
    }
    setShowOpener(false);
  }, [round, phase]);

  return (
    <div className="phase-indicator-container">
      {/* Chapter title + round */}
      <div className="phase-chapter-header">
        <span className="phase-chapter-round" style={{ color: "var(--accent)" }}>
          {t("game.board.round", { round })}
        </span>
        <span className="phase-chapter-title">
          {chapter.title}
        </span>
      </div>

      {/* Narrative opener (fades after 5s) */}
      {showOpener && (
        <div className="phase-chapter-opener animate-fade-in-up">
          {chapter.opener}
        </div>
      )}

      {/* Phase stepper */}
      <div className="phase-stepper">
        {GAME_PHASES.map((p, i) => {
          const isActive = i === currentIndex;
          const isCompleted = i < currentIndex;

          let dotClass = "phase-dot phase-dot-pending";
          if (isCompleted) dotClass = "phase-dot phase-dot-completed";
          else if (isActive) dotClass = "phase-dot phase-dot-active";

          return (
            <div key={p} className="flex items-center gap-2">
              {i > 0 && (
                <div
                  className="phase-connector"
                  style={{
                    background:
                      i <= currentIndex
                        ? "var(--positive)"
                        : "var(--border-light)",
                  }}
                />
              )}
              <div className="phase-step-group">
                <div className="flex items-center gap-1.5">
                  <div className={dotClass} />
                  <span
                    className={`phase-label ${isActive ? "phase-label-active" : ""}`}
                    style={{
                      color: isActive
                        ? "var(--accent)"
                        : isCompleted
                          ? "var(--positive)"
                          : "var(--text-muted)",
                    }}
                  >
                    {PHASE_LABELS[p] || t(`game.phase.${p}`)}
                  </span>
                </div>
                {isActive && (
                  <span className="phase-subtitle animate-fade-in-up">
                    {PHASE_SUBTITLES[p]}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Escalating discussion timer */}
      <DiscussionTimer round={round} phase={phase} onTimerExpire={onTimerExpire} />
    </div>
  );
}
