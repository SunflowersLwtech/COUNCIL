"use client";

import { useI18n } from "@/lib/i18n";
import type { GamePhase } from "@/lib/game-types";

interface PhaseIndicatorProps {
  phase: GamePhase;
  round: number;
}

const GAME_PHASES: GamePhase[] = ["discussion", "voting", "reveal", "night"];

export default function PhaseIndicator({ phase, round }: PhaseIndicatorProps) {
  const { t } = useI18n();

  const currentIndex = GAME_PHASES.indexOf(phase);

  return (
    <div className="flex items-center gap-3">
      <span
        className="text-xs font-semibold"
        style={{ color: "var(--accent)" }}
      >
        {t("game.board.round", { round })}
      </span>

      <div className="phase-stepper">
        {GAME_PHASES.map((p, i) => {
          let dotClass = "phase-dot phase-dot-pending";
          if (i < currentIndex) dotClass = "phase-dot phase-dot-completed";
          else if (i === currentIndex) dotClass = "phase-dot phase-dot-active";

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
              <div className="flex items-center gap-1.5">
                <div className={dotClass} />
                <span
                  className="text-[10px] font-medium"
                  style={{
                    color:
                      i === currentIndex
                        ? "var(--accent)"
                        : i < currentIndex
                          ? "var(--positive)"
                          : "var(--text-muted)",
                  }}
                >
                  {t(`game.phase.${p}`)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
