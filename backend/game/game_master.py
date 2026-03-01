"""GameMaster — manages phase transitions, win conditions, narration, voting, and tension."""

from __future__ import annotations

import os
import json
import asyncio
import random
import logging
from typing import TYPE_CHECKING
from mistralai import Mistral
from dotenv import load_dotenv

from backend.models.game_models import (
    GameState, GameEvent, CharacterPublicInfo, ChatMessage,
    NightAction, VoteRecord, VoteResult,
)
from backend.game import state as game_state
from backend.game.character_agent import CharacterAgent
from backend.game.prompts import (
    NARRATION_SYSTEM, NARRATION_TEMPLATES, RESPONDER_SELECTION_SYSTEM,
    DISCUSSION_SUMMARY_SYSTEM,
)

if TYPE_CHECKING:
    from backend.game.skill_loader import SkillConfig, SkillLoader

load_dotenv()
logger = logging.getLogger(__name__)

# Complication templates for dynamic event injection
EARLY_ROUND_THRESHOLD = 1  # Kills active from round 1 (first night after first discussion)

COMPLICATION_TYPES = {
    "revelation": "New information has come to light — someone's story doesn't add up. A detail from earlier contradicts what was just said.",
    "time_pressure": "Tensions are rising and patience is wearing thin. The council demands decisive action NOW.",
    "suspicion_shift": "A quiet council member suddenly looks nervous. Eyes turn toward someone who has been suspiciously silent.",
    "alliance_crack": "Two allies exchange a tense glance. Something unspoken hangs between them.",
    "evidence": "A piece of evidence is discovered — a note, a reaction, a slip of the tongue — that changes everything.",
}


