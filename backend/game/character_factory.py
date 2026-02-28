"""Character generation from WorldModel using Mistral Large 3."""

import os
import json
import uuid
from mistralai import Mistral
from dotenv import load_dotenv

from backend.models.game_models import WorldModel, Character, SimsTraits, MindMirror, MindMirrorPlane
from backend.game.prompts import CHARACTER_GENERATION_SYSTEM, CHARACTER_GENERATION_USER

load_dotenv()

VOICE_POOL = ["Sarah", "George", "Charlie", "Alice", "Harry", "Emily", "James", "Lily"]


class CharacterFactory:
    def __init__(self):
        self._mistral = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    async def generate_characters(
        self, world: WorldModel, num_characters: int = 5
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

        try:
            response = await self._mistral.chat.complete_async(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            raw_chars = data.get("characters", [])
            if not isinstance(raw_chars, list) or len(raw_chars) == 0:
                return self._fallback_characters(world, num_characters)
        except Exception:
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

        return characters
