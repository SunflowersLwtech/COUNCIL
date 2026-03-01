"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import type {
  GamePhase,
  CharacterPublic,
  GameSession,
  VoteResult,
  CharacterRevealed,
  GameStreamEvent,
  ScenarioInfo,
  PlayerRole,
  NightActionTarget,
} from "@/lib/game-types";
import * as api from "@/lib/api";

export interface GameChatMessage {
  role: "user" | "character" | "narrator" | "system";
  characterId?: string;
  characterName?: string;
  content: string;
  isThinking?: boolean;
  isStreaming?: boolean;
  voiceId?: string;
  isComplication?: boolean;
  emotion?: string;
}

interface GameStateCtx {
  phase: GamePhase;
  isRecovering: boolean;
  isStarting: boolean;
  startProgress: number;
  startStatusText: string;
  session: GameSession | null;
  chatMessages: GameChatMessage[];
  isChatStreaming: boolean;
  parseProgress: string;
  selectedVote: string | null;
  hasVoted: boolean;
  voteResults: VoteResult | null;
  revealedCharacter: CharacterRevealed | null;
  gameEnd: { winner: string } | null;
  error: string | null;
  scenarios: ScenarioInfo[];
  round: number;
  tension: number;
  chatTarget: string | null;
  // Intro
  introNarration: string | null;
  completeIntro: () => void;
  // Player role
  playerRole: PlayerRole | null;
  isGhostMode: boolean;
  nightActionRequired: { actionType: string; targets: NightActionTarget[] } | null;
  investigationResult: { name: string; faction: string } | null;
  revealedCharacters: Array<{
    id: string; name: string; hidden_role: string; faction: string;
    is_eliminated: boolean; persona: string; public_role: string; avatar_seed: string;
  }>;
  staggeredVotes: Array<{
    voterName: string; targetName: string; timestamp: number;
  }>;
  // Actions
  uploadDocument: (file: File) => Promise<void>;
  uploadText: (text: string) => Promise<void>;
  loadScenario: (id: string) => Promise<void>;
  startGame: () => Promise<void>;
  showHowToPlay: () => void;
  sendMessage: (text: string, targetId?: string | null) => void;
  castVote: (charId: string) => void;
  setSelectedVote: (id: string | null) => void;
  setChatTarget: (id: string | null) => void;
  dismissReveal: () => void;
  triggerNight: () => void;
  resetGame: () => void;
  loadScenarios: () => Promise<void>;
  submitNightAction: (targetId: string) => void;
  dismissInvestigation: () => void;
  endDiscussion: () => void;
}

const GameStateContext = createContext<GameStateCtx | null>(null);

interface GameStateProviderProps {
  children: ReactNode;
  onCharacterResponse?: (content: string, characterName: string, voiceId?: string, characterId?: string) => void;
}

