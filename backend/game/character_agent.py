"""CharacterAgent — an LLM-driven game character built on MistralBaseAgent."""

from __future__ import annotations

import json
import logging
import random
import re
import asyncio
from typing import Optional, TYPE_CHECKING

from backend.agents.base_agent import MistralBaseAgent
from backend.models.game_models import Character, CharacterPublicInfo, ChatMessage, NightAction, WorldModel, Relationship, Memory
from backend.game.prompts import (
    CHARACTER_SYSTEM_PROMPT, VOTE_PROMPT,
    NIGHT_ACTION_PROMPT, SPONTANEOUS_REACTION_PROMPT, ROUND_SUMMARY_PROMPT,
)

if TYPE_CHECKING:
    from backend.game.skill_loader import SkillConfig, SkillLoader

logger = logging.getLogger(__name__)

# ── Mistral function-calling tool definitions ────────────────────────

GAME_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "cast_vote",
            "description": "Vote to eliminate a player from the council",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {"type": "string", "description": "ID of player to vote for"},
                    "reasoning": {"type": "string", "description": "Internal reasoning (hidden)"},
                },
                "required": ["target_id", "reasoning"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "night_action",
            "description": "Perform a night action (kill/investigate/protect)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string", "enum": ["kill", "investigate", "protect", "none"]},
                    "target_id": {"type": "string", "description": "Target player ID"},
                    "reasoning": {"type": "string", "description": "Internal reasoning"},
                },
                "required": ["action_type"],
            },
        },
    },
]

# ── Keyword triggers for emotion updates ─────────────────────────────

ACCUSATION_KEYWORDS = {"suspect", "traitor", "lying", "liar", "suspicious", "accuse", "blame", "guilty"}
SUPPORT_KEYWORDS = {"agree", "trust", "innocent", "support", "defend", "believe", "honest"}

# ── AI-like phrases to strip ─────────────────────────────────────────

AI_PHRASES = [
    "As an AI", "I cannot", "It's important to note",
    "I should mention", "As a language model",
    "I don't have personal", "It is worth noting",
]

# Response validation patterns (anti-jailbreak)
BREAKING_PATTERNS = [
    re.compile(r'as an ai', re.I),
    re.compile(r'language model', re.I),
    re.compile(r"i'm sorry,? but", re.I),
    re.compile(r'chatgpt|openai|anthropic|mistral ai', re.I),
    re.compile(r'my (training|programming|instructions)', re.I),
    re.compile(r'i am an? (ai|artificial|bot|program)', re.I),
]

# Memory bounds
MAX_CONVERSATION_HISTORY = 20
MAX_ROUND_MEMORY = 8
MAX_RECENT_MEMORIES = 10


