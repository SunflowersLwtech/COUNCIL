/** Maps agent display names (from chat API) to TTS agent_id values. */

const ROLE_TO_AGENT_ID: Record<string, string> = {
  Orchestrator: "orchestrator",
  "Architecture Analyst": "architecture",
  "Code Quality Analyst": "code-quality",
  "Documentation Analyst": "documentation",
  "Security Analyst": "security",
};

export function agentRoleToId(agentRole: string): string {
  // For COUNCIL system agents, map display name to ID.
  // For game characters, the agentRole is already the voice_id — pass through as-is.
  return ROLE_TO_AGENT_ID[agentRole] ?? agentRole;
}

export const AGENT_SEAT_INDEX: Record<string, number> = {
  architecture: 1,
  "code-quality": 2,
  documentation: 3,
  security: 4,
};
