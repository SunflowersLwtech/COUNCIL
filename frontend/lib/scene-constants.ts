export const TABLE_RADIUS = 1.8;
export const SEAT_RADIUS = 2.8;
export const TABLE_HEIGHT = 0.8;

export function getSeatPosition(index: number, totalSeats: number = 6): [number, number, number] {
  const angle = (index / totalSeats) * Math.PI * 2 - Math.PI / 2;
  return [Math.cos(angle) * SEAT_RADIUS, 0, Math.sin(angle) * SEAT_RADIUS];
}

export const CAMERA_PRESETS = {
  "birds-eye": { position: [0, 8, 0.1] as const, target: [0, 0, 0] as const },
  "first-person": {
    position: [0, 1.6, -2.5] as const,
    target: [0, 0.8, 0] as const,
  },
  orbit: { position: [4, 3, 4] as const, target: [0, 0.8, 0] as const },
} as const;

export type CameraView = "birds-eye" | "first-person" | "orbit";

export interface Agent3DConfig {
  id: string;
  /** i18n key for display name, e.g. "agents.Architecture Analyst" */
  i18nKey: string;
  displayName: string;
  seatIndex: number;
  color: string;
  initial: string;
}

// ── Dynamic agent configs from game characters ────────────────────

import type { CharacterPublic } from "@/lib/game-types";

const CHAR_COLORS = ["#4ECDC4", "#45B7D1", "#96CEB4", "#FF6B6B", "#FFD93D", "#C39BD3", "#F1948A", "#76D7C4"];

export function createAgent3DConfigs(characters: CharacterPublic[]): Agent3DConfig[] {
  // Seat 0 is reserved for the player; AI characters start at seat 1
  const playerSeat: Agent3DConfig = {
    id: "__player__",
    i18nKey: "character.player",
    displayName: "You",
    seatIndex: 0,
    color: "#FFD700",
    initial: "P",
  };
  const charSeats = characters.map((char, index) => ({
    id: char.id,
    i18nKey: `character.${char.id}`,
    displayName: char.name,
    seatIndex: index + 1,
    color: CHAR_COLORS[index % CHAR_COLORS.length],
    initial: char.name.charAt(0).toUpperCase(),
  }));
  return [playerSeat, ...charSeats];
}

export const AGENTS_3D: Agent3DConfig[] = [
  {
    id: "architecture",
    i18nKey: "agents.Architecture Analyst",
    displayName: "Architecture",
    seatIndex: 1,
    color: "#4ECDC4",
    initial: "A",
  },
  {
    id: "code-quality",
    i18nKey: "agents.Code Quality Analyst",
    displayName: "Code Quality",
    seatIndex: 2,
    color: "#45B7D1",
    initial: "Q",
  },
  {
    id: "documentation",
    i18nKey: "agents.Documentation Analyst",
    displayName: "Documentation",
    seatIndex: 3,
    color: "#96CEB4",
    initial: "D",
  },
  {
    id: "security",
    i18nKey: "agents.Security Analyst",
    displayName: "Security",
    seatIndex: 4,
    color: "#FF6B6B",
    initial: "S",
  },
];