export function GameStateProvider({ children, onCharacterResponse }: GameStateProviderProps) {
  const [phase, setPhase] = useState<GamePhase>("upload");
  const [isRecovering, setIsRecovering] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [startProgress, setStartProgress] = useState(0);
  const [startStatusText, setStartStatusText] = useState("Preparing the council...");
  const [session, setSession] = useState<GameSession | null>(null);
  const [chatMessages, setChatMessages] = useState<GameChatMessage[]>([]);
  const [isChatStreaming, setIsChatStreaming] = useState(false);
  const [parseProgress, setParseProgress] = useState("");
  const [selectedVote, setSelectedVote] = useState<string | null>(null);
  const [hasVoted, setHasVoted] = useState(false);
  const [voteResults, setVoteResults] = useState<VoteResult | null>(null);
  const [revealedCharacter, setRevealedCharacter] = useState<CharacterRevealed | null>(null);
  const [gameEnd, setGameEnd] = useState<{ winner: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [round, setRound] = useState(1);
  const [tension, setTension] = useState(0.2);
  const [chatTarget, setChatTarget] = useState<string | null>(null);
  const [introNarration, setIntroNarration] = useState<string | null>(null);
  const [playerRole, setPlayerRole] = useState<PlayerRole | null>(null);
  const [isGhostMode, setIsGhostMode] = useState(false);
  const [nightActionRequired, setNightActionRequired] = useState<{
    actionType: string; targets: NightActionTarget[];
  } | null>(null);
  const [investigationResult, setInvestigationResult] = useState<{
    name: string; faction: string;
  } | null>(null);
  const [revealedCharacters, setRevealedCharacters] = useState<Array<{
    id: string; name: string; hidden_role: string; faction: string;
    is_eliminated: boolean; persona: string; public_role: string; avatar_seed: string;
  }>>([]);
  // Staggered vote reveal: accumulate individual votes for animated display
  const [staggeredVotes, setStaggeredVotes] = useState<Array<{
    voterName: string; targetName: string; timestamp: number;
  }>>([]);

  // Prune chat messages if they exceed 500
  useEffect(() => {
    if (chatMessages.length > 500) {
      setChatMessages(prev => prev.slice(-400));
    }
  }, [chatMessages.length]);

  const streamRef = useRef<AbortController | null>(null);
  const pendingDiscussionEndRef = useRef(false);

  // ── Session recovery from localStorage ────────────────────────────
  const STORAGE_KEY = "council_session_id";
  const hasAttemptedRecovery = useRef(false);

  useEffect(() => {
    if (hasAttemptedRecovery.current) return;
    hasAttemptedRecovery.current = true;

    const savedId = localStorage.getItem(STORAGE_KEY);
    if (!savedId || session) return;

    setIsRecovering(true);
    (async () => {
      try {
        const data = await api.getGameState(savedId, true);
        // Restore session
        setSession({
          session_id: data.session_id,
          world_title: data.world_title,
          world_setting: data.world_setting,
          characters: data.characters,
          phase: data.phase,
        });
        // If recovered to intro, skip to discussion (backend is already in discussion)
        if (data.phase === "intro") {
          setPhase("discussion");
        } else {
          setPhase(data.phase as GamePhase);
        }
        setRound(data.round || 1);

        // Restore messages
        if (data.messages && data.messages.length > 0) {
          const restored: GameChatMessage[] = data.messages.map((m: any) => {
            if (m.speaker_id === "player") {
              return { role: "user" as const, content: m.content };
            }
            if (m.speaker_id === "narrator" || m.speaker_id === "") {
              return { role: "narrator" as const, content: m.content };
            }
            return {
              role: "character" as const,
              characterId: m.speaker_id,
              characterName: m.speaker_name,
              content: m.content,
            };
          });
          setChatMessages(restored);
        }

        // Restore vote results
        if (data.vote_results && data.vote_results.length > 0) {
          setVoteResults(data.vote_results[data.vote_results.length - 1]);
        }

        // Restore player role
        if (data.player_role) {
          setPlayerRole(data.player_role);
          if (data.player_role.is_eliminated) {
            setIsGhostMode(true);
          }
        }

        // Restore pending night action prompt
        if (data.night_action_prompt) {
          setNightActionRequired({
            actionType: data.night_action_prompt.action_type,
            targets: data.night_action_prompt.eligible_targets,
          });
        }

        // Restore game end
        if (data.winner) {
          setGameEnd({ winner: data.winner });
        }
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      } finally {
        setIsRecovering(false);
      }
    })();
  }, []);

  const handleSessionCreated = useCallback((sess: GameSession) => {
    setSession(sess);
    setPhase("lobby");
    setParseProgress("");
    setError(null);
    localStorage.setItem(STORAGE_KEY, sess.session_id);
  }, []);

  const onCharacterResponseRef = useRef(onCharacterResponse);
  onCharacterResponseRef.current = onCharacterResponse;

  const handleStreamEvent = useCallback((event: GameStreamEvent) => {
    switch (event.type) {
      case "responders":
        // List of characters who will respond - no UI action needed
        break;

      case "thinking":
        if (event.character_name) {
          setChatMessages((prev) => [
            ...prev,
            {
              role: "character",
              characterId: event.character_id,
              characterName: event.character_name,
              content: "",
              isThinking: true,
            },
          ]);
        }
        break;

      case "stream_start":
        // Replace thinking placeholder with empty streaming message
        setChatMessages((prev) => {
          const filtered = prev.filter(
            (m) => !(m.characterId === event.character_id && m.isThinking)
          );
          return [
            ...filtered,
            {
              role: "character",
              characterId: event.character_id,
              characterName: event.character_name,
              content: "",
              isStreaming: true,
            },
          ];
        });
        break;

      case "stream_delta":
        // Append delta to the streaming message
        setChatMessages((prev) => {
          const idx = prev.findLastIndex(
            (m) => m.characterId === event.character_id && m.isStreaming
          );
          if (idx === -1) return prev;
          const updated = [...prev];
          updated[idx] = { ...updated[idx], content: updated[idx].content + (event.delta || "") };
          return updated;
        });
        break;

      case "stream_end":
        // Finalize streaming message with complete text, trigger TTS
        setChatMessages((prev) => {
          const idx = prev.findLastIndex(
            (m) => m.characterId === event.character_id && m.isStreaming
          );
          if (idx === -1) return prev;
          const updated = [...prev];
          updated[idx] = {
            ...updated[idx],
            content: event.content || updated[idx].content,
            isStreaming: false,
            voiceId: event.voice_id,
            emotion: event.emotion,
          };
          return updated;
        });
        if (event.content && event.character_name) {
          onCharacterResponseRef.current?.(event.content, event.character_name, event.voice_id, event.character_id);
        }
        break;

      case "response":
        // Legacy non-streaming response (fallback)
        setChatMessages((prev) => {
          const filtered = prev.filter(
            (m) => !(m.characterId === event.character_id && m.isThinking)
          );
          return [
            ...filtered,
            {
              role: "character",
              characterId: event.character_id,
              characterName: event.character_name,
              content: event.content || "",
              voiceId: event.voice_id,
              emotion: event.emotion,
            },
          ];
        });
        if (event.content && event.character_name) {
          onCharacterResponseRef.current?.(event.content, event.character_name, event.voice_id, event.character_id);
        }
        break;

      case "reaction":
        // Spontaneous character reaction
        setChatMessages((prev) => [
          ...prev,
          {
            role: "character",
            characterId: event.character_id,
            characterName: event.character_name,
            content: event.content || "",
            voiceId: event.voice_id,
            emotion: event.emotion,
          },
        ]);
        if (event.content && event.character_name) {
          onCharacterResponseRef.current?.(event.content, event.character_name, event.voice_id, event.character_id);
        }
        break;

      case "complication":
        // Dynamic game event injected by the game master
        setChatMessages((prev) => [
          ...prev,
          { role: "narrator", content: event.content || "Something unexpected happens...", isComplication: true },
        ]);
        if (event.tension !== undefined) setTension(event.tension);
        if (event.content) {
          onCharacterResponseRef.current?.(event.content, "Narrator");
        }
        break;

      case "discussion_warning":
        setChatMessages((prev) => [
          ...prev,
          { role: "system", content: event.content || "The council grows restless. A vote will be called shortly." },
        ]);
        break;

      case "discussion_ending":
        pendingDiscussionEndRef.current = false;
        setChatMessages((prev) => [
          ...prev,
          { role: "system", content: event.content || "The council has heard enough. The vote will now begin." },
        ]);
        // Auto-transition to voting phase so VotePanel appears
        setPhase("voting");
        setHasVoted(false);
        setVoteResults(null);
        setSelectedVote(null);
        setStaggeredVotes([]);
        break;

      case "night_action":
        // Night action progress (hidden details, just show action type)
        setChatMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: `${event.character_name || "Someone"} performs a mysterious action...`,
          },
        ]);
        break;

      case "narration":
        setChatMessages((prev) => [
          ...prev,
          { role: "narrator", content: event.content || event.narration || "" },
        ]);
        // Trigger TTS for narrator
        if (event.content || event.narration) {
          onCharacterResponseRef.current?.(event.content || event.narration || "", "Narrator");
        }
        // Narration with phase/round means phase transition
        if (event.phase) {
          setPhase(event.phase as GamePhase);
          if (event.round) setRound(event.round);
          if (event.phase === "voting") {
            setHasVoted(false);
            setVoteResults(null);
            setSelectedVote(null);
            setStaggeredVotes([]);
            setChatMessages((prev) => [
              ...prev,
              {
                role: "system",
                content: "Time to vote. Select the council member you believe is a traitor.",
              },
            ]);
          }
          if (event.phase === "discussion" && event.round && event.round > 1) {
            setChatMessages((prev) => [
              ...prev,
              {
                role: "system",
                content: "A new day dawns. The council is back in session \u2014 discuss what happened and plan your next move.",
              },
            ]);
          }
        }
        break;

      case "night_started":
        setPhase("night");
        setChatMessages((prev) => [
          ...prev,
          { role: "narrator", content: event.content || "Night falls... The hidden forces move in darkness." },
          { role: "system", content: "Night falls. You have no night action \u2014 wait for dawn." },
        ]);
        if (event.content) {
          onCharacterResponseRef.current?.(event.content, "Narrator");
        }
        break;

      case "night_results":
        setChatMessages((prev) => [
          ...prev,
          { role: "narrator", content: event.content || event.narration || "Dawn breaks... The results of the night are revealed." },
        ]);
        if (event.content || event.narration) {
          onCharacterResponseRef.current?.(event.content || event.narration || "", "Narrator");
        }
        // Update eliminated characters from night kills
        {
          const ids = event.eliminated_ids || (event.character_id ? [event.character_id] : []);
          if (ids.length > 0) {
            setSession((prev) => {
              if (!prev) return prev;
              const eliminatedSet = new Set(ids);
              return {
                ...prev,
                characters: prev.characters.map((c) =>
                  eliminatedSet.has(c.id)
                    ? { ...c, is_eliminated: true }
                    : c
                ),
              };
            });
          }
        }
        break;

      case "voting_started":
        setPhase("voting");
        setHasVoted(false);
        setVoteResults(null);
        setSelectedVote(null);
        setStaggeredVotes([]);
        setChatMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: "Time to vote. Select the council member you believe is a traitor.",
          },
        ]);
        break;

      case "vote":
        // Accumulate into staggered votes for animated reveal
        if (event.voter_name && event.target_name) {
          setStaggeredVotes((prev) => [
            ...prev,
            {
              voterName: event.voter_name!,
              targetName: event.target_name!,
              timestamp: Date.now(),
            },
          ]);
        }
        break;

      case "tally":
        setVoteResults((prev) => ({
          votes: prev?.votes || [],
          tally: event.tally || {},
          eliminated_id: prev?.eliminated_id || null,
          eliminated_name: prev?.eliminated_name || null,
          is_tie: event.is_tie || false,
        }));
        break;

      case "elimination":
        // Character eliminated - update session state
        setRevealedCharacter(null);
        if (event.character_id) {
          setSession((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              characters: prev.characters.map((c) =>
                c.id === event.character_id
                  ? { ...c, is_eliminated: true }
                  : c
              ),
            };
          });
        }
        // Update vote results with elimination info
        setVoteResults(prev => prev ? {
            ...prev,
            eliminated_id: event.character_id || null,
            eliminated_name: event.character_name || null,
        } : prev);
        setChatMessages((prev) => [
          ...prev,
          {
            role: "narrator",
            content: event.narration || `${event.character_name} has been eliminated. They were a ${event.hidden_role} of the ${event.faction}.`,
          },
        ]);
        setPhase("reveal");
        break;

      case "night_action_prompt":
        // Player needs to choose a night action
        if (event.action_type && event.eligible_targets) {
          setNightActionRequired({
            actionType: event.action_type,
            targets: event.eligible_targets,
          });
          setChatMessages((prev) => [
            ...prev,
            {
              role: "system",
              content: `Night falls. You may perform your action: ${event.action_type}. Select your target below.`,
            },
          ]);
        }
        break;

      case "player_eliminated":
        // Player has been eliminated — enter ghost mode
        setIsGhostMode(true);
        if (event.all_characters) {
          setRevealedCharacters(event.all_characters);
        }
        setPlayerRole((prev) =>
          prev ? { ...prev, is_eliminated: true, eliminated_by: event.eliminated_by || "" } : prev
        );
        setChatMessages((prev) => [
          ...prev,
          {
            role: "narrator",
            content: event.narration || `You have been eliminated. You were a ${event.hidden_role} of the ${event.faction}. Entering ghost mode...`,
          },
        ]);
        break;

      case "investigation_result":
        if (event.investigation_result) {
          setInvestigationResult(event.investigation_result);
        }
        break;

      case "game_over":
        setGameEnd({ winner: event.winner || "Unknown" });
        setChatMessages((prev) => [
          ...prev,
          { role: "narrator", content: event.narration || `Game over! ${event.winner} wins!` },
        ]);
        setPhase("ended");
        break;

      case "error":
        setError(event.error || "An error occurred");
        setIsChatStreaming(false);
        break;

      case "done":
        setIsChatStreaming(false);
        streamRef.current = null;
        // done event may carry phase/round for next phase
        if (event.phase) {
          setPhase(event.phase as GamePhase);
          if (event.round) setRound(event.round);
        }
        if (event.tension !== undefined) setTension(event.tension);
        // Execute deferred discussion end (timer/button fired while streaming)
        if (pendingDiscussionEndRef.current) {
          pendingDiscussionEndRef.current = false;
          setChatMessages(prev => [...prev, { role: "system", content: "The council has heard enough. The vote will now begin." }]);
          setPhase("voting");
          setHasVoted(false);
          setVoteResults(null);
          setSelectedVote(null);
          setStaggeredVotes([]);
        }
        break;
    }
  }, []);

  const uploadDocument = useCallback(async (file: File) => {
    setPhase("parsing");
    setParseProgress("Analyzing document...");
    setError(null);
    try {
      const sess = await api.createGameFromDocument(file);
      handleSessionCreated(sess);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setPhase("upload");
    }
  }, [handleSessionCreated]);

  const uploadText = useCallback(async (text: string) => {
    setPhase("parsing");
    setParseProgress("Generating characters...");
    setError(null);
    try {
      const sess = await api.createGameFromText(text);
      handleSessionCreated(sess);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Creation failed");
      setPhase("upload");
    }
  }, [handleSessionCreated]);

  const loadScenarioFn = useCallback(async (id: string) => {
    setPhase("parsing");
    setParseProgress("Loading scenario...");
    setError(null);
    try {
      const sess = await api.loadScenario(id);
      handleSessionCreated(sess);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scenario");
      setPhase("upload");
    }
  }, [handleSessionCreated]);

  const HOWTOPLAY_STORAGE_KEY = "council_howtoplay_seen";

  const startGameFn = useCallback(async () => {
    if (!session) return;
    setError(null);
    setIsStarting(true);
    setStartProgress(0);
    setStartStatusText("Preparing the council...");

    // Simulated progress stages while the API call runs
    const stages = [
      { pct: 15, text: "Assigning roles..." },
      { pct: 35, text: "Building world state..." },
      { pct: 55, text: "Awakening characters..." },
      { pct: 75, text: "Setting the scene..." },
      { pct: 90, text: "Almost ready..." },
    ];
    let stageIdx = 0;
    const progressTimer = setInterval(() => {
      if (stageIdx < stages.length) {
        setStartProgress(stages[stageIdx].pct);
        setStartStatusText(stages[stageIdx].text);
        stageIdx++;
      }
    }, 600);

    try {
      const result = await api.startGame(session.session_id);
      clearInterval(progressTimer);
      setStartProgress(100);
      setStartStatusText("The council awaits...");

      // Fetch player role in parallel with the brief pause
      try {
        const role = await api.getPlayerRole(session.session_id);
        setPlayerRole(role);
      } catch {
        // Player role is optional
      }

      // Brief pause at 100% before transitioning
      await new Promise((r) => setTimeout(r, 400));

      setRound(result.round || 1);
      setIntroNarration(result.narration || null);
      setPhase("intro");
    } catch (err) {
      clearInterval(progressTimer);
      setError(err instanceof Error ? err.message : "Failed to start game");
    } finally {
      setIsStarting(false);
      setStartProgress(0);
    }
  }, [session]);

  const completeIntro = useCallback(() => {
    setPhase("discussion");
    setChatMessages([{
      role: "narrator",
      content: introNarration || "The council is now in session. Speak your mind.",
    }]);
    setIntroNarration(null);

    // Auto-trigger opening statements from AI characters
    if (session) {
      setIsChatStreaming(true);
      const controller = api.streamOpenDiscussion(
        session.session_id,
        handleStreamEvent
      );
      streamRef.current = controller;
    }
  }, [introNarration, session, handleStreamEvent]);

  const showHowToPlay = useCallback(() => {
    if (!session) return;
    const seen = localStorage.getItem(HOWTOPLAY_STORAGE_KEY);
    if (seen === "true") {
      // Skip straight to starting the game
      startGameFn();
    } else {
      setPhase("howtoplay");
    }
  }, [session, startGameFn]);

  const sendMessage = useCallback(
    (text: string, targetId?: string | null) => {
      if (!session || isChatStreaming || isGhostMode) return;

      const target = targetId ?? chatTarget;
      const targetChar = target
        ? session.characters.find((c) => c.id === target)
        : null;

      setChatMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: targetChar ? `@${targetChar.name} ${text}` : text,
        },
      ]);
      setIsChatStreaming(true);
      setChatTarget(null);

      const controller = api.streamGameChat(
        session.session_id,
        text,
        target ?? null,
        handleStreamEvent
      );
      streamRef.current = controller;
    },
    [session, isChatStreaming, isGhostMode, chatTarget, handleStreamEvent]
  );

  const castVote = useCallback(
    (charId: string) => {
      if (!session || hasVoted || isGhostMode) return;
      setHasVoted(true);
      setIsChatStreaming(true);

      const controller = api.streamGameVote(
        session.session_id,
        charId,
        handleStreamEvent
      );
      streamRef.current = controller;
    },
    [session, hasVoted, isGhostMode, handleStreamEvent]
  );

  const submitNightAction = useCallback(
    (targetId: string) => {
      if (!session || !nightActionRequired || isChatStreaming) return;
      setIsChatStreaming(true);
      setNightActionRequired(null);
      const controller = api.streamPlayerNightAction(
        session.session_id,
        nightActionRequired.actionType,
        targetId,
        handleStreamEvent
      );
      streamRef.current = controller;
    },
    [session, nightActionRequired, isChatStreaming, handleStreamEvent]
  );

  const dismissInvestigation = useCallback(() => {
    setInvestigationResult(null);
  }, []);

  const endDiscussion = useCallback(() => {
    if (phase !== "discussion") return;
    if (isChatStreaming) {
      pendingDiscussionEndRef.current = true;
      return;
    }
    setChatMessages(prev => [...prev, { role: "system", content: "The council has heard enough. The vote will now begin." }]);
    setPhase("voting");
    setHasVoted(false);
    setVoteResults(null);
    setSelectedVote(null);
    setStaggeredVotes([]);
  }, [phase, isChatStreaming]);

  const dismissReveal = useCallback(() => {
    setRevealedCharacter(null);
    // Auto-trigger night phase if game hasn't ended
    if (session && !gameEnd) {
      setIsChatStreaming(true);
      const controller = api.streamGameNight(
        session.session_id,
        handleStreamEvent
      );
      streamRef.current = controller;
    }
  }, [session, gameEnd, handleStreamEvent]);

  const triggerNight = useCallback(() => {
    if (!session || isChatStreaming) return;
    setIsChatStreaming(true);
    const controller = api.streamGameNight(
      session.session_id,
      handleStreamEvent
    );
    streamRef.current = controller;
  }, [session, isChatStreaming, handleStreamEvent]);

  const resetGame = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.abort();
      streamRef.current = null;
    }
    localStorage.removeItem(STORAGE_KEY);
    setPhase("upload");
    setSession(null);
    setChatMessages([]);
    setIsChatStreaming(false);
    setParseProgress("");
    setSelectedVote(null);
    setHasVoted(false);
    setVoteResults(null);
    setRevealedCharacter(null);
    setGameEnd(null);
    setError(null);
    setRound(1);
    setIntroNarration(null);
    setPlayerRole(null);
    setIsGhostMode(false);
    setNightActionRequired(null);
    setInvestigationResult(null);
    setRevealedCharacters([]);
    setStaggeredVotes([]);
  }, []);

  const loadScenarios = useCallback(async () => {
    try {
      const list = await api.getGameScenarios();
      setScenarios(list);
    } catch {
      // scenarios are optional
    }
  }, []);

  return (
    <GameStateContext.Provider
      value={{
        phase,
        isRecovering,
        isStarting,
        startProgress,
        startStatusText,
        session,
        chatMessages,
        isChatStreaming,
        parseProgress,
        selectedVote,
        hasVoted,
        voteResults,
        revealedCharacter,
        gameEnd,
        error,
        scenarios,
        round,
        tension,
        chatTarget,
        introNarration,
        completeIntro,
        playerRole,
        isGhostMode,
        nightActionRequired,
        investigationResult,
        revealedCharacters,
        staggeredVotes,
        uploadDocument,
        uploadText,
        loadScenario: loadScenarioFn,
        startGame: startGameFn,
        showHowToPlay,
        sendMessage,
        castVote,
        setSelectedVote,
        setChatTarget,
        dismissReveal,
        triggerNight,
        resetGame,
        loadScenarios,
        submitNightAction,
        dismissInvestigation,
        endDiscussion,
      }}
    >
      {children}
    </GameStateContext.Provider>
  );
}

export function useGameState() {
  const ctx = useContext(GameStateContext);
  if (!ctx) throw new Error("useGameState must be used within GameStateProvider");
  return ctx;
}
