"use client";

import { Users, Play, MapPin } from "lucide-react";
import { useGameState } from "@/hooks/useGameState";
import { useI18n } from "@/lib/i18n";
import CharacterCard from "@/components/CharacterCard";

export default function GameLobby() {
  const { t } = useI18n();
  const { session, startGame, error } = useGameState();

  if (!session) return null;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="max-w-3xl w-full space-y-8">
        {/* World Title */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold welcome-gradient-text">
            {session.world_title}
          </h1>
          <p
            className="text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            {t("game.lobby.title")}
          </p>
        </div>

        {/* Setting */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-3">
            <MapPin size={14} style={{ color: "var(--accent)" }} />
            <span
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: "var(--text-muted)" }}
            >
              {t("game.lobby.setting")}
            </span>
          </div>
          <p
            className="text-sm leading-relaxed"
            style={{ color: "var(--text-secondary)" }}
          >
            {session.world_setting}
          </p>
        </div>

        {/* Characters */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Users size={14} style={{ color: "var(--accent)" }} />
            <span
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: "var(--text-muted)" }}
            >
              {t("game.lobby.characters")} ({session.characters.length})
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {session.characters.map((char) => (
              <CharacterCard key={char.id} character={char} />
            ))}
          </div>
        </div>

        {/* Start button */}
        <div className="text-center">
          <button
            className="demo-btn text-lg px-12 py-4 flex items-center gap-3 mx-auto"
            onClick={startGame}
          >
            <Play size={20} />
            {t("game.lobby.startGame")}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div
            className="p-3 rounded-lg text-sm text-center animate-fade-in"
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              color: "var(--critical)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
            }}
          >
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
