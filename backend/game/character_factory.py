"""Character generation from WorldModel using Mistral Large 3."""

import asyncio
import os
import json
import random
import uuid
import logging
from mistralai import Mistral
from dotenv import load_dotenv

from backend.models.game_models import WorldModel, Character, SimsTraits, MindMirror, MindMirrorPlane
from backend.game.prompts import CHARACTER_GENERATION_SYSTEM, CHARACTER_GENERATION_USER

load_dotenv()
logger = logging.getLogger(__name__)

VOICE_POOL = ["Sarah", "George", "Charlie", "Alice", "Harry", "Emily", "James", "Lily"]

# Timeout for Mistral API calls (seconds).
# Character generation with detailed traits (big five, MBTI, sims, mind mirror)
# requires ~60-70s from the Mistral API.
_MISTRAL_TIMEOUT = 120

# Retry configuration for character generation
_MAX_RETRIES = 3
_BASE_DELAY = 2.0


def _new_mistral_client() -> Mistral:
    """Create a fresh Mistral client to avoid stale httpx connection pools."""
    return Mistral(api_key=os.environ["MISTRAL_API_KEY"])


class CharacterFactory:
    def __init__(self):
        pass  # No longer reuse a single Mistral client

    async def generate_characters(
        self, world: WorldModel, num_characters: int = 7
    ) -> list[Character]:
        """Generate characters from a WorldModel via a single Mistral call."""
        num_characters = max(3, min(num_characters, 8))

        factions_str = json.dumps(world.factions, indent=2)
        roles_str = json.dumps(world.roles, indent=2)
        win_str = json.dumps(world.win_conditions, indent=2)

        system = CHARACTER_GENERATION_SYSTEM.format(num_characters=num_characters)
        user = CHARACTER_GENERATION_USER.format(
            world_title=world.title,
            setting=world.setting,
            factions=factions_str,
            roles=roles_str,
            win_conditions=win_str,
            num_characters=num_characters,
        )

        def _sync_generate():
            """Run Mistral call in a thread to avoid uvicorn event loop issues."""
            client = _new_mistral_client()
            resp = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            return resp

        last_error = None
        raw_chars = []
        for attempt in range(_MAX_RETRIES):
            try:
                logger.info("Character generation attempt %d/%d...", attempt + 1, _MAX_RETRIES)
                response = await asyncio.wait_for(
                    asyncio.to_thread(_sync_generate),
                    timeout=_MISTRAL_TIMEOUT,
                )
                data = json.loads(response.choices[0].message.content)
                raw_chars = data.get("characters", [])
                if isinstance(raw_chars, list) and len(raw_chars) > 0:
                    logger.info("Character generation succeeded on attempt %d", attempt + 1)
                    break
                last_error = "Empty or invalid response"
            except asyncio.TimeoutError:
                last_error = f"Timeout after {_MISTRAL_TIMEOUT}s"
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"

            if attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY * (2 ** attempt)
                logger.warning("Character gen attempt %d failed (%s), retry in %.1fs",
                              attempt + 1, last_error, delay)
                await asyncio.sleep(delay)
        else:
            logger.error("All %d attempts failed (%s), using fallback", _MAX_RETRIES, last_error)
            return self._fallback_characters(world, num_characters)

        characters = []
        for i, raw in enumerate(raw_chars[:num_characters]):
            char = Character(
                id=str(uuid.uuid4())[:8],
                name=raw.get("name", f"Character {i+1}"),
                persona=raw.get("persona", "A mysterious council member."),
                speaking_style=raw.get("speaking_style", "neutral"),
                avatar_seed=raw.get("avatar_seed", str(uuid.uuid4())[:6]),
                public_role=raw.get("public_role", "Council Member"),
                hidden_role=raw.get("hidden_role", "Unknown"),
                faction=raw.get("faction", "Unknown"),
                win_condition=raw.get("win_condition", "Survive"),
                hidden_knowledge=raw.get("hidden_knowledge", []),
                behavioral_rules=raw.get("behavioral_rules", []),
                big_five=raw.get("big_five", ""),
                mbti=raw.get("mbti", ""),
                moral_values=raw.get("moral_values", []),
                decision_making_style=raw.get("decision_making_style", ""),
                secret=raw.get("secret", ""),
                want=raw.get("want", ""),
                method=raw.get("method", ""),
                personality_summary=raw.get("personality_summary", ""),
                voice_id=VOICE_POOL[i % len(VOICE_POOL)],
            )

            # Parse enhanced personality if present
            raw_sims = raw.get("sims_traits", {})
            if isinstance(raw_sims, dict):
                char.sims_traits = SimsTraits(
                    neat=raw_sims.get("neat", 5),
                    outgoing=raw_sims.get("outgoing", 5),
                    active=raw_sims.get("active", 5),
                    playful=raw_sims.get("playful", 5),
                    nice=raw_sims.get("nice", 5),
                )

            raw_mm = raw.get("mind_mirror", {})
            if isinstance(raw_mm, dict):
                planes = {}
                for plane_name in ["bio_energy", "emotional", "mental", "social"]:
                    raw_plane = raw_mm.get(plane_name, {})
                    if isinstance(raw_plane, dict):
                        planes[plane_name] = MindMirrorPlane(
                            traits=raw_plane.get("traits", {}),
                            jazz=raw_plane.get("jazz", {}),
                        )
                char.mind_mirror = MindMirror(**planes)

            characters.append(char)

        # Guarantee at least 1 Doctor/Protector among good-faction characters
        characters = self._ensure_doctor_role(characters, world)

        return characters

    def _ensure_doctor_role(
        self, characters: list[Character], world: WorldModel
    ) -> list[Character]:
        """Ensure at least one good-faction character has a Doctor/Protector role."""
        doctor_keywords = {"doctor", "protector", "protect", "healer", "medic"}
        has_doctor = any(
            any(kw in c.hidden_role.lower() for kw in doctor_keywords)
            for c in characters
        )
        if has_doctor:
            return characters

        evil_factions = {
            f.get("name", "")
            for f in world.factions
            if f.get("alignment", "").lower() == "evil"
        }

        # Find a good-faction character without a special role to reassign
        candidates = [
            c for c in characters
            if c.faction not in evil_factions
            and "seer" not in c.hidden_role.lower()
            and "investigat" not in c.hidden_role.lower()
        ]
        if not candidates:
            return characters

        # Pick a random non-special good character
        target = random.choice(candidates)
        target.hidden_role = "Doctor"
        target.hidden_knowledge = [
            f"You are the Doctor of the {target.faction}.",
            "Ability: Protect one player per night from elimination (Round 3+).",
        ] + [k for k in target.hidden_knowledge if "doctor" not in k.lower()]
        target.behavioral_rules = [
            r for r in target.behavioral_rules
            if "villager" not in r.lower()
        ] + ["Protect key allies at night. Don't reveal your role unless strategically necessary."]

        logger.info("Guaranteed Doctor role assigned to %s", target.name)
        return characters

    def _fallback_characters(
        self, world: WorldModel, num_characters: int
    ) -> list[Character]:
        """Generate fallback characters from world roles."""
        characters = []
        roles = world.roles if world.roles else [
            {"name": "Villager", "faction": "Village", "ability": "None", "description": "A regular villager"},
            {"name": "Seer", "faction": "Village", "ability": "Can sense evil", "description": "A mystic"},
            {"name": "Werewolf", "faction": "Werewolf", "ability": "Deception", "description": "A hidden wolf"},
        ]

        evil_factions = {
            f.get("name", "")
            for f in world.factions
            if f.get("alignment", "").lower() == "evil"
        }

        fallback_names = [
            ("Elder Marcus", "Speaks with authority and gravitas", "formal and measured"),
            ("Swift Lila", "Quick-witted trader from the eastern markets", "casual with sharp observations"),
            ("Brother Aldric", "A pious monk who sees signs in everything", "reverent and cryptic"),
            ("Captain Thorne", "Former military, trusts no one easily", "curt and suspicious"),
            ("Mira the Weaver", "Kind-hearted artisan who knows everyone's secrets", "warm but gossips"),
            ("Old Sage Finn", "Village elder with a memory like a steel trap", "slow, deliberate, wise"),
            ("Young Petra", "Ambitious newcomer eager to prove herself", "enthusiastic and bold"),
            ("Quiet Jasper", "Rarely speaks, but when he does, people listen", "terse and blunt"),
        ]

        # Assign varied personality traits for fallbacks
        fallback_traits = [
            SimsTraits(neat=7, outgoing=3, active=4, playful=2, nice=6),  # Elder Marcus: tidy, introverted, serious, kind
            SimsTraits(neat=3, outgoing=8, active=7, playful=6, nice=5),  # Swift Lila: messy, outgoing, active, playful
            SimsTraits(neat=8, outgoing=4, active=3, playful=1, nice=7),  # Brother Aldric: orderly, reserved, serious, kind
            SimsTraits(neat=5, outgoing=5, active=8, playful=3, nice=3),  # Captain Thorne: neutral, active, serious, grouchy
            SimsTraits(neat=4, outgoing=9, active=5, playful=7, nice=8),  # Mira: warm, outgoing, playful, very nice
            SimsTraits(neat=6, outgoing=2, active=2, playful=3, nice=7),  # Old Sage Finn: tidy, shy, lazy, nice
            SimsTraits(neat=3, outgoing=7, active=9, playful=8, nice=5),  # Young Petra: messy, outgoing, very active, playful
            SimsTraits(neat=6, outgoing=1, active=4, playful=2, nice=4),  # Quiet Jasper: tidy, very shy, serious, neutral
        ]

        for i in range(min(num_characters, len(fallback_names))):
            role_data = roles[i % len(roles)]
            faction = role_data.get("faction", "Village")
            is_evil = faction in evil_factions
            name, persona, style = fallback_names[i]

            wc = "Survive and outnumber the good" if is_evil else "Find and eliminate all evil members"
            for wcd in world.win_conditions:
                if wcd.get("faction", "") == faction:
                    wc = wcd.get("condition", wc)
                    break

            char = Character(
                id=str(uuid.uuid4())[:8],
                name=name,
                persona=persona,
                speaking_style=style,
                avatar_seed=str(uuid.uuid4())[:6],
                public_role="Council Member",
                hidden_role=role_data.get("name", "Villager"),
                faction=faction,
                win_condition=wc,
                hidden_knowledge=[
                    f"You are a {role_data.get('name', 'member')} of the {faction}.",
                    f"Ability: {role_data.get('ability', 'None')}",
                ],
                behavioral_rules=[
                    "Never reveal your true role directly.",
                    "Stay in character at all times.",
                    f"{'Deflect suspicion from yourself and fellow evil members.' if is_evil else 'Use logic and observation to find evil players.'}",
                ],
                voice_id=VOICE_POOL[i % len(VOICE_POOL)],
            )
            char.sims_traits = fallback_traits[i]
            characters.append(char)

        # Guarantee at least 1 Doctor/Protector in fallback
        characters = self._ensure_doctor_role(characters, world)

        return characters
