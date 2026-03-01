export type GamePhase = "upload" | "parsing" | "lobby" | "howtoplay" | "intro" | "discussion" | "voting" | "reveal" | "night" | "ended";

export interface CharacterPublic {
  id: string;
  name: string;
  persona: string;
  speaking_style: string;
  avatar_seed: string;
  public_role: string;
  voice_id: string;
  is_eliminated: boolean;
}

export interface CharacterRevealed extends CharacterPublic {
  hidden_role: string;
  faction: string;
  win_condition: string;
  hidden_knowledge: string[];
  behavioral_rules: string[];
  lie_timeline?: LieEntry[];
}

export interface LieEntry {
  round: number;
  statement: string;
  truth: string;
}

export interface GameSession {
  session_id: string;
  world_title: string;
  world_setting: string;
  characters: CharacterPublic[];
  phase: string;
}

export interface VoteResult {
  votes: Array<{ voter_id: string; voter_name: string; target_id: string; target_name: string }>;
  tally: Record<string, number>;
  eliminated_id: string | null;
  eliminated_name: string | null;
  is_tie: boolean;
}

export interface GameEndState {
  winner: string;
  characters: CharacterRevealed[];
}

export interface NightActionTarget {
  id: string;
  name: string;
  persona: string;
  public_role: string;
  avatar_seed: string;
}

export interface GameStreamEvent {
  type:
    | "thinking"
    | "responders"
    | "response"
    | "reaction"
    | "complication"
    | "night_action"
    | "night_action_prompt"
    | "narration"
    | "voting_started"
    | "vote"
    | "tally"
    | "elimination"
    | "player_eliminated"
    | "night_started"
    | "night_results"
    | "night_kill_reveal"
    | "investigation_result"
    | "discussion_warning"
    | "discussion_ending"
    | "game_over"
    | "stream_start"
    | "stream_delta"
    | "stream_end"
    | "error"
    | "done";
  character_id?: string;
  character_ids?: string[];
  character_name?: string;
  content?: string;
  delta?: string;
  voice_id?: string;
  tts_text?: string;
  phase?: string;
  round?: number;
  tension?: number;
  // vote events
  voter_name?: string;
  target_name?: string;
  tally?: Record<string, number>;
  is_tie?: boolean;
  // elimination
  hidden_role?: string;
  faction?: string;
  narration?: string;
  // night results
  eliminated_ids?: string[];
  // night_kill_reveal fields
  win_condition?: string;
  hidden_knowledge?: string[];
  behavioral_rules?: string[];
  persona?: string;
  public_role?: string;
  avatar_seed?: string;
  // game_over
  winner?: string;
  // emotion from character responses/reactions
  emotion?: string;
  // error
  error?: string;
  // night_action_prompt
  action_type?: string;
  eligible_targets?: NightActionTarget[];
  allies?: Array<{ id: string; name: string; avatar_seed: string }>;
  // investigation_result
  investigation_result?: { name: string; faction: string };
  // player_eliminated — all characters revealed for ghost mode
  eliminated_by?: string;
  all_characters?: Array<{
    id: string;
    name: string;
    hidden_role: string;
    faction: string;
    is_eliminated: boolean;
    persona: string;
    public_role: string;
    avatar_seed: string;
  }>;
}

export interface PlayerRole {
  hidden_role: string;
  faction: string;
  win_condition: string;
  allies: Array<{ id: string; name: string }>;
  is_eliminated: boolean;
  eliminated_by: string;
}

export interface ScenarioInfo {
  id: string;
  name: string;
}
