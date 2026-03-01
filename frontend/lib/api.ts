import type {
  ScenarioInfo,
  GameSession,
  GameStreamEvent,
  CharacterRevealed,
  PlayerRole,
} from "@/lib/game-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface Finding {
  severity: "critical" | "high" | "medium" | "low" | "info";
  category: string;
  file_path: string;
  line_range: string | null;
  description: string;
  recommendation: string;
}

export interface AgentReport {
  agent_role: string;
  findings: Finding[];
  summary: string;
}

export interface ConsensusSummary {
  critical: Finding[];
  high: Finding[];
  medium: Finding[];
  low: Finding[];
  positive: string[];
  cross_references: {
    finding_indices: number[];
    agents: string[];
    description: string;
  }[];
  executive_summary: string;
}

export interface AnalysisResult {
  status: string;
  consensus: ConsensusSummary;
  agent_reports: Record<string, AgentReport>;
}

export interface ChatResponse {
  agent_role: string;
  response: string;
}

export async function generateTTS(
  text: string,
  agentId: string
): Promise<Blob | null> {
  try {
    const res = await fetch(`${API_BASE}/api/voice/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, agent_id: agentId }),
    });
    if (!res.ok) {
      console.warn(`TTS request failed: ${res.status} ${res.statusText}`);
      return null;
    }
    const ct = res.headers.get("content-type");
    if (ct?.includes("audio")) return res.blob();
    console.warn("TTS response was not audio:", ct);
    return null;
  } catch (err) {
    console.warn("TTS fetch error:", err);
    return null;
  }
}

// ── Game API ────────────────────────────────────────────────────────

export async function getGameScenarios(): Promise<ScenarioInfo[]> {
  const res = await fetch(`${API_BASE}/api/game/scenarios`);
  if (!res.ok) throw new Error(`Failed to load scenarios: ${res.status} ${res.statusText}`);
  const data = await res.json();
  return data.scenarios || data;
}

export async function createGameFromDocument(file: File): Promise<GameSession> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/game/create`, { method: "POST", body: formData });
  if (!res.ok) throw new Error(`Failed to create game: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function createGameFromText(text: string): Promise<GameSession> {
  const formData = new FormData();
  formData.append("text", text);
  const res = await fetch(`${API_BASE}/api/game/create`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Failed to create game: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function loadScenario(scenarioId: string): Promise<GameSession> {
  const res = await fetch(`${API_BASE}/api/game/scenario/${scenarioId}`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to load scenario: ${res.status} ${res.statusText}`);
  return res.json();
}

export interface StartGameResponse {
  phase: string;
  round: number;
  narration: string;
  has_player_role: boolean;
}

export async function startGame(sessionId: string): Promise<StartGameResponse> {
  const res = await fetch(`${API_BASE}/api/game/${sessionId}/start`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to start game: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function getGameState(sessionId: string, full: boolean = false): Promise<any> {
  const params = full ? "?full=true" : "";
  const res = await fetch(`${API_BASE}/api/game/${sessionId}/state${params}`);
  if (!res.ok) throw new Error(`Failed to get game state: ${res.status} ${res.statusText}`);
  return res.json();
}

export function streamGameChat(
  sessionId: string,
  message: string,
  targetCharId: string | null,
  onEvent: (event: GameStreamEvent) => void
): AbortController {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(60000);
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/game/${sessionId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, target_character_id: targetCharId }),
        signal: AbortSignal.any([controller.signal, timeoutSignal]),
      });
      if (!res.ok) {
        onEvent({ type: "error", error: `Chat failed: ${res.statusText}` });
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try { onEvent(JSON.parse(line.slice(6))); } catch {}
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onEvent({ type: "error", error: (err as Error).message });
      }
    }
  })();
  return controller;
}

export function streamOpenDiscussion(
  sessionId: string,
  onEvent: (event: GameStreamEvent) => void
): AbortController {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(90000);
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/game/${sessionId}/open-discussion`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: AbortSignal.any([controller.signal, timeoutSignal]),
      });
      if (!res.ok) {
        onEvent({ type: "error", error: `Open discussion failed: ${res.statusText}` });
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try { onEvent(JSON.parse(line.slice(6))); } catch {}
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onEvent({ type: "error", error: (err as Error).message });
      }
    }
  })();
  return controller;
}

export function streamGameVote(
  sessionId: string,
  targetCharId: string,
  onEvent: (event: GameStreamEvent) => void
): AbortController {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(60000);
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/game/${sessionId}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_character_id: targetCharId }),
        signal: AbortSignal.any([controller.signal, timeoutSignal]),
      });
      if (!res.ok) {
        onEvent({ type: "error", error: `Vote failed: ${res.statusText}` });
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try { onEvent(JSON.parse(line.slice(6))); } catch {}
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onEvent({ type: "error", error: (err as Error).message });
      }
    }
  })();
  return controller;
}

export function streamNightChat(
  sessionId: string,
  message: string,
  onEvent: (event: GameStreamEvent) => void
): AbortController {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(60000);
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/game/${sessionId}/night-chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: AbortSignal.any([controller.signal, timeoutSignal]),
      });
      if (!res.ok) {
        onEvent({ type: "error", error: `Night chat failed: ${res.statusText}` });
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try { onEvent(JSON.parse(line.slice(6))); } catch {}
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onEvent({ type: "error", error: (err as Error).message });
      }
    }
  })();
  return controller;
}

export async function getPlayerRole(sessionId: string): Promise<PlayerRole> {
  const res = await fetch(`${API_BASE}/api/game/${sessionId}/player-role`);
  if (!res.ok) throw new Error(`Failed to get player role: ${res.status} ${res.statusText}`);
  return res.json();
}

export function streamPlayerNightAction(
  sessionId: string,
  actionType: string,
  targetId: string,
  onEvent: (event: GameStreamEvent) => void
): AbortController {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(60000);
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/game/${sessionId}/night-action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type: actionType, target_character_id: targetId }),
        signal: AbortSignal.any([controller.signal, timeoutSignal]),
      });
      if (!res.ok) {
        onEvent({ type: "error", error: `Night action failed: ${res.statusText}` });
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try { onEvent(JSON.parse(line.slice(6))); } catch {}
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onEvent({ type: "error", error: (err as Error).message });
      }
    }
  })();
  return controller;
}

export async function getCharacterReveal(sessionId: string, charId: string): Promise<CharacterRevealed> {
  const res = await fetch(`${API_BASE}/api/game/${sessionId}/reveal/${charId}`);
  if (!res.ok) throw new Error(`Failed to get reveal: ${res.status} ${res.statusText}`);
  return res.json();
}

export function streamGameNight(
  sessionId: string,
  onEvent: (event: GameStreamEvent) => void
): AbortController {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(60000);
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/game/${sessionId}/night`, {
        method: "POST",
        signal: AbortSignal.any([controller.signal, timeoutSignal]),
      });
      if (!res.ok) {
        onEvent({ type: "error", error: `Night failed: ${res.statusText}` });
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop()!;
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try { onEvent(JSON.parse(line.slice(6))); } catch {}
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onEvent({ type: "error", error: (err as Error).message });
      }
    }
  })();
  return controller;
}
