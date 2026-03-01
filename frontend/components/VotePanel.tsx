"use client";

import { useState } from "react";
import { Vote, CheckCircle, AlertTriangle, Scale, ArrowRight } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { useSFX } from "@/hooks/useSFX";
import { useI18n } from "@/lib/i18n";
import { seedToColor } from "@/components/CharacterCard";

/* ── Running tally from staggered votes ────────────────────────── */

function buildRunningTally(votes: Array<{ voterName: string; targetName: string }>) {
  const tally: Record<string, number> = {};
  for (const v of votes) {
    tally[v.targetName] = (tally[v.targetName] || 0) + 1;
  }
  return tally;
}

/* ── Staggered vote reveal (shown while votes stream in) ──────── */

function StaggeredVoteReveal({
  votes,
  totalVoters,
}: {
  votes: Array<{ voterName: string; targetName: string; timestamp: number }>;
  totalVoters: number;
}) {
  const tally = buildRunningTally(votes);
  const maxCount = Math.max(...Object.values(tally), 1);

  return (
    <div className="vote-center-card glass-card animate-fade-in">
      <div className="vote-center-header">
        <Vote size={20} style={{ color: "var(--accent)" }} />
        <h2 className="vote-center-title">Votes Being Cast...</h2>
        <p className="vote-center-subtitle">
          {votes.length} of {totalVoters} council members have voted
        </p>
      </div>

      {/* Individual vote entries with stagger */}
      <div className="staggered-vote-list">
        {votes.map((v, i) => (
          <div
            key={`${v.voterName}-${i}`}
            className="staggered-vote-entry animate-vote-slide-in"
            style={{ animationDelay: `${i * 0.3}s` }}
          >
            <span className="staggered-vote-voter">{v.voterName}</span>
            <ArrowRight size={14} className="staggered-vote-arrow" />
            <span className="staggered-vote-target">{v.targetName}</span>
          </div>
        ))}
      </div>

      {/* Running tally bar */}
      {Object.keys(tally).length > 0 && (
        <div className="staggered-tally">
          <div className="staggered-tally-header">Running Tally</div>
          <div className="vote-tally-list">
            {Object.entries(tally)
              .sort(([, a], [, b]) => b - a)
              .map(([name, count]) => {
                const pct = (count / maxCount) * 100;
                return (
                  <div key={name} className="vote-tally-row animate-fade-in-up">
                    <div className="vote-tally-info">
                      <span className="vote-tally-name">{name}</span>
                      <span className="vote-tally-count">{count}</span>
                    </div>
                    <div className="vote-tally-bar-track">
                      <div
                        className="vote-tally-bar-fill"
                        style={{
                          width: `${pct}%`,
                          background: "linear-gradient(90deg, var(--accent), var(--accent-hover))",
                        }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────────── */

export default function VotePanel() {
  const { t } = useI18n();
  const {
    session,
    selectedVote,
    setSelectedVote,
    hasVoted,
    castVote,
    voteResults,
    staggeredVotes,
  } = useGameState();
  const sfx = useSFX();
  const [showConfirm, setShowConfirm] = useState(false);

  if (!session) return null;

  const aliveCharacters = session.characters.filter((c) => !c.is_eliminated);
  const selectedName = aliveCharacters.find((c) => c.id === selectedVote)?.name;

  // Show staggered vote reveal while votes are streaming in (after player votes, before tally)
  if (hasVoted && !voteResults && staggeredVotes.length > 0) {
    return (
      <StaggeredVoteReveal
        votes={staggeredVotes}
        totalVoters={aliveCharacters.length}
      />
    );
  }

  // Vote results view (final tally)
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
        onClick={() => setShowConfirm(true)}
      >
        {hasVoted ? t("game.vote.waiting") : t("game.vote.confirm")}
      </button>

      {/* Vote Confirmation Dialog */}
      {showConfirm && selectedVote && (
        <div className="vote-confirm-overlay" onClick={() => setShowConfirm(false)}>
          <div className="vote-confirm-dialog animate-fade-in-up" onClick={(e) => e.stopPropagation()}>
            <p className="vote-confirm-text">
              Vote to eliminate <strong>{selectedName}</strong>?
            </p>
            <p className="vote-confirm-subtext">This action cannot be undone.</p>
            <div className="vote-confirm-actions">
              <button
                className="vote-confirm-cancel"
                onClick={() => setShowConfirm(false)}
              >
                Cancel
              </button>
              <button
                className="demo-btn vote-confirm-submit"
                onClick={() => {
                  setShowConfirm(false);
                  sfx.playVote();
                  castVote(selectedVote);
                }}
              >
                Confirm Vote
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
