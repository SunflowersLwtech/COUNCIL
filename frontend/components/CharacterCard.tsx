"use client";

import type { CharacterPublic } from "@/lib/game-types";

const CHAR_COLORS = [
  "#4ECDC4",
  "#45B7D1",
  "#96CEB4",
  "#FF6B6B",
  "#FFD93D",
  "#C39BD3",
  "#F1948A",
  "#76D7C4",
];

function seedToColor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  return CHAR_COLORS[Math.abs(hash) % CHAR_COLORS.length];
}

interface CharacterCardProps {
  character: CharacterPublic;
  isSpeaking?: boolean;
  isThinking?: boolean;
  isSelected?: boolean;
  onClick?: () => void;
  compact?: boolean;
}

export default function CharacterCard({
  character,
  isSpeaking = false,
  isThinking = false,
  isSelected = false,
  onClick,
  compact = false,
}: CharacterCardProps) {
  const color = seedToColor(character.avatar_seed || character.id);
  const initial = character.name.charAt(0).toUpperCase();

  const cardClass = [
    "character-card",
    isSelected && "character-card-selected",
    character.is_eliminated && "character-card-eliminated",
    isSpeaking && "character-card-speaking",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cardClass} onClick={onClick}>
      <div className="flex items-center gap-3">
        {/* Avatar */}
        <div
          className="flex items-center justify-center rounded-full font-bold text-white shrink-0"
          style={{
            width: compact ? 36 : 44,
            height: compact ? 36 : 44,
            backgroundColor: color,
            fontSize: compact ? 14 : 18,
            boxShadow: isSpeaking ? `0 0 12px ${color}80` : undefined,
          }}
        >
          {initial}
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <p
            className="font-semibold truncate"
            style={{
              color: character.is_eliminated
                ? "var(--text-muted)"
                : "var(--text-primary)",
              fontSize: compact ? 13 : 15,
              textDecoration: character.is_eliminated
                ? "line-through"
                : undefined,
            }}
          >
            {character.name}
          </p>
          <p
            className="text-xs truncate"
            style={{ color: "var(--text-muted)" }}
          >
            {character.public_role}
          </p>
        </div>

        {/* Status indicators */}
        {isThinking && (
          <div className="thinking-dots">
            <span style={{ backgroundColor: color }} />
            <span style={{ backgroundColor: color }} />
            <span style={{ backgroundColor: color }} />
          </div>
        )}
      </div>
    </div>
  );
}

export { seedToColor, CHAR_COLORS };
