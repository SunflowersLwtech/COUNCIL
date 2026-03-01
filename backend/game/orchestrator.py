"""GameOrchestrator — manages game sessions with in-memory state + Redis persistence."""

import json
import logging
import random
import asyncio
from typing import AsyncGenerator

from backend.models.game_models import (
    GameState, GameCreateResponse, CharacterPublicInfo,
    ChatMessage, VoteResult, NightAction, PlayerRole,
)
from backend.game.document_engine import DocumentEngine
from backend.game.character_factory import CharacterFactory
from backend.game.character_agent import CharacterAgent
from backend.game.game_master import GameMaster, EARLY_ROUND_THRESHOLD
from backend.game.skill_loader import SkillLoader, SkillConfig
from backend.game import state as game_state
from backend.game.persistence import PersistenceManager
from backend.voice.tts_middleware import inject_emotion_tags

logger = logging.getLogger(__name__)

# Base probability for spontaneous NPC reactions
BASE_REACTION_PROB = 0.25


class GameOrchestrator:
    """Manages game sessions and coordinates document engine, characters, and game master."""

    def __init__(self, persistence: PersistenceManager | None = None):
        self.doc_engine = DocumentEngine()
        self.char_factory = CharacterFactory()
        self.skill_loader = SkillLoader()
        self.game_master = GameMaster(skill_loader=self.skill_loader)
        self.persistence = persistence
        # In-memory session storage
        self._sessions: dict[str, GameState] = {}
        self._agents: dict[str, dict[str, CharacterAgent]] = {}  # session_id -> {char_id -> agent}
        # Background tasks for fire-and-forget emotion updates
        self._bg_tasks: set[asyncio.Task] = set()

    async def _get_session(self, session_id: str) -> GameState:
        # 1. Check in-memory cache
        state = self._sessions.get(session_id)
        if state:
            return state

        # 2. Try loading from Redis
        if self.persistence and self.persistence.available:
            loaded = await self.persistence.load_game_state(session_id)
            if loaded:
                state_dict, agent_memory = loaded
                try:
                    state = GameState.model_validate(state_dict)
                    self._sessions[session_id] = state
                    self._reconstruct_agents(session_id, state, agent_memory)
                    logger.info("Session %s restored from Redis", session_id)
                    return state
                except Exception as exc:
                    logger.warning("Failed to restore session %s: %s", session_id, exc)

        raise ValueError(f"Session {session_id} not found")

    def _extract_agent_memory(self, session_id: str) -> dict:
        """Extract serialisable memory from all agents for a session."""
        agents = self._agents.get(session_id, {})
        memory = {}
        for char_id, agent in agents.items():
            memory[char_id] = {
                "conversation_history": agent._conversation_history,
                "round_memory": agent._round_memory,
            }
        return memory

    def _resolve_session_skills(self, state: GameState) -> list[SkillConfig]:
        """Resolve active skills for a game session."""
        skill_ids = state.active_skills
        if not skill_ids:
            return []
        try:
            return self.skill_loader.resolve_skills(skill_ids)
        except ValueError as exc:
            logger.warning("Skill resolution failed: %s", exc)
            return []

    def _reconstruct_agents(
        self, session_id: str, state: GameState, agent_memory: dict
    ):
        """Rebuild CharacterAgent instances from GameState and restore their memory."""
        skills = self._resolve_session_skills(state)
        evil_factions = {
            f.get("name", "")
            for f in state.world.factions
            if f.get("alignment", "").lower() == "evil"
        }
        agents: dict[str, CharacterAgent] = {}
        for char in state.characters:
            agent = CharacterAgent(
                char, state.world,
                active_skills=skills,
                skill_loader=self.skill_loader,
                evil_factions=evil_factions,
                canon_facts=state.canon_facts,
            )
            mem = agent_memory.get(char.id, {})
            agent._conversation_history = mem.get("conversation_history", [])
            agent._round_memory = mem.get("round_memory", [])
            agents[char.id] = agent
        self._agents[session_id] = agents
        # Update game master with skills too
        self.game_master.set_skills(skills)

    async def _save_session(self, session_id: str):
        """Persist current session state + agent memory to Redis."""
        if not self.persistence or not self.persistence.available:
            return
        state = self._sessions.get(session_id)
        if not state:
            return
        agent_memory = self._extract_agent_memory(session_id)
        await self.persistence.save_game_state(
            session_id, state.model_dump(mode="json"), agent_memory
        )

    def _get_agents(self, session_id: str) -> dict[str, CharacterAgent]:
        return self._agents.get(session_id, {})

    def _public_state(self, state: GameState, full: bool = False) -> dict:
        """Build public projection of game state (no hidden info).

        Args:
            full: If True, return all messages (for session recovery).
                  If False, return only the last 50 messages.
        """
        chars = [
            CharacterPublicInfo(
                id=c.id, name=c.name, persona=c.persona,
                speaking_style=c.speaking_style, avatar_seed=c.avatar_seed,
                public_role=c.public_role, voice_id=c.voice_id,
                is_eliminated=c.is_eliminated,
            )
            for c in state.characters
        ]
        messages = state.messages if full else state.messages[-50:]
        result = {
            "session_id": state.session_id,
            "phase": state.phase,
            "round": state.round,
            "world_title": state.world.title,
            "world_setting": state.world.setting,
            "flavor_text": state.world.flavor_text,
            "characters": [c.model_dump() for c in chars],
            "eliminated": state.eliminated,
            "messages": [m.model_dump() for m in messages],
            "vote_results": [vr.model_dump() for vr in state.vote_results],
            "winner": state.winner,
        }
        # Include player role info (safe — only player's own data)
        if state.player_role:
            pr = state.player_role
            ally_details = []
            for aid in pr.allies:
                achar = next((c for c in state.characters if c.id == aid), None)
                if achar and not achar.is_eliminated:
                    ally_details.append({"id": aid, "name": achar.name})
            result["player_role"] = {
                "hidden_role": pr.hidden_role,
                "faction": pr.faction,
                "win_condition": pr.win_condition,
                "allies": ally_details,
                "is_eliminated": pr.is_eliminated,
                "eliminated_by": pr.eliminated_by,
            }

        # Include pending night action prompt for session recovery
        if full and state.awaiting_player_night_action:
            action_type = self._get_player_night_action_type(state)
            if action_type:
                result["night_action_prompt"] = {
                    "action_type": action_type,
                    "eligible_targets": self._get_eligible_night_targets(state),
                }

        return result

    # ── Session creation ──────────────────────────────────────────────

    async def create_session_from_file(
        self, file_bytes: bytes, filename: str, num_characters: int = 7,
        enabled_skills: list[str] | None = None,
    ) -> GameCreateResponse:
        """Create a game from an uploaded document."""
        world = await self.doc_engine.process_document(file_bytes, filename)
        return await self._finalize_session(world, num_characters, enabled_skills)

    async def create_session_from_text(
        self, text: str, num_characters: int = 7,
        enabled_skills: list[str] | None = None,
    ) -> GameCreateResponse:
        """Create a game from raw text."""
        world = await self.doc_engine.process_text(text)
        return await self._finalize_session(world, num_characters, enabled_skills)

    async def create_session_from_scenario(
        self, scenario_id: str, num_characters: int = 7,
        enabled_skills: list[str] | None = None,
    ) -> GameCreateResponse:
        """Create a game from a pre-built scenario."""
        world = await self.doc_engine.load_scenario(scenario_id)
        return await self._finalize_session(world, num_characters, enabled_skills)

    async def _finalize_session(
        self, world, num_characters: int,
        enabled_skills: list[str] | None = None,
    ) -> GameCreateResponse:
        """Generate characters, create agents, store session."""
        characters = await self.char_factory.generate_characters(world, num_characters)

        # Resolve skills — use all available skills by default
        skill_ids = enabled_skills if enabled_skills is not None else self.skill_loader.all_skill_ids()
        try:
            active_skills = self.skill_loader.resolve_skills(skill_ids)
        except ValueError as exc:
            logger.warning("Skill resolution failed, starting without skills: %s", exc)
            active_skills = []

        state = GameState(
            world=world,
            characters=characters,
            active_skills=[s.id for s in active_skills],
        )

        # Establish canon facts from world setup
        state.canon_facts.append(f"World: {world.title}")
        state.canon_facts.append(f"Setting: {world.setting}")
        for faction in world.factions:
            state.canon_facts.append(f"Faction '{faction.get('name', '?')}' is {faction.get('alignment', '?')}")
        for char in characters:
            state.canon_facts.append(f"{char.name} is publicly known as {char.public_role}")

        # ── Assign player a hidden role ──────────────────────────────
        player_role = self._assign_player_role(state, world, characters)
        state.player_role = player_role
        state.canon_facts.append("You (the player) are publicly known as a Council Member")

        self._sessions[state.session_id] = state

        # Update game master with active skills
        self.game_master.set_skills(active_skills)

        # Compute evil factions once for all agents
        evil_factions = {
            f.get("name", "")
            for f in world.factions
            if f.get("alignment", "").lower() == "evil"
        }

        # Create character agents with active skills and faction-aware injection
        agents = {}
        for char in characters:
            agent = CharacterAgent(
                char, world,
                active_skills=active_skills,
                skill_loader=self.skill_loader,
                evil_factions=evil_factions,
                canon_facts=state.canon_facts,
            )
            # If player is evil, inform evil AI allies about the player
            if player_role and player_role.faction == char.faction:
                if char.faction in evil_factions:
                    ally_note = (
                        f"The player (You) is secretly your ally — "
                        f"they are a {player_role.hidden_role} of the {player_role.faction}. "
                        f"Do NOT target the player during night actions."
                    )
                    char.hidden_knowledge.append(ally_note)
                    # Rebuild agent prompt to include the new knowledge
                    agent = CharacterAgent(
                        char, world,
                        active_skills=active_skills,
                        skill_loader=self.skill_loader,
                        evil_factions=evil_factions,
                        canon_facts=state.canon_facts,
                    )
            agents[char.id] = agent
        self._agents[state.session_id] = agents

        chars_public = [
            CharacterPublicInfo(
                id=c.id, name=c.name, persona=c.persona,
                speaking_style=c.speaking_style, avatar_seed=c.avatar_seed,
                public_role=c.public_role, voice_id=c.voice_id,
                is_eliminated=c.is_eliminated,
            )
            for c in characters
        ]

        await self._save_session(state.session_id)

        return GameCreateResponse(
            session_id=state.session_id,
            world_title=world.title,
            world_setting=world.setting,
            characters=chars_public,
            phase=state.phase,
        )

    def _assign_player_role(self, state: GameState, world, characters) -> PlayerRole:
        """Assign the player a hidden role from the world's role pool."""
        evil_factions = {
            f.get("name", "")
            for f in world.factions
            if f.get("alignment", "").lower() == "evil"
        }
        good_factions = {
            f.get("name", "")
            for f in world.factions
            if f.get("alignment", "").lower() in ("good", "neutral")
        }

        # Count existing faction distribution
        evil_count = sum(1 for c in characters if c.faction in evil_factions)
        good_count = sum(1 for c in characters if c.faction in good_factions)
        total = evil_count + good_count + 1  # +1 for player

        # Target ~1/3 evil. If evil is under-represented, higher chance for player
        target_evil = max(1, total // 3)
        if evil_count < target_evil:
            player_is_evil = random.random() < 0.6
        else:
            player_is_evil = random.random() < 0.15

        # Pick faction
        if player_is_evil and evil_factions:
            player_faction = random.choice(list(evil_factions))
        elif good_factions:
            player_faction = random.choice(list(good_factions))
        else:
            player_faction = evil_factions.pop() if evil_factions else "Unknown"

        # Pick a role from world.roles matching the faction
        matching_roles = [
            r for r in world.roles
            if r.get("faction", r.get("alignment", "")).lower() == player_faction.lower()
            or (player_is_evil and r.get("alignment", "").lower() == "evil")
            or (not player_is_evil and r.get("alignment", "").lower() in ("good", "neutral"))
        ]
        if matching_roles:
            role_info = random.choice(matching_roles)
            role_name = role_info.get("name", "Villager")
        else:
            # Fallback: assign based on faction
            if player_is_evil:
                role_name = "Werewolf"
            else:
                role_options = ["Villager", "Seer", "Doctor"]
                # Avoid duplicate special roles
                existing_roles = {c.hidden_role.lower() for c in characters}
                available = [r for r in role_options if r.lower() not in existing_roles]
                role_name = random.choice(available) if available else "Villager"

        # Find win condition
        win_conditions = {
            wc.get("faction", wc.get("name", "")): wc.get("condition", wc.get("description", ""))
            for wc in world.win_conditions
        }
        win_condition = win_conditions.get(player_faction, "Survive and help your faction win")

        # If player is evil, populate allies
        allies = []
        if player_is_evil:
            allies = [c.id for c in characters if c.faction in evil_factions]

        return PlayerRole(
            hidden_role=role_name,
            faction=player_faction,
            win_condition=win_condition,
            allies=allies,
        )

    # ── Game flow ─────────────────────────────────────────────────────

    async def start_game(self, session_id: str) -> dict:
        """Transition from lobby to discussion and return narration."""
        state = await self._get_session(session_id)
        agents = self._get_agents(session_id)
        state, narration = await self.game_master.advance_phase(state, agents)
        self._sessions[session_id] = state
        await self._save_session(session_id)

        return {
            "phase": state.phase,
            "round": state.round,
            "narration": narration,
            "has_player_role": state.player_role is not None,
        }

    async def handle_chat(
        self, session_id: str, message: str, target_character_id: str | None = None
    ) -> AsyncGenerator[str, None]:
        """Handle a player chat message. Yields SSE event strings."""
        state = await self._get_session(session_id)
        agents = self._get_agents(session_id)

        if state.phase != "discussion":
            yield f"data: {json.dumps({'type': 'error', 'error': 'Chat only available during discussion phase'})}\n\n"
            return

        # Ghost mode: eliminated player cannot chat
        if state.player_role and state.player_role.is_eliminated:
            yield f"data: {json.dumps({'type': 'error', 'error': 'You have been eliminated. Spectating in ghost mode.'})}\n\n"
            return

        # Record player message
        player_msg = ChatMessage(
            speaker_id="player",
            speaker_name="You",
            content=message,
            is_public=True,
            phase=state.phase,
            round=state.round,
        )
        state.messages.append(player_msg)

        # Select which characters respond
        responder_ids = await self.game_master.select_responders(
            state, message, target_character_id, agents
        )

        yield f"data: {json.dumps({'type': 'responders', 'character_ids': responder_ids})}\n\n"

        # Update emotions on all alive characters (fire-and-forget to avoid blocking SSE stream)
        emotion_tasks = []
        for char in game_state.get_alive_characters(state):
            agent = agents.get(char.id)
            if agent:
                emotion_tasks.append(agent.update_emotions_llm(message, "player"))
        if emotion_tasks:
            task = asyncio.ensure_future(
                asyncio.gather(*emotion_tasks, return_exceptions=True)
            )
            self._bg_tasks.add(task)
            task.add_done_callback(self._bg_tasks.discard)

        for i, char_id in enumerate(responder_ids):
            agent = agents.get(char_id)
            if not agent:
                continue

            # Staggered timing between responses
            if i > 0:
                await asyncio.sleep(random.uniform(1.5, 4.0))

            char = agent.character
            yield f"data: {json.dumps({'type': 'thinking', 'character_id': char_id, 'character_name': char.name})}\n\n"

            try:
                talk_modifier = self.game_master._get_talk_modifier(state, char_id)

                # Stream response token-by-token via SSE
                yield f"data: {json.dumps({'type': 'stream_start', 'character_id': char_id, 'character_name': char.name})}\n\n"

                full_response = ""
                try:
                    async for chunk in agent.respond_stream(message, state.messages, talk_modifier=talk_modifier):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'stream_delta', 'character_id': char_id, 'delta': chunk})}\n\n"
                        await asyncio.sleep(0)  # yield control so ASGI flushes each SSE event
                except Exception:
                    if not full_response:
                        full_response = agent._get_fallback_response()

                response = getattr(agent, '_last_response', None) or full_response

                ai_msg = ChatMessage(
                    speaker_id=char_id,
                    speaker_name=char.name,
                    content=response,
                    is_public=True,
                    phase=state.phase,
                    round=state.round,
                )
                state.messages.append(ai_msg)

                # Fire-and-forget emotion updates: stagger delay absorbs execution time
                ai_emotion_tasks = []
                for other_char in game_state.get_alive_characters(state):
                    other_agent = agents.get(other_char.id)
                    if other_agent and other_char.id != char_id:
                        ai_emotion_tasks.append(other_agent.update_emotions_llm(response, char_id))
                if ai_emotion_tasks:
                    task = asyncio.ensure_future(
                        asyncio.gather(*ai_emotion_tasks, return_exceptions=True)
                    )
                    self._bg_tasks.add(task)

                    def _bg_task_done(t: asyncio.Task):
                        self._bg_tasks.discard(t)
                        if not t.cancelled():
                            exc = t.exception()
                            if exc:
                                logger.warning("Background emotion task failed: %s", exc)

                    task.add_done_callback(_bg_task_done)

                # Emit stream_end with complete data for TTS
                tts_text = inject_emotion_tags(response, char.emotional_state)
                dominant_emotion = agent.get_dominant_emotion()
                yield f"data: {json.dumps({'type': 'stream_end', 'character_id': char_id, 'character_name': char.name, 'content': response, 'tts_text': tts_text, 'voice_id': char.voice_id, 'emotion': dominant_emotion})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'character_id': char_id, 'error': str(e)})}\n\n"

        # Spontaneous reactions: probability based on emotional state (anger boosts it)
        if len(state.messages) >= 4:
            alive = game_state.get_alive_characters(state)
            non_responders = [
                c for c in alive
                if c.id not in responder_ids and c.id in agents
            ]
            reactor = None
            reactor_agent = None
            if non_responders:
                reactor = random.choice(non_responders)
                reactor_agent = agents[reactor.id]
                reaction_prob = BASE_REACTION_PROB + (reactor.emotional_state.anger * 0.3)
                if random.random() >= reaction_prob:
                    reactor = None
                    reactor_agent = None
            if non_responders and reactor_agent:
                try:
                    reaction = await reactor_agent.react(state.messages)
                    if reaction:
                        # Stream reaction via stream_start/delta/end so frontend renders it progressively
                        yield f"data: {json.dumps({'type': 'stream_start', 'character_id': reactor.id, 'character_name': reactor.name})}\n\n"
                        # Emit the text in small word-groups for a streaming effect
                        words = reaction.split(" ")
                        for wi, word in enumerate(words):
                            chunk = word if wi == 0 else " " + word
                            yield f"data: {json.dumps({'type': 'stream_delta', 'character_id': reactor.id, 'delta': chunk})}\n\n"
                            await asyncio.sleep(0.03)
                        react_msg = ChatMessage(
                            speaker_id=reactor.id,
                            speaker_name=reactor.name,
                            content=reaction,
                            is_public=True,
                            phase=state.phase,
                            round=state.round,
                        )
                        state.messages.append(react_msg)
                        tts_reaction = inject_emotion_tags(reaction, reactor.emotional_state)
                        reactor_emotion = reactor_agent.get_dominant_emotion()
                        yield f"data: {json.dumps({'type': 'stream_end', 'character_id': reactor.id, 'character_name': reactor.name, 'content': reaction, 'tts_text': tts_reaction, 'voice_id': reactor.voice_id, 'emotion': reactor_emotion})}\n\n"
                except Exception:
                    pass

        # Update tension level
        state = self.game_master.update_tension(state)

        # Check discussion turn limits
        limit_status = self.game_master.check_discussion_limit(state)
        if limit_status == "warning":
            yield f"data: {json.dumps({'type': 'discussion_warning', 'content': 'The council grows restless. A vote will be called shortly.'})}\n\n"
        elif limit_status == "end":
            yield f"data: {json.dumps({'type': 'discussion_ending', 'content': 'The council has heard enough. The vote will now begin.'})}\n\n"

        # Complication injection: when discussion stalls, inject a dramatic event
        if self.game_master.should_inject_complication(state):
            try:
                state, comp_narration = await self.game_master.inject_complication(state)
                if comp_narration:
                    yield f"data: {json.dumps({'type': 'complication', 'content': comp_narration, 'tension': state.tension_level})}\n\n"
            except Exception as e:
                logger.warning("Complication injection failed: %s", e)

        self._sessions[session_id] = state
        await self._save_session(session_id)
        yield f"data: {json.dumps({'type': 'done', 'tension': state.tension_level})}\n\n"

    async def handle_vote(
        self, session_id: str, target_character_id: str
    ) -> AsyncGenerator[str, None]:
        """Handle player vote. Yields SSE events for voting flow."""
        state = await self._get_session(session_id)
        agents = self._get_agents(session_id)

        # Transition to voting if still in discussion
        if state.phase == "discussion":
            state, narration = await self.game_master.advance_phase(state, agents)
            if narration:
                yield f"data: {json.dumps({'type': 'narration', 'content': narration})}\n\n"

        if state.phase != "voting":
            yield f"data: {json.dumps({'type': 'error', 'error': 'Not in voting phase'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'voting_started'})}\n\n"

        # Process votes
        state, vote_result = await self.game_master.handle_voting(
            state, target_character_id, agents
        )

        # Emit each vote
        for vote in vote_result.votes:
            yield f"data: {json.dumps({'type': 'vote', 'voter_name': vote.voter_name, 'target_name': vote.target_name})}\n\n"

        # Emit tally
        yield f"data: {json.dumps({'type': 'tally', 'tally': vote_result.tally, 'is_tie': vote_result.is_tie})}\n\n"

        # Transition to reveal
        state, _ = await self.game_master.advance_phase(state, agents)

        if vote_result.is_tie:
            narration = await self.game_master._generate_narration(state, "tie_vote", {})
            yield f"data: {json.dumps({'type': 'narration', 'content': narration})}\n\n"
        elif vote_result.eliminated_id:
            # Check if the player was eliminated
            if vote_result.eliminated_id == "player" and state.player_role:
                state.player_role.eliminated_by = "vote"
                state.canon_facts.append(
                    f"The player (Council Member) was eliminated in round {state.round} by vote"
                )

                # Emit player_eliminated with all hidden info for ghost mode
                all_characters = [
                    {
                        "id": c.id, "name": c.name, "hidden_role": c.hidden_role,
                        "faction": c.faction, "is_eliminated": c.is_eliminated,
                        "persona": c.persona, "public_role": c.public_role,
                        "avatar_seed": c.avatar_seed,
                    }
                    for c in state.characters
                ]
                narration = await self.game_master._generate_narration(
                    state, "elimination", {
                        "name": "You (Council Member)",
                        "role": state.player_role.hidden_role,
                        "faction": state.player_role.faction,
                    }
                )
                yield f"data: {json.dumps({'type': 'player_eliminated', 'hidden_role': state.player_role.hidden_role, 'faction': state.player_role.faction, 'eliminated_by': 'vote', 'all_characters': all_characters, 'narration': narration})}\n\n"
                yield f"data: {json.dumps({'type': 'elimination', 'character_id': 'player', 'character_name': 'You', 'hidden_role': state.player_role.hidden_role, 'faction': state.player_role.faction, 'narration': narration})}\n\n"
            else:
                eliminated_char = next(
                    (c for c in state.characters if c.id == vote_result.eliminated_id), None
                )
                if eliminated_char:
                    # Record elimination as canon
                    state.canon_facts.append(
                        f"{eliminated_char.name} was eliminated in round {state.round} "
                        f"(was {eliminated_char.hidden_role} of {eliminated_char.faction})"
                    )

                    # Push updated canon facts to all alive agents
                    for char in game_state.get_alive_characters(state):
                        agent = agents.get(char.id)
                        if agent:
                            agent.update_canon_facts(state.canon_facts)

                    # Update emotions on all alive characters after elimination
                    for char in game_state.get_alive_characters(state):
                        agent = agents.get(char.id)
                        if agent:
                            agent.update_emotions_for_elimination(
                                vote_result.eliminated_id, eliminated_char.faction
                            )

                    narration = await self.game_master._generate_narration(
                        state, "elimination", {
                            "name": eliminated_char.name,
                            "role": eliminated_char.hidden_role,
                            "faction": eliminated_char.faction,
                        }
                    )
                    yield f"data: {json.dumps({'type': 'elimination', 'character_id': vote_result.eliminated_id, 'character_name': vote_result.eliminated_name, 'hidden_role': eliminated_char.hidden_role, 'faction': eliminated_char.faction, 'narration': narration})}\n\n"

        # Check win condition and advance (reveal -> night or ended)
        state, narration = await self.game_master.advance_phase(state, agents)
        if state.phase == "ended":
            yield f"data: {json.dumps({'type': 'game_over', 'winner': state.winner, 'narration': narration})}\n\n"
        elif state.phase == "night":
            # Emit night start narration
            if narration:
                yield f"data: {json.dumps({'type': 'narration', 'content': narration, 'phase': state.phase, 'round': state.round})}\n\n"

            # Summarize round for all agents before night
            alive = game_state.get_alive_characters(state)
            round_msgs = [m for m in state.messages if m.round == state.round]
            for char in alive:
                agent = agents.get(char.id)
                if agent:
                    try:
                        await agent.summarize_round(round_msgs)
                    except Exception:
                        pass

            self._sessions[session_id] = state
            await self._save_session(session_id)

            # Auto-trigger night phase
            async for night_event in self.handle_night(session_id):
                yield night_event
            return
        else:
            if narration:
                yield f"data: {json.dumps({'type': 'narration', 'content': narration, 'phase': state.phase, 'round': state.round})}\n\n"

        self._sessions[session_id] = state
        await self._save_session(session_id)
        yield f"data: {json.dumps({'type': 'done', 'phase': state.phase, 'round': state.round})}\n\n"

    # ── Night phase ────────────────────────────────────────────────────

    def _get_player_night_action_type(self, state: GameState) -> str | None:
        """Determine what night action the player can perform, or None.

        Rounds 1-2: Only investigation is available. Kills and protections are blocked.
        Round 3+: Full powers.
        """
        if not state.player_role or state.player_role.is_eliminated:
            return None
        role = state.player_role.hidden_role.lower()
        is_early_round = state.round < EARLY_ROUND_THRESHOLD
        evil_factions = {
            f.get("name", "")
            for f in state.world.factions
            if f.get("alignment", "").lower() == "evil"
        }
        if state.player_role.faction in evil_factions:
            return None if is_early_round else "kill"
        if "seer" in role or "investigat" in role:
            return "investigate"  # Seer can always investigate
        if "doctor" in role or "protect" in role:
            return "protect" if is_early_round else "protect"  # Doctor can practice-protect
        return None  # Villager — no night action

    def _get_eligible_night_targets(self, state: GameState) -> list[dict]:
        """Get list of characters the player can target at night."""
        alive = game_state.get_alive_characters(state)
        action_type = self._get_player_night_action_type(state)
        targets = []
        for c in alive:
            # Evil players should not target evil allies
            if action_type == "kill" and state.player_role:
                if c.id in state.player_role.allies:
                    continue
            targets.append({
                "id": c.id,
                "name": c.name,
                "persona": c.persona,
                "public_role": c.public_role,
                "avatar_seed": c.avatar_seed,
            })
        return targets

    async def handle_night(
        self, session_id: str
    ) -> AsyncGenerator[str, None]:
        """Handle the night phase. Yields SSE event strings."""
        state = await self._get_session(session_id)
        agents = self._get_agents(session_id)

        if state.phase != "night":
            yield f"data: {json.dumps({'type': 'error', 'error': 'Not in night phase'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'night_started'})}\n\n"

        # Check if player needs to act
        player_action_type = self._get_player_night_action_type(state)
        if player_action_type:
            # Emit prompt for player to choose their night action
            eligible_targets = self._get_eligible_night_targets(state)
            yield f"data: {json.dumps({'type': 'night_action_prompt', 'action_type': player_action_type, 'eligible_targets': eligible_targets})}\n\n"
            # Mark state as awaiting player action and return
            state.awaiting_player_night_action = True
            self._sessions[session_id] = state
            await self._save_session(session_id)
            return

        # Player has no night action (villager) — resolve immediately
        async for event in self._resolve_night(session_id, player_action=None):
            yield event

    async def handle_player_night_action(
        self, session_id: str, action_type: str, target_character_id: str
    ) -> AsyncGenerator[str, None]:
        """Handle the player's submitted night action, then resolve all night actions."""
        state = await self._get_session(session_id)

        if not state.awaiting_player_night_action:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Not awaiting player night action'})}\n\n"
            return

        state.awaiting_player_night_action = False
        self._sessions[session_id] = state

        player_action = NightAction(
            character_id="player",
            action_type=action_type,
            target_id=target_character_id,
        )

        async for event in self._resolve_night(session_id, player_action=player_action):
            yield event

    async def _resolve_night(
        self, session_id: str, player_action: NightAction | None = None
    ) -> AsyncGenerator[str, None]:
        """Resolve all night actions (AI + player) and emit SSE events."""
        state = await self._get_session(session_id)
        agents = self._get_agents(session_id)

        # Execute night phase via game master (includes player action)
        state, narration = await self.game_master.handle_night(state, agents, player_action=player_action)

        # Emit individual night actions (hidden details, just action types)
        for action in state.night_actions:
            if action.action_type != "none" and action.character_id != "player":
                char = next((c for c in state.characters if c.id == action.character_id), None)
                yield f"data: {json.dumps({'type': 'night_action', 'character_id': action.character_id, 'character_name': char.name if char else 'Unknown', 'action_type': action.action_type, 'result': action.result})}\n\n"
                await asyncio.sleep(random.uniform(1.0, 2.5))

        # Check if player got an investigation result
        if state.player_investigation_result:
            yield f"data: {json.dumps({'type': 'investigation_result', 'investigation_result': state.player_investigation_result})}\n\n"

        # Check if player was killed at night
        player_killed = state.player_killed_at_night

        # Emit night results with narration and eliminated character IDs
        eliminated_ids = [a.target_id for a in state.night_actions if a.result == "killed" and a.target_id]
        yield f"data: {json.dumps({'type': 'night_results', 'narration': narration, 'eliminated_ids': eliminated_ids})}\n\n"

        # If player was killed, emit player_eliminated with all hidden info for ghost mode
        if player_killed and state.player_role:
            all_characters = [
                {
                    "id": c.id, "name": c.name, "hidden_role": c.hidden_role,
                    "faction": c.faction, "is_eliminated": c.is_eliminated,
                    "persona": c.persona, "public_role": c.public_role,
                    "avatar_seed": c.avatar_seed,
                }
                for c in state.characters
            ]
            yield f"data: {json.dumps({'type': 'player_eliminated', 'hidden_role': state.player_role.hidden_role, 'faction': state.player_role.faction, 'eliminated_by': 'night_kill', 'all_characters': all_characters})}\n\n"

        # Update emotions for night eliminations
        for killed_id in eliminated_ids:
            if killed_id == "player":
                continue
            killed_char = next((c for c in state.characters if c.id == killed_id), None)
            if killed_char:
                for char in game_state.get_alive_characters(state):
                    agent = agents.get(char.id)
                    if agent:
                        agent.update_emotions_for_elimination(killed_id, killed_char.faction)

        # Record night kills as canon facts
        for killed_id in eliminated_ids:
            if killed_id == "player":
                state.canon_facts.append(
                    f"The player (Council Member) was killed during night of round {state.round}"
                )
            else:
                killed_char = next((c for c in state.characters if c.id == killed_id), None)
                if killed_char:
                    state.canon_facts.append(
                        f"{killed_char.name} was killed during night of round {state.round} "
                        f"(was {killed_char.hidden_role} of {killed_char.faction})"
                    )
        # Push updated canon facts to all alive agents
        for char in game_state.get_alive_characters(state):
            agent = agents.get(char.id)
            if agent:
                agent.update_canon_facts(state.canon_facts)

        # Decay emotions at round boundary for all alive characters
        for char in game_state.get_alive_characters(state):
            agent = agents.get(char.id)
            if agent:
                agent.decay_emotions()

        # Update tension after night results
        state = self.game_master.update_tension(state)

        # Check win conditions after night
        winner = self.game_master._check_win_conditions(state)
        if winner:
            state = game_state.end_game(state, winner)
            evil_factions = {
                f.get("name", "")
                for f in state.world.factions
                if f.get("alignment", "").lower() == "evil"
            }
            template_key = "game_end_evil" if winner in evil_factions else "game_end_good"
            end_narration = await self.game_master._generate_narration(state, template_key, {"faction": winner})
            yield f"data: {json.dumps({'type': 'game_over', 'winner': state.winner, 'narration': end_narration})}\n\n"
        else:
            # Advance to next discussion round
            state, disc_narration = await self.game_master.advance_phase(state, agents)
            if disc_narration:
                yield f"data: {json.dumps({'type': 'narration', 'content': disc_narration, 'phase': state.phase, 'round': state.round})}\n\n"

        self._sessions[session_id] = state
        await self._save_session(session_id)
        yield f"data: {json.dumps({'type': 'done', 'phase': state.phase, 'round': state.round})}\n\n"

    # ── Public state ──────────────────────────────────────────────────

    async def get_public_state(self, session_id: str, full: bool = False) -> dict:
        """Return the public projection of game state."""
        state = await self._get_session(session_id)
        return self._public_state(state, full=full)

    async def get_reveal(self, session_id: str, character_id: str) -> dict:
        """Get an eliminated character's hidden info."""
        state = await self._get_session(session_id)
        char = next((c for c in state.characters if c.id == character_id), None)
        if not char:
            raise ValueError(f"Character {character_id} not found")
        if not char.is_eliminated:
            raise ValueError(f"Character {character_id} is not eliminated")
        return {
            "id": char.id,
            "name": char.name,
            "hidden_role": char.hidden_role,
            "faction": char.faction,
            "win_condition": char.win_condition,
            "hidden_knowledge": char.hidden_knowledge,
            "behavioral_rules": char.behavioral_rules,
        }

    async def get_player_role(self, session_id: str) -> dict:
        """Get the player's hidden role (only visible to the player)."""
        state = await self._get_session(session_id)
        if not state.player_role:
            raise ValueError("No player role assigned")
        pr = state.player_role
        ally_details = []
        for aid in pr.allies:
            achar = next((c for c in state.characters if c.id == aid), None)
            if achar:
                ally_details.append({"id": aid, "name": achar.name})
        return {
            "hidden_role": pr.hidden_role,
            "faction": pr.faction,
            "win_condition": pr.win_condition,
            "allies": ally_details,
            "is_eliminated": pr.is_eliminated,
            "eliminated_by": pr.eliminated_by,
        }

    def list_scenarios(self) -> list[dict]:
        """List available pre-built scenarios."""
        return self.doc_engine.list_scenarios()
