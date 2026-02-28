"use client";

import { useI18n } from "@/lib/i18n";

const AGENT_COLORS: Record<string, string> = {
  Orchestrator: "#FF6B35",
  "Architecture Analyst": "#4ECDC4",
  "Code Quality Analyst": "#45B7D1",
  "Documentation Analyst": "#96CEB4",
  "Security Analyst": "#FF6B6B",
  System: "#6b7280",
};

const AGENT_INITIALS: Record<string, string> = {
  Orchestrator: "O",
  "Architecture Analyst": "A",
  "Code Quality Analyst": "Q",
  "Documentation Analyst": "D",
  "Security Analyst": "S",
  System: "!",
};

interface AgentAvatarProps {
  role: string;
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
}

export default function AgentAvatar({
  role,
  size = "md",
  pulse = false,
}: AgentAvatarProps) {
  const { t } = useI18n();
  const color = AGENT_COLORS[role] || "#6b7280";
  const initial = AGENT_INITIALS[role] || role[0]?.toUpperCase() || "?";
  const displayName = t(`agents.${role}`);

  const sizes = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base",
  };

  return (
    <div
      className={`${sizes[size]} rounded-full flex items-center justify-center font-bold text-white shrink-0 ${pulse ? "animate-pulse-dot" : ""}`}
      style={{ backgroundColor: color }}
      title={displayName}
    >
      {initial}
    </div>
  );
}
