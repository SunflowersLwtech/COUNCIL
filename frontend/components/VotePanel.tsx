"use client";

import { Vote, CheckCircle, AlertTriangle, Scale } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { useI18n } from "@/lib/i18n";
import { seedToColor } from "@/components/CharacterCard";

export default function VotePanel() {
  const { t } = useI18n();
  const {
    session,
    selectedVote,
    setSelectedVote,
    hasVoted,
    castVote,
    voteResults,
  } = useGameState();

  if (!session) return null;

  const aliveCharacters = session.characters.filter((c) => !c.is_eliminated);

  // Vote results view
  if (voteResults) {
    const isTie = voteResults.is_tie;

    return (
      <div className="vote-center-card glass-card animate-fade-in">
        <div className="vote-center-header">
          {isTie ? (
            <>
              <Scale size={20} style={{ color: "#f59e0b" }} />
              <h2 className="vote-center-title" style={{ color: "#f59e0b" }}>
                {t("game.vote.noElimination")}
              </h2>
            </>
          ) : (
            <>
              <CheckCircle size={20} style={{ color: "var(--critical)" }} />
              <h2 className="vote-center-title">
                {voteResults.eliminated_name
                  ? t("game.vote.eliminated", { name: voteResults.eliminated_name })
                  : t("game.vote.noElimination")}
              </h2>
            </>
          )}
        </div>

        {isTie && (
          <div className="vote-tie-banner">
            <AlertTriangle size={14} />
            <span>The council could not reach consensus. No one is eliminated.</span>
          </div>
        )}

        {/* Tally bars */}
        <div className="vote-tally-list">
          {Object.entries(voteResults.tally)
            .sort(([, a], [, b]) => b - a)
            .map(([name, count]) => {
              const maxVotes = Math.max(...Object.values(voteResults.tally));
              const pct = maxVotes > 0 ? (count / maxVotes) * 100 : 0;
              const isEliminated = name === voteResults.eliminated_name;

              return (
                <div
                  key={name}
                  className={`vote-tally-row animate-fade-in-up ${isEliminated ? "vote-tally-row-eliminated" : ""}`}
                >
                  <div className="vote-tally-info">
                    <span className="vote-tally-name">{name}</span>
                    <span className="vote-tally-count">{count}</span>
                  </div>
                  <div className="vote-tally-bar-track">
                    <div
                      className="vote-tally-bar-fill"
                      style={{
                        width: `${pct}%`,
                        background: isEliminated
                          ? "linear-gradient(90deg, var(--critical), #dc2626)"
                          : "linear-gradient(90deg, var(--accent), var(--accent-hover))",
                      }}
                    />
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    );
  }

  // Voting view
  return (
    <div className="vote-center-card glass-card animate-fade-in-up">
      <div className="vote-center-header">
        <Vote size={20} style={{ color: "var(--accent)" }} />
        <h2 className="vote-center-title">{t("game.vote.title")}</h2>
        <p className="vote-center-subtitle">Choose who to eliminate from the council</p>
      </div>

      <div className="vote-center-grid">
        {aliveCharacters.map((char) => {
          const color = seedToColor(char.avatar_seed || char.id);
          const initial = char.name.charAt(0).toUpperCase();
          const isSelected = selectedVote === char.id;

          return (
            <button
              key={char.id}
              className={`vote-char-card ${isSelected ? "vote-char-card-selected" : ""}`}
              onClick={() => !hasVoted && setSelectedVote(char.id)}
              disabled={hasVoted}
              style={{
                "--char-color": color,
                borderColor: isSelected ? color : undefined,
              } as React.CSSProperties}
            >
              <div
                className="vote-char-avatar"
                style={{
                  backgroundColor: color,
                  boxShadow: isSelected ? `0 0 16px ${color}80` : undefined,
                }}
              >
                {initial}
              </div>
              <span className="vote-char-name">{char.name}</span>
              <span className="vote-char-role">{char.public_role}</span>
            </button>
          );
        })}
      </div>

      <button
        className="demo-btn vote-cast-btn"
        disabled={!selectedVote || hasVoted}
        onClick={() => selectedVote && castVote(selectedVote)}
      >
        {hasVoted ? t("game.vote.waiting") : t("game.vote.confirm")}
      </button>
    </div>
  );
}