class GameMaster:
    """Manages game flow: transitions, narration, voting, win conditions, tension."""

    # Discussion soft limit constants
    DISCUSSION_SOFT_LIMIT_PER_PLAYER = 2.5  # avg msgs per alive player before warning
    DISCUSSION_HARD_LIMIT_EXTRA = 3  # additional msgs after warning before auto-vote

    def __init__(
        self,
        skill_loader: SkillLoader | None = None,
        active_skills: list[SkillConfig] | None = None,
    ):
        self._mistral = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        self._skill_loader = skill_loader
        self.active_skills: list[SkillConfig] = []
        self._narration_injection: str = ""
        self._discussion_warning_sent: dict[str, dict[int, bool]] = {}  # session_id -> {round -> bool}
        if active_skills:
            self.set_skills(active_skills)

    def set_skills(self, skills: list[SkillConfig]):
        """Update active skills and recompute cached narration injection."""
        self.active_skills = skills
        if self._skill_loader:
            self._narration_injection = self._skill_loader.build_injection("narration", skills)
        else:
            self._narration_injection = ""

    async def advance_phase(
        self, state: GameState, agents: dict[str, CharacterAgent]
    ) -> tuple[GameState, str]:
        """Advance to the next phase and generate narration.

        Returns (updated state, narration text).
        """
        current = state.phase

        if current == "lobby":
            state = game_state.advance_to_discussion(state)
            narration = await self._generate_narration(state, "game_start", {
                "num_players": len(game_state.get_alive_characters(state)),
            })
        elif current == "discussion":
            state = game_state.advance_to_voting(state)
            narration = await self._generate_narration(state, "voting_start", {})
            session_warnings = self._discussion_warning_sent.get(state.session_id, {})
            session_warnings.pop(state.round, None)
        elif current == "voting":
            state = game_state.advance_to_reveal(state)
            narration = ""  # Narration comes after vote tally
        elif current == "reveal":
            winner = self._check_win_conditions(state)
            if winner:
                state = game_state.end_game(state, winner)
                # Determine which template to use
                evil_factions = {
                    f.get("name", "")
                    for f in state.world.factions
                    if f.get("alignment", "").lower() == "evil"
                }
                if winner in evil_factions:
                    template_key = "game_end_evil"
                else:
                    template_key = "game_end_good"
                narration = await self._generate_narration(state, template_key, {
                    "faction": winner,
                })
            else:
                state = game_state.advance_to_night(state)
                narration = await self._generate_narration(state, "night_start", {})
        elif current == "night":
            # Generate a summary of the previous round's discussion
            summary = await self._generate_discussion_summary(state)
            state = game_state.advance_to_discussion(state)
            narration = await self._generate_narration(state, "discussion_start", {
                "round": state.round,
                "summary_of_discussion": summary + " " if summary else "",
            })
        else:
            narration = ""

        return state, narration

    def _check_win_conditions(self, state: GameState) -> str | None:
        """Check if any faction has won.

        Good wins: all evil eliminated.
        Evil wins: evil > good among alive players (majority, not parity).
        Round cap: after round 6, faction with more members wins (ties go to good).
        Returns winning faction name or None.
        """
        alive = game_state.get_alive_characters(state)
        player_alive = state.player_role and not state.player_role.is_eliminated
        if not alive and not player_alive:
            # All players eliminated — evil wins by default (council destroyed)
            evil_factions_check = {
                f.get("name", "")
                for f in state.world.factions
                if f.get("alignment", "").lower() == "evil"
            }
            if evil_factions_check:
                return sorted(evil_factions_check)[0]
            return "draw"

        evil_factions = {
            f.get("name", "")
            for f in state.world.factions
            if f.get("alignment", "").lower() == "evil"
        }
        good_factions = {
            f.get("name", "")
            for f in state.world.factions
            if f.get("alignment", "").lower() in ("good", "neutral")
        }

        evil_alive = [c for c in alive if c.faction in evil_factions]
        good_alive = [c for c in alive if c.faction in good_factions]

        evil_alive_count = len(evil_alive)
        good_alive_count = len(good_alive)

        # Count player in faction tallies
        if state.player_role and not state.player_role.is_eliminated:
            if state.player_role.faction in evil_factions:
                evil_alive_count += 1
            else:
                good_alive_count += 1

        # All evil eliminated -> good wins
        if evil_alive_count == 0 and good_factions:
            return sorted(good_factions)[0]

        # Evil > good -> evil wins (majority, not parity)
        if evil_factions and evil_alive_count > good_alive_count:
            return sorted(evil_factions)[0]

        # Round cap: after round 6, resolve by numbers (ties go to good)
        if state.round >= 6:
            if evil_alive_count > good_alive_count:
                return sorted(evil_factions)[0]
            else:
                # Tied or good has more — good wins (defender's advantage)
                return sorted(good_factions)[0] if good_factions else None

        return None

    async def handle_voting(
        self,
        state: GameState,
        player_vote_target_id: str,
        agents: dict[str, CharacterAgent],
    ) -> tuple[GameState, VoteResult]:
        """Collect player vote, trigger AI votes in parallel, tally, determine eliminated."""
        alive = game_state.get_alive_characters(state)
        alive_public = [
            CharacterPublicInfo(
                id=c.id, name=c.name, persona=c.persona,
                speaking_style=c.speaking_style, avatar_seed=c.avatar_seed,
                public_role=c.public_role, voice_id=c.voice_id,
                is_eliminated=c.is_eliminated,
            )
            for c in alive
        ]

        # Include the player as a votable target for AI agents
        player_is_alive = state.player_role and not state.player_role.is_eliminated
        if player_is_alive:
            alive_public.append(CharacterPublicInfo(
                id="player", name="You (Council Member)", persona="A council member",
                public_role="Council Member", voice_id="",
                is_eliminated=False,
            ))

        votes: list[VoteRecord] = []

        # Player vote (only if alive)
        if player_is_alive:
            target_char = next((c for c in alive if c.id == player_vote_target_id), None)
            if target_char:
                votes.append(VoteRecord(
                    voter_id="player",
                    voter_name="You",
                    target_id=player_vote_target_id,
                    target_name=target_char.name,
                ))

        # AI votes — collect in parallel for faster response
        async def _get_vote(char, agent):
            try:
                target_id = await agent.vote(alive_public)
                target = next((c for c in alive if c.id == target_id), None)
                if target:
                    return VoteRecord(
                        voter_id=char.id, voter_name=char.name,
                        target_id=target_id, target_name=target.name,
                    )
            except Exception as e:
                logger.warning("Vote failed for %s: %s", char.name, e)
            return None

        vote_tasks = []
        for char in alive:
            agent = agents.get(char.id)
            if agent and not char.is_eliminated:
                vote_tasks.append(_get_vote(char, agent))

        if vote_tasks:
            results = await asyncio.gather(*vote_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, VoteRecord):
                    votes.append(result)

        # Tally
        tally: dict[str, int] = {}
        for v in votes:
            tally[v.target_id] = tally.get(v.target_id, 0) + 1

        state.votes = votes

        # Determine elimination
        if not tally:
            result = VoteResult(votes=votes, tally=tally, is_tie=True)
            state.vote_results.append(result)
            return state, result

        max_votes = max(tally.values())
        top = [tid for tid, count in tally.items() if count == max_votes]

        if len(top) > 1:
            # Tie
            result = VoteResult(votes=votes, tally=tally, is_tie=True)
            state.vote_results.append(result)
            return state, result

        eliminated_id = top[0]
        eliminated_char = next((c for c in alive if c.id == eliminated_id), None)
        eliminated_name = eliminated_char.name if eliminated_char else "Unknown"

        state = game_state.eliminate_character(state, eliminated_id)

        result = VoteResult(
            votes=votes,
            tally=tally,
            eliminated_id=eliminated_id,
            eliminated_name=eliminated_name,
            is_tie=False,
        )
        state.vote_results.append(result)

        return state, result

    def _get_talk_modifier(self, state: GameState, char_id: str) -> str:
        """Return a game-state-aware prompt modifier for a character."""
        round_msgs = [m for m in state.messages if m.round == state.round]
        char_count = sum(1 for m in round_msgs if m.speaker_id == char_id)
        alive_count = max(len(game_state.get_alive_characters(state)), 1)
        avg = len(round_msgs) / alive_count

        # Find the character object and their agent info
        char = next((c for c in state.characters if c.id == char_id), None)
        char_name_lower = char.name.lower() if char else ""

        # Check recent accusations in messages
        accusation_patterns = {"suspect", "suspicious", "accuse", "liar", "lying", "traitor", "blame", "guilty", "vote out", "eliminate"}
        recent_msgs = round_msgs[-8:]
        recent_text_lower = " ".join(m.content.lower() for m in recent_msgs)

        # Is this character accused?
        char_is_accused = char_name_lower and any(
            char_name_lower in m.content.lower() and any(kw in m.content.lower() for kw in accusation_patterns)
            for m in recent_msgs if m.speaker_id != char_id
        )

        # Is an ally of this character accused? (check if char is evil and ally is accused)
        ally_accused = False
        if char and char.faction:
            evil_factions = {
                f.get("name", "")
                for f in state.world.factions
                if f.get("alignment", "").lower() == "evil"
            }
            if char.faction in evil_factions:
                allies = [c for c in state.characters if c.faction == char.faction and c.id != char_id and not c.is_eliminated]
                for ally in allies:
                    ally_name_lower = ally.name.lower()
                    if any(
                        ally_name_lower in m.content.lower() and any(kw in m.content.lower() for kw in accusation_patterns)
                        for m in recent_msgs if m.speaker_id != ally.id
                    ):
                        ally_accused = True
                        break

        # Check if discussion is stalling (no accusations in recent messages)
        has_accusations = any(kw in recent_text_lower for kw in accusation_patterns)
        discussion_stalling = len(round_msgs) > 6 and not has_accusations

        # Build modifier
        if char_is_accused:
            return "You are under suspicion. Defend yourself with specific evidence."
        elif ally_accused:
            return "Be careful not to defend them too obviously."
        elif discussion_stalling:
            return "Take a stand — accuse or defend someone specifically."
        elif char_count < avg * 0.5:
            return "You haven't spoken much this round. Share your thoughts."
        elif char_count > avg * 1.5:
            return "You've been vocal. Keep responses brief."
        return "React to the discussion. Reference specific claims made by other characters by name."

    async def select_responders(
        self,
        state: GameState,
        message: str,
        target_id: str | None,
        agents: dict[str, CharacterAgent],
    ) -> list[str]:
        """Decide which characters should respond to a player message."""
        alive = game_state.get_alive_characters(state)

        # If a specific target was addressed, they always respond
        if target_id and target_id in agents:
            char = next((c for c in alive if c.id == target_id), None)
            if char and not char.is_eliminated:
                # Also pick 1-2 more to react
                others = [c for c in alive if c.id != target_id]
                extra_ids = await self._pick_responders(state, message, others)
                return [target_id] + extra_ids[:2]

        # General message: let LLM pick 2-3 responders
        return await self._pick_responders(state, message, alive)

    async def handle_night(
        self,
        state: GameState,
        agents: dict[str, CharacterAgent],
        player_action: NightAction | None = None,
    ) -> tuple[GameState, str]:
        """Execute the night phase: collect actions, resolve conflicts, apply results.

        Rounds 1-2: Investigation only — no kills, no protections needed.
        Round 3+: Full powers — kills, protections, investigations.

        Args:
            player_action: Optional night action from the human player.
        Returns (updated state, night narration).
        """
        is_early_round = state.round < EARLY_ROUND_THRESHOLD  # Rounds 1-2: investigation only

        alive = game_state.get_alive_characters(state)
        alive_public = [
            CharacterPublicInfo(
                id=c.id, name=c.name, persona=c.persona,
                speaking_style=c.speaking_style, avatar_seed=c.avatar_seed,
                public_role=c.public_role, voice_id=c.voice_id,
                is_eliminated=c.is_eliminated,
            )
            for c in alive
        ]

        # Include player as targetable if alive
        player_is_alive = state.player_role and not state.player_role.is_eliminated
        if player_is_alive:
            alive_public.append(CharacterPublicInfo(
                id="player", name="You (Council Member)", persona="A council member",
                public_role="Council Member", voice_id="",
                is_eliminated=False,
            ))

        # Determine evil factions
        evil_factions = {
            f.get("name", "")
            for f in state.world.factions
            if f.get("alignment", "").lower() == "evil"
        }

        # Check if player is an evil ally — evil AI should not target player
        player_is_evil_ally = (
            player_is_alive
            and state.player_role
            and state.player_role.faction in evil_factions
        )

        # Collect night actions from eligible AI characters in parallel
        async def get_action(char, agent):
            extra_instructions = ""
            if player_is_evil_ally and char.faction in evil_factions:
                extra_instructions = " Do NOT target 'player' — they are your ally."
            if char.faction in evil_factions:
                if is_early_round:
                    # Early rounds: evil discusses but cannot kill
                    return NightAction(character_id=char.id, action_type="none",
                                       result="Powers not yet active")
                role_actions = "You are evil. Choose a target to KILL tonight." + extra_instructions
                return await agent.night_action(alive_public, role_actions)
            elif "seer" in char.hidden_role.lower() or "investigat" in char.hidden_role.lower():
                # Seer can always investigate
                role_actions = "You are the Seer. Choose a target to INVESTIGATE tonight."
                return await agent.night_action(alive_public, role_actions)
            elif "doctor" in char.hidden_role.lower() or "protect" in char.hidden_role.lower():
                if is_early_round:
                    # Early rounds: Doctor can practice-protect (no kills to block)
                    role_actions = "You are the Doctor. Choose a target to PROTECT tonight. (No kills are possible yet — this is practice.)"
                    return await agent.night_action(alive_public, role_actions)
                role_actions = "You are the Doctor. Choose a target to PROTECT tonight."
                return await agent.night_action(alive_public, role_actions)
            return NightAction(character_id=char.id, action_type="none")

        tasks = []
        action_chars = []
        for char in alive:
            agent = agents.get(char.id)
            if agent:
                tasks.append(get_action(char, agent))
                action_chars.append(char)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        night_actions: list[NightAction] = []
        for i, result in enumerate(results):
            if isinstance(result, NightAction):
                night_actions.append(result)

        # Include player's night action if provided
        # But block kill actions in early rounds
        if player_action:
            if is_early_round and player_action.action_type == "kill":
                player_action.action_type = "none"
                player_action.result = "Powers not yet active"
            night_actions.append(player_action)

        state.night_actions = night_actions

        # Resolve conflicts: kill vs protect
        kill_targets = set()
        protect_targets = set()
        investigate_actions = []

        for action in night_actions:
            if action.action_type == "kill" and action.target_id:
                kill_targets.add(action.target_id)
            elif action.action_type == "protect" and action.target_id:
                protect_targets.add(action.target_id)
            elif action.action_type == "investigate" and action.target_id:
                investigate_actions.append(action)

        # Apply results
        killed_chars = []
        player_killed = False
        protected = False
        for target_id in kill_targets:
            if target_id in protect_targets:
                protected = True
                for action in night_actions:
                    if action.action_type == "kill" and action.target_id == target_id:
                        action.result = "protected"
                    if action.action_type == "protect" and action.target_id == target_id:
                        action.result = "saved"
            else:
                state = game_state.eliminate_character(state, target_id)
                if target_id == "player" and state.player_role:
                    state.player_role.eliminated_by = "night_kill"
                    player_killed = True
                else:
                    target_char = next((c for c in state.characters if c.id == target_id), None)
                    if target_char:
                        killed_chars.append(target_char)
                for action in night_actions:
                    if action.action_type == "kill" and action.target_id == target_id:
                        action.result = "killed"

        # Handle investigations
        investigation_result = None
        for action in investigate_actions:
            if action.target_id == "player" and state.player_role:
                action.result = f"Investigated: You (Council Member) is {state.player_role.faction}"
            else:
                target_char = next((c for c in state.characters if c.id == action.target_id), None)
                if target_char:
                    action.result = f"Investigated: {target_char.name} is {target_char.faction}"
            # If this was the player's investigation, capture the result
            if action.character_id == "player" and action.target_id:
                if action.target_id == "player":
                    investigation_result = {"name": "You", "faction": state.player_role.faction if state.player_role else "Unknown"}
                else:
                    tc = next((c for c in state.characters if c.id == action.target_id), None)
                    if tc:
                        investigation_result = {"name": tc.name, "faction": tc.faction}

        # Store investigation result on state for SSE emission
        state.player_investigation_result = investigation_result
        state.player_killed_at_night = player_killed

        # Generate night narration
        if is_early_round:
            # Early rounds: narrative anomaly instead of kills
            narration = await self._generate_narration(state, "night_investigation", {
                "round": state.round,
            })
        elif killed_chars or player_killed:
            if killed_chars:
                char = killed_chars[0]
                narration = await self._generate_narration(state, "night_kill", {
                    "target_name": char.name,
                    "target_role": char.hidden_role,
                })
            else:
                narration = await self._generate_narration(state, "night_kill", {
                    "target_name": "a council member",
                    "target_role": "unknown",
                })
        elif protected:
            narration = await self._generate_narration(state, "night_protected", {})
        else:
            narration = await self._generate_narration(state, "night_results", {
                "summary": "The night passed quietly. No one was harmed.",
            })

        return state, narration

    # ── Discussion limits ───────────────────────────────────────────

    def check_discussion_limit(self, state: GameState) -> str | None:
        """Check if discussion has hit soft or hard limit.

        Returns:
            - "warning" if soft limit reached and warning not yet sent
            - "end" if hard limit reached and should auto-transition to vote
            - None if within limits
        """
        round_msgs = [m for m in state.messages if m.round == state.round]
        alive_count = max(len(game_state.get_alive_characters(state)), 1)
        total_msgs = len(round_msgs)

        soft_limit = int(alive_count * self.DISCUSSION_SOFT_LIMIT_PER_PLAYER)
        hard_limit = soft_limit + self.DISCUSSION_HARD_LIMIT_EXTRA

        session_warnings = self._discussion_warning_sent.setdefault(state.session_id, {})

        if total_msgs >= hard_limit and session_warnings.get(state.round, False):
            return "end"
        if total_msgs >= soft_limit and not session_warnings.get(state.round, False):
            session_warnings[state.round] = True
            return "warning"
        return None

    # ── Discussion summary ───────────────────────────────────────────

    async def _generate_discussion_summary(self, state: GameState) -> str:
        """Generate a 1-2 sentence summary of the current round's discussion."""
        round_msgs = [m for m in state.messages if m.round == state.round and m.is_public]
        if not round_msgs:
            return ""

        msgs_text = "\n".join(
            f"[{m.speaker_name}]: {m.content}" for m in round_msgs[-20:]
        )

        try:
            response = await asyncio.wait_for(
                self._mistral.chat.complete_async(
                    model="mistral-small-latest",
                    messages=[
                        {"role": "system", "content": DISCUSSION_SUMMARY_SYSTEM},
                        {"role": "user", "content": f"Summarize this discussion:\n\n{msgs_text}"},
                    ],
                    temperature=0.3,
                ),
                timeout=8.0,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return ""

    async def _pick_responders(
        self, state: GameState, message: str, candidates: list
    ) -> list[str]:
        """Use Mistral to pick which characters should respond."""
        if not candidates:
            return []

        chars_desc = ", ".join(
            f"{c.name} (id: {c.id}, role: {c.public_role})"
            for c in candidates
        )

        try:
            response = await asyncio.wait_for(
                self._mistral.chat.complete_async(
                    model="mistral-large-latest",
                    messages=[
                        {
                            "role": "system",
                            "content": RESPONDER_SELECTION_SYSTEM.format(characters=chars_desc),
                        },
                        {
                            "role": "user",
                            "content": f"Player says: {message}\n\nWhich characters should respond?",
                        },
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                ),
                timeout=10.0,
            )
            data = json.loads(response.choices[0].message.content)
            responder_ids = data.get("responders", [])
            valid_ids = {c.id for c in candidates}
            return [rid for rid in responder_ids if rid in valid_ids][:3]
        except asyncio.TimeoutError:
            logger.warning("Responder selection timed out, using fallback")
            return [c.id for c in candidates[:2]]
        except Exception:
            return [c.id for c in candidates[:2]]

    # ── Tension & complication management ────────────────────────────

    def update_tension(self, state: GameState) -> GameState:
        """Update tension level based on game progression."""
        alive = game_state.get_alive_characters(state)
        total = len(state.characters)
        alive_count = len(alive)

        # Base tension rises as more players are eliminated
        elimination_ratio = 1.0 - (alive_count / max(total, 1))
        round_factor = min(state.round / 6.0, 1.0)  # Rises over 6 rounds

        state.tension_level = min(1.0, 0.2 + elimination_ratio * 0.4 + round_factor * 0.3)

        # Spike tension after night kills
        recent_kills = [a for a in state.night_actions if a.result == "killed"]
        if recent_kills:
            state.tension_level = min(1.0, state.tension_level + 0.15)

        return state

    def should_inject_complication(self, state: GameState) -> bool:
        """Determine if discussion is stalling and needs a complication."""
        round_msgs = [m for m in state.messages if m.round == state.round]
        if len(round_msgs) < 6:
            return False  # Too early in discussion

        # Check if recent messages are repetitive (low info content)
        recent = round_msgs[-4:]
        unique_speakers = len({m.speaker_id for m in recent})
        if unique_speakers <= 1:
            return True  # Only one person talking — stalling

        # Check if no accusations in recent messages
        accusation_kw = {"suspect", "traitor", "lying", "accuse", "vote", "eliminate"}
        recent_text = " ".join(m.content.lower() for m in recent)
        has_accusations = any(kw in recent_text for kw in accusation_kw)
        if not has_accusations and len(round_msgs) > 8:
            return True  # Lots of discussion but no one making moves

        # Random chance increases with round number
        if random.random() < min(0.1 * state.round, 0.5):
            return True

        return False

    async def inject_complication(self, state: GameState) -> tuple[GameState, str]:
        """Generate and inject a dynamic complication into the game."""
        comp_type = random.choice(list(COMPLICATION_TYPES.keys()))
        comp_desc = COMPLICATION_TYPES[comp_type]

        event = GameEvent(
            event_type=comp_type,
            description=comp_desc,
            round=state.round,
            injected_at_message=len(state.messages),
        )
        state.game_events.append(event)

        # Boost tension on complication
        state.tension_level = min(1.0, state.tension_level + 0.1)

        # Generate dramatic narration for the complication
        narration = await self._generate_narration(state, "complication", {
            "complication_type": comp_type,
            "description": comp_desc,
        })

        return state, narration

    # ── Narration ─────────────────────────────────────────────────────

    async def _generate_narration(
        self, state: GameState, event_type: str, extra: dict
    ) -> str:
        """Generate dramatic narration via Mistral Large 3 with timeout."""
        template = NARRATION_TEMPLATES.get(event_type, "Something happens in the game.")
        try:
            event_text = template.format(**extra)
        except (KeyError, IndexError):
            event_text = template

        # Add tension context to narration
        tension_hint = ""
        if state.tension_level > 0.7:
            tension_hint = " The atmosphere is electric with suspicion and dread."
        elif state.tension_level > 0.4:
            tension_hint = " Tension hangs thick in the air."

        system = NARRATION_SYSTEM.format(
            world_title=state.world.title,
            setting=state.world.setting,
            flavor_text=state.world.flavor_text,
        )

        if self._narration_injection:
            system += "\n\n" + self._narration_injection

        try:
            response = await asyncio.wait_for(
                self._mistral.chat.complete_async(
                    model="mistral-large-latest",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": event_text + tension_hint},
                    ],
                    temperature=0.7,
                ),
                timeout=15.0,
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            logger.warning("Narration generation timed out for %s", event_type)
            return event_text
        except Exception:
            return event_text