class CharacterAgent(MistralBaseAgent):
    """An AI character agent that responds in-character during game play."""

    def __init__(
        self,
        character: Character,
        world_model: WorldModel,
        active_skills: list[SkillConfig] | None = None,
        skill_loader: SkillLoader | None = None,
        evil_factions: set[str] | None = None,
        canon_facts: list[str] | None = None,
    ):
        super().__init__()
        self.character = character
        self.world_model = world_model
        self.active_skills: list[SkillConfig] = active_skills or []
        self._skill_loader = skill_loader
        self._evil_factions: set[str] = evil_factions or set()
        self.canon_facts: list[str] = list(canon_facts) if canon_facts else []
        self.temperature = 0.7
        self.agent_role = character.name

        # Lazy injection cache — loaded on first access per target
        self._injection_cache: dict[str, str] = {}

        # Pre-compute merged behavioral rules
        self._all_behavioral_rules: list[str] = list(self.character.behavioral_rules)
        for skill in self.active_skills:
            self._all_behavioral_rules.extend(skill.behavioral_rules)

        self._prompt_dirty: bool = False
        self.system_prompt = self._build_system_prompt()
        self._conversation_history: list[dict] = []
        self._round_memory: list[str] = []
        self.current_round: int = 0

    def _get_injection(self, target: str) -> str:
        """Lazy-load skill injection for a target, with faction filtering and caching."""
        if target in self._injection_cache:
            return self._injection_cache[target]
        if self._skill_loader and self.active_skills:
            injection = self._skill_loader.build_injection_for_agent(
                target, self.active_skills,
                self.character.faction, self._evil_factions,
            )
        else:
            injection = ""
        self._injection_cache[target] = injection
        return injection

    def _build_system_prompt(self) -> str:
        """Build multi-layer prompt with YAML Jazz personality."""
        c = self.character
        w = self.world_model

        hidden_knowledge = "\n".join(f"- {k}" for k in c.hidden_knowledge) or "- None"

        behavioral_rules = "\n".join(f"- {r}" for r in self._all_behavioral_rules) or "- Stay in character."

        emotional_modifier = self.get_response_style()

        skill_injections = self._get_injection("character_agent")

        return CHARACTER_SYSTEM_PROMPT.format(
            name=c.name,
            world_title=w.title,
            hidden_role=c.hidden_role,
            faction=c.faction,
            win_condition=c.win_condition,
            hidden_knowledge=hidden_knowledge,
            behavioral_rules=behavioral_rules,
            persona=c.persona,
            speaking_style=c.speaking_style,
            public_role=c.public_role,
            want=c.want or "survive and understand what is happening",
            method=c.method or "observation and careful questioning",
            sims_traits_jazz=self._build_sims_jazz(),
            mind_mirror_jazz=self._build_mind_mirror_jazz(),
            personality_summary=c.personality_summary or "observant and cautious",
            emotional_modifier=emotional_modifier,
            current_mood=c.current_mood or "calm",
            driving_need=c.driving_need or "none",
            relationships_jazz=self._build_relationships_jazz(),
            memories_jazz=self._build_memories_jazz(),
            skill_injections=skill_injections,
            secret=c.secret or "none",
            decision_making_style=c.decision_making_style or "balanced and cautious",
            moral_values=self._build_moral_values_line(),
            big_five=c.big_five or "balanced",
            mbti=c.mbti or "XXXX",
            canon_facts_jazz=self._build_canon_facts_jazz(),
        )

    def _build_sims_jazz(self) -> str:
        st = self.character.sims_traits
        labels = {"neat": ("Sloppy", "Neat"), "outgoing": ("Shy", "Outgoing"),
                  "active": ("Lazy", "Active"), "playful": ("Serious", "Playful"),
                  "nice": ("Grouchy", "Nice")}
        lines = []
        for name, (low, high) in labels.items():
            val = getattr(st, name)
            label = low if val < 4 else (high if val > 6 else f"{low}/{high}")
            lines.append(f"# {name}: {val}/10  ({label})")
        return "\n".join(lines)

    def _build_mind_mirror_jazz(self) -> str:
        mm = self.character.mind_mirror
        lines = []
        for plane_name in ["bio_energy", "emotional", "mental", "social"]:
            plane = getattr(mm, plane_name)
            if plane.traits:
                lines.append(f"# {plane_name.upper()}:")
                for trait, val in plane.traits.items():
                    jazz = plane.jazz.get(trait, "")
                    suffix = f"  # {jazz}" if jazz else ""
                    lines.append(f"#   {trait}: {val}/7{suffix}")
        return "\n".join(lines) if lines else "# (default personality)"

    def _build_relationships_jazz(self) -> str:
        rels = self.character.relationships
        if not rels:
            return "# No strong feelings about anyone yet."
        lines = []
        for r in rels:
            word = "trusts" if r.trust > 0.6 else ("distrusts" if r.trust < 0.3 else "unsure about")
            lines.append(f"# {r.target_name}: {word} (closeness={r.closeness:.1f})")
            if r.narrative:
                lines.append(f"#   {r.narrative}")
        return "\n".join(lines)

    def _build_memories_jazz(self) -> str:
        mems = self.character.recent_memories
        if not mems:
            return "# No significant memories yet."
        lines = []
        for m in mems[-5:]:
            lines.append(f"# - {m.event}")
            if m.narrative:
                lines.append(f"#   {m.narrative}")
        return "\n".join(lines)

    def update_canon_facts(self, facts: list[str]):
        """Replace canon facts and mark prompt for rebuild."""
        self.canon_facts = list(facts)
        self._prompt_dirty = True

    def _build_canon_facts_jazz(self) -> str:
        if not self.canon_facts:
            return "# No established facts yet."
        lines = ["# ESTABLISHED FACTS (do not contradict):"]
        for fact in self.canon_facts:
            lines.append(f"# - {fact}")
        return "\n".join(lines)

    def _build_moral_values_line(self) -> str:
        vals = self.character.moral_values
        if not vals:
            return "adaptable, pragmatic"
        return ", ".join(vals)

    # ── Emotion system ───────────────────────────────────────────────

    async def update_emotions_llm(self, message: str, speaker_id: str):
        """Update emotional state using LLM analysis with keyword fallback."""
        try:
            analysis = await asyncio.wait_for(
                self._analyze_emotion_llm(message, speaker_id),
                timeout=5.0,
            )
            if analysis:
                self._apply_llm_emotion_analysis(analysis, speaker_id)
                return
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.warning("Emotion analysis failed for %s: %s", self.character.name, e)
        # Fallback to keyword matching
        self.update_emotions(message, speaker_id)

    async def _analyze_emotion_llm(self, message: str, speaker_id: str) -> dict | None:
        """Use mistral-small-latest to analyze emotional content of a message."""
        prompt = (
            f"Analyze this message from a social deduction game for its emotional impact on the character '{self.character.name}' "
            f"(faction: {self.character.faction}).\n\n"
            f"Message: \"{message}\"\n\n"
            f"Return valid JSON with these float scores (0.0 to 1.0):\n"
            f"- accusation_level: how much this message accuses or suspects {self.character.name}\n"
            f"- support_level: how much this message supports or defends {self.character.name}\n"
            f"- threat_to_faction: how threatening this message is to {self.character.name}'s faction goals\n"
        )
        messages = [
            {"role": "system", "content": "You are an emotion analyzer. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ]
        response = await self._mistral.chat.complete_async(
            model="mistral-small-latest",
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        data = json.loads(raw)
        return data

    def _apply_llm_emotion_analysis(self, analysis: dict, speaker_id: str):
        """Apply LLM emotion analysis results to emotional state."""
        es = self.character.emotional_state
        st = self.character.sims_traits
        mm = self.character.mind_mirror

        accusation = float(analysis.get("accusation_level", 0.0))
        support = float(analysis.get("support_level", 0.0))
        threat = float(analysis.get("threat_to_faction", 0.0))

        confidence = mm.emotional.traits.get("confident", 4) / 7.0
        niceness = st.nice / 10.0
        forcefulness = mm.emotional.traits.get("forceful", 4) / 7.0

        relationship = self._find_relationship(speaker_id)
        trust_with_speaker = relationship.trust if relationship else 0.5

        if accusation > 0.3:
            fear_delta = accusation * 0.25 * (1.0 - confidence * 0.6)
            anger_delta = accusation * 0.2 * (0.5 + forcefulness * 0.5)
            es.fear = min(1.0, es.fear + fear_delta)
            es.anger = min(1.0, es.anger + anger_delta)
            es.trust = max(0.0, es.trust - accusation * 0.15 * (0.5 + trust_with_speaker))
            es.happiness = max(0.0, es.happiness - accusation * 0.1)
            if relationship:
                relationship.trust = max(0.0, relationship.trust - accusation * 0.15)
            self._add_memory("Accused by someone", {"fear": fear_delta, "anger": anger_delta},
                           "That stung" if niceness > 0.5 else "They'll regret that")

        if support > 0.3:
            outgoingness = st.outgoing / 10.0
            es.trust = min(1.0, es.trust + support * 0.15 * (0.5 + outgoingness * 0.5))
            es.happiness = min(1.0, es.happiness + support * 0.1)
            es.fear = max(0.0, es.fear - support * 0.08 * confidence)
            if relationship:
                relationship.trust = min(1.0, relationship.trust + support * 0.1)
                relationship.closeness = min(1.0, relationship.closeness + support * 0.05)

        if threat > 0.3:
            es.curiosity = min(1.0, es.curiosity + threat * 0.1)
            es.energy = min(1.0, es.energy + threat * 0.05)

        self._update_mood_summary()
        self._prompt_dirty = True

    def update_emotions(self, message: str, speaker_id: str):
        """Update emotional state using keyword matching (synchronous fallback)."""
        es = self.character.emotional_state
        st = self.character.sims_traits
        mm = self.character.mind_mirror
        msg_lower = message.lower()
        name_lower = self.character.name.lower()
        is_targeted = name_lower in msg_lower

        # Personality modulation factors
        confidence = mm.emotional.traits.get("confident", 4) / 7.0
        niceness = st.nice / 10.0
        forcefulness = mm.emotional.traits.get("forceful", 4) / 7.0
        playfulness = st.playful / 10.0

        # Relationship context
        relationship = self._find_relationship(speaker_id)
        trust_with_speaker = relationship.trust if relationship else 0.5

        if is_targeted and any(kw in msg_lower for kw in ACCUSATION_KEYWORDS):
            fear_delta = 0.2 * (1.0 - confidence * 0.6)
            anger_delta = 0.15 * (0.5 + forcefulness * 0.5) * (1.0 - playfulness * 0.3)
            trust_delta = -0.1 * (0.5 + trust_with_speaker)
            happy_delta = -0.1 * (0.5 + niceness * 0.5)

            if forcefulness > 0.6:
                anger_delta += fear_delta * 0.3
                fear_delta *= 0.6

            es.fear = min(1.0, es.fear + fear_delta)
            es.anger = min(1.0, es.anger + anger_delta)
            es.trust = max(0.0, es.trust + trust_delta)
            es.happiness = max(0.0, es.happiness + happy_delta)

            if relationship:
                relationship.trust = max(0.0, relationship.trust - 0.15)

            self._add_memory(f"Accused by someone", {"fear": fear_delta, "anger": anger_delta},
                           "That stung" if niceness > 0.5 else "They'll regret that")

        if is_targeted and any(kw in msg_lower for kw in SUPPORT_KEYWORDS):
            outgoingness = st.outgoing / 10.0
            es.trust = min(1.0, es.trust + 0.15 * (0.5 + outgoingness * 0.5))
            es.happiness = min(1.0, es.happiness + 0.1 * (0.5 + niceness * 0.5))
            es.fear = max(0.0, es.fear - 0.08 * confidence)

            if relationship:
                relationship.trust = min(1.0, relationship.trust + 0.1)
                relationship.closeness = min(1.0, relationship.closeness + 0.05)

        if any(kw in msg_lower for kw in ACCUSATION_KEYWORDS):
            es.curiosity = min(1.0, es.curiosity + 0.05)
            es.energy = min(1.0, es.energy + 0.03)

        self._update_mood_summary()
        self._prompt_dirty = True

    def update_emotions_for_elimination(self, eliminated_id: str, eliminated_faction: str):
        """Update emotions when someone is eliminated."""
        es = self.character.emotional_state
        same_faction = eliminated_faction == self.character.faction

        if same_faction:
            # Ally eliminated — fear and sadness
            es.fear = min(1.0, es.fear + 0.3)
            es.happiness = max(0.0, es.happiness - 0.2)
            es.anger = min(1.0, es.anger + 0.1)
        else:
            # Enemy eliminated — relief
            es.happiness = min(1.0, es.happiness + 0.2)
            es.fear = max(0.0, es.fear - 0.1)
            es.trust = min(1.0, es.trust + 0.05)

        self._prompt_dirty = True

    def decay_emotions(self):
        """Decay emotions toward baseline between rounds. Anger decays slower (grudges persist)."""
        es = self.character.emotional_state
        baseline = {"happiness": 0.5, "anger": 0.0, "fear": 0.1, "trust": 0.5, "energy": 0.8, "curiosity": 0.5}
        decay_rate = 0.05

        for attr, base in baseline.items():
            current = getattr(es, attr)
            # Anger decays at half rate (grudges persist longer)
            effective_rate = decay_rate * 0.5 if attr == "anger" else decay_rate
            if current > base:
                setattr(es, attr, max(base, current - effective_rate))
            elif current < base:
                setattr(es, attr, min(base, current + effective_rate))

        self._prompt_dirty = True

    def _find_relationship(self, target_id: str) -> Optional[Relationship]:
        for r in self.character.relationships:
            if r.target_id == target_id:
                return r
        return None

    def _add_memory(self, event: str, mood_effect: dict, narrative: str):
        mem = Memory(event=event, mood_effect=mood_effect, narrative=narrative, round=self.current_round)
        self.character.recent_memories.append(mem)
        if len(self.character.recent_memories) > MAX_RECENT_MEMORIES:
            self.character.recent_memories = self.character.recent_memories[-MAX_RECENT_MEMORIES:]

    def _update_mood_summary(self):
        es = self.character.emotional_state
        moods = []
        if es.anger > 0.6: moods.append("angry")
        elif es.anger > 0.3: moods.append("irritated")
        if es.fear > 0.6: moods.append("anxious")
        elif es.fear > 0.3: moods.append("uneasy")
        if es.happiness > 0.7: moods.append("confident")
        elif es.happiness < 0.3: moods.append("dejected")
        if es.trust < 0.2: moods.append("suspicious of everyone")
        if es.curiosity > 0.7: moods.append("intensely focused")
        self.character.current_mood = ", ".join(moods) if moods else "calm and watchful"

    def get_dominant_emotion(self) -> str:
        """Return the dominant emotion label for SSE events."""
        es = self.character.emotional_state
        emotions = {
            "angry": es.anger,
            "fearful": es.fear,
            "happy": es.happiness,
            "suspicious": 1.0 - es.trust,
            "curious": es.curiosity,
        }
        dominant = max(emotions, key=emotions.get)
        # Only report if it's meaningfully elevated
        if emotions[dominant] < 0.4:
            return "neutral"
        return dominant

    def get_response_style(self) -> str:
        """Return a modifier string based on dominant emotion."""
        es = self.character.emotional_state
        modifiers = []

        if es.anger > 0.7:
            modifiers.append("You are defensive and aggressive. Snap back at accusations.")
        elif es.anger > 0.4:
            modifiers.append("You are irritated and tense.")

        if es.fear > 0.7:
            modifiers.append("You are nervous and evasive. Deflect attention from yourself.")
        elif es.fear > 0.4:
            modifiers.append("You feel uneasy and watchful.")

        if es.happiness > 0.7:
            modifiers.append("You are confident and relaxed. Speak with assurance.")

        if es.trust < 0.2:
            modifiers.append("You are deeply suspicious of everyone. Question motives.")

        if es.energy < 0.3:
            modifiers.append("You are exhausted and withdrawn. Keep responses short.")

        if es.curiosity > 0.7:
            modifiers.append("You are intensely curious. Ask probing questions.")

        if not modifiers:
            modifiers.append("You are calm and observant.")

        return " ".join(modifiers)

    def _ensure_prompt_fresh(self):
        """Rebuild the system prompt only if emotions have changed since last build."""
        if self._prompt_dirty:
            self.system_prompt = self._build_system_prompt()
            self._prompt_dirty = False

    # ── Humanize output ──────────────────────────────────────────────

    def _validate_in_character(self, response: str) -> str:
        """Validate response is in-character. Return fallback if broken."""
        for pattern in BREAKING_PATTERNS:
            if pattern.search(response):
                return self._get_fallback_response()
        return response

    def _get_fallback_response(self) -> str:
        """Return a safe in-character fallback response."""
        c = self.character
        fallbacks = [
            f"*{c.name} pauses, considering their words carefully*",
            f"Interesting point. I need to think about that",
            f"Let's not lose focus on what really matters here",
            f"I'm not sure what you mean by that",
        ]
        return random.choice(fallbacks)

    def _humanize(self, text: str) -> str:
        """Post-process: strip AI phrases and validate in-character."""
        text = text.strip()
        for phrase in AI_PHRASES:
            text = text.replace(phrase, "")
        text = text.strip().lstrip(",").lstrip(";").strip()
        text = self._validate_in_character(text)
        return text

    # ── Response generation ──────────────────────────────────────────

    async def respond_stream(self, message: str, context_messages: list[ChatMessage], talk_modifier: str = ""):
        """Stream an in-character response token-by-token. Yields text chunks.
        After iteration, self._last_response holds the final humanized text."""
        self._ensure_prompt_fresh()
        modifier_prefix = f"[Pacing note: {talk_modifier}]\n" if talk_modifier else ""
        context = ""
        recent = context_messages[-20:] if len(context_messages) > 20 else context_messages
        for msg in recent:
            prefix = f"[{msg.speaker_name}]" if msg.speaker_name else "[Unknown]"
            context += f"{prefix}: {msg.content}\n"

        memory_context = ""
        if self._round_memory:
            memory_context = "Your memory from previous rounds:\n" + "\n".join(
                f"- Round {i+1}: {mem}" for i, mem in enumerate(self._round_memory[-MAX_ROUND_MEMORY:])
            ) + "\n\n"

        own_messages = [m.content for m in context_messages if m.speaker_id == self.character.id][-3:]
        anti_repeat = ""
        if own_messages:
            anti_repeat = "Your previous messages (DO NOT repeat these):\n" + "\n".join(f"- {m}" for m in own_messages) + "\n\n"

        messages = [{"role": "system", "content": self.system_prompt}]

        if len(self._conversation_history) > 0 and len(self._conversation_history) % 10 == 0:
            messages.append({
                "role": "system",
                "content": f"REMINDER: You are {self.character.name}. Speak with {self.character.speaking_style}. Never break character.",
            })

        for turn in self._conversation_history[-6:]:
            messages.append(turn)

        messages.append({
            "role": "user",
            "content": (
                f"{modifier_prefix}{memory_context}"
                f"{anti_repeat}"
                f"Recent discussion:\n{context}\n\n"
                f"New message directed at the council: {message}\n\n"
                f"Respond in character as {self.character.name}. "
                "Keep it to 2-4 sentences."
            ),
        })

        full_response = ""
        try:
            async with asyncio.timeout(15.0):
                async for chunk in self.call_mistral_stream(messages):
                    full_response += chunk
                    yield chunk
        except TimeoutError:
            if not full_response:
                full_response = self._get_fallback_response()
                yield full_response
        except Exception:
            if not full_response:
                full_response = self._get_fallback_response()
                yield full_response

        # Don't re-humanize streamed content (client already has raw text).
        # Only validate it stays in-character for safety.
        final = self._validate_in_character(full_response.strip()) if full_response else self._get_fallback_response()
        self._last_response = final

        self._conversation_history.append({"role": "user", "content": message})
        self._conversation_history.append({"role": "assistant", "content": final})
        if len(self._conversation_history) > MAX_CONVERSATION_HISTORY:
            self._conversation_history = self._conversation_history[-MAX_CONVERSATION_HISTORY:]
        if len(self._round_memory) > MAX_ROUND_MEMORY:
            self._round_memory = self._round_memory[-MAX_ROUND_MEMORY:]

    async def respond(self, message: str, context_messages: list[ChatMessage], talk_modifier: str = "") -> str:
        """Generate an in-character response with safety guards."""
        self._ensure_prompt_fresh()
        modifier_prefix = f"[Pacing note: {talk_modifier}]\n" if talk_modifier else ""
        context = ""
        recent = context_messages[-20:] if len(context_messages) > 20 else context_messages
        for msg in recent:
            prefix = f"[{msg.speaker_name}]" if msg.speaker_name else "[Unknown]"
            context += f"{prefix}: {msg.content}\n"

        memory_context = ""
        if self._round_memory:
            memory_context = "Your memory from previous rounds:\n" + "\n".join(
                f"- Round {i+1}: {mem}" for i, mem in enumerate(self._round_memory[-MAX_ROUND_MEMORY:])
            ) + "\n\n"

        own_messages = [m.content for m in context_messages if m.speaker_id == self.character.id][-3:]
        anti_repeat = ""
        if own_messages:
            anti_repeat = "Your previous messages (DO NOT repeat these):\n" + "\n".join(f"- {m}" for m in own_messages) + "\n\n"

        messages = [{"role": "system", "content": self.system_prompt}]

        # Personality reinforcement every 5 exchanges
        if len(self._conversation_history) > 0 and len(self._conversation_history) % 10 == 0:
            messages.append({
                "role": "system",
                "content": f"REMINDER: You are {self.character.name}. Speak with {self.character.speaking_style}. Never break character.",
            })

        for turn in self._conversation_history[-6:]:
            messages.append(turn)

        messages.append({
            "role": "user",
            "content": (
                f"{modifier_prefix}{memory_context}"
                f"{anti_repeat}"
                f"Recent discussion:\n{context}\n\n"
                f"New message directed at the council: {message}\n\n"
                f"Respond in character as {self.character.name}. "
                "Keep it to 2-4 sentences."
            ),
        })

        try:
            response = await asyncio.wait_for(self.call_mistral(messages), timeout=15.0)
            response = self._humanize(response)
        except asyncio.TimeoutError:
            response = self._get_fallback_response()
        except Exception:
            response = self._get_fallback_response()

        # Bounded conversation history
        self._conversation_history.append({"role": "user", "content": message})
        self._conversation_history.append({"role": "assistant", "content": response})
        if len(self._conversation_history) > MAX_CONVERSATION_HISTORY:
            self._conversation_history = self._conversation_history[-MAX_CONVERSATION_HISTORY:]

        # Bounded round memory
        if len(self._round_memory) > MAX_ROUND_MEMORY:
            self._round_memory = self._round_memory[-MAX_ROUND_MEMORY:]

        return response

    async def vote(self, alive_characters: list[CharacterPublicInfo]) -> str:
        """AI decides who to vote for using function calling. Returns target character id."""
        self._ensure_prompt_fresh()
        c = self.character

        alive_list = "\n".join(
            f"- {ch.name} (id: {ch.id}) — {ch.public_role}"
            for ch in alive_characters
            if ch.id != c.id
        )

        recent_msgs = "\n".join(
            f"[{turn['role']}]: {turn['content'][:200]}"
            for turn in self._conversation_history[-15:]
        )

        prompt = VOTE_PROMPT.format(
            name=c.name,
            hidden_role=c.hidden_role,
            faction=c.faction,
            win_condition=c.win_condition,
            alive_list=alive_list,
            recent_messages=recent_msgs or "(no recent discussion)",
        )

        vote_injection = self._get_injection("vote_prompt")
        if vote_injection:
            prompt += "\n\n" + vote_injection

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        valid_ids = {ch.id for ch in alive_characters if ch.id != c.id}

        try:
            result = await asyncio.wait_for(
                self.call_mistral(messages, tools=[GAME_TOOLS[0]], tool_choice="any"),
                timeout=10.0,
            )
            if hasattr(result, 'arguments'):
                data = json.loads(result.arguments)
                target_id = data.get("target_id", "")
                if target_id in valid_ids:
                    return target_id
            elif isinstance(result, str):
                # Fallback: try parsing as JSON from text response
                data = json.loads(result)
                target_id = data.get("target_id", "")
                if target_id in valid_ids:
                    return target_id
            return next(iter(valid_ids)) if valid_ids else ""
        except Exception:
            # Fallback: vote for the first non-self alive character
            for ch in alive_characters:
                if ch.id != c.id:
                    return ch.id
            return ""

    async def night_action(
        self,
        alive_characters: list[CharacterPublicInfo],
        role_actions: str,
    ) -> NightAction:
        """Choose a night action using function calling. Returns a NightAction."""
        self._ensure_prompt_fresh()
        c = self.character

        alive_list = "\n".join(
            f"- {ch.name} (id: {ch.id}) — {ch.public_role}"
            for ch in alive_characters
            if ch.id != c.id
        )

        prompt = NIGHT_ACTION_PROMPT.format(
            name=c.name,
            hidden_role=c.hidden_role,
            faction=c.faction,
            win_condition=c.win_condition,
            alive_list=alive_list,
            role_actions=role_actions,
        )

        night_injection = self._get_injection("night_action")
        if night_injection:
            prompt += "\n\n" + night_injection

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            result = await asyncio.wait_for(
                self.call_mistral(messages, tools=[GAME_TOOLS[1]], tool_choice="any"),
                timeout=10.0,
            )
            if hasattr(result, 'arguments'):
                data = json.loads(result.arguments)
            elif isinstance(result, str):
                data = json.loads(result)
            else:
                return NightAction(character_id=c.id, action_type="none", target_id=None)

            action_type = data.get("action_type", "none")
            target_id = data.get("target_id")

            # Validate target
            if target_id:
                valid_ids = {ch.id for ch in alive_characters if ch.id != c.id}
                if target_id not in valid_ids:
                    target_id = next(iter(valid_ids)) if valid_ids else None

            return NightAction(
                character_id=c.id,
                action_type=action_type,
                target_id=target_id,
            )
        except Exception:
            return NightAction(
                character_id=c.id,
                action_type="none",
                target_id=None,
            )

    async def summarize_round(self, messages: list[ChatMessage]) -> str:
        """Compress a round's discussion into key takeaways for memory."""
        self._ensure_prompt_fresh()
        c = self.character

        msgs_text = "\n".join(
            f"[{m.speaker_name}]: {m.content}" for m in messages[-20:]
        )

        prompt = ROUND_SUMMARY_PROMPT.format(messages=msgs_text)

        summary_injection = self._get_injection("round_summary")
        if summary_injection:
            prompt += "\n\n" + summary_injection

        llm_messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            summary = await self.call_mistral(llm_messages)
            self._round_memory.append(summary)
            return summary
        except Exception:
            fallback = f"Round discussion with {len(messages)} messages."
            self._round_memory.append(fallback)
            return fallback

    async def react(self, context_messages: list[ChatMessage]) -> str | None:
        """Generate a spontaneous short reaction (1 sentence) or None."""
        self._ensure_prompt_fresh()
        c = self.character

        recent = context_messages[-10:] if len(context_messages) > 10 else context_messages
        recent_context = "\n".join(
            f"[{m.speaker_name}]: {m.content}" for m in recent
        )

        prompt = SPONTANEOUS_REACTION_PROMPT.format(
            name=c.name,
            recent_context=recent_context,
        )

        react_injection = self._get_injection("spontaneous_reaction")
        if react_injection:
            prompt += "\n\n" + react_injection

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.call_mistral(messages)
            if response.strip().upper() == "PASS":
                return None
            return self._humanize(response)
        except Exception:
            return None
