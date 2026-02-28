"""Integration tests: document -> world -> characters full pipeline.

Uses mocked Mistral API calls and real scenario files.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.game_models import WorldModel, Character, GameState
from backend.game.document_engine import DocumentEngine
from backend.game.character_factory import CharacterFactory

SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "test" / "scenarios"

SCENARIO_FILES = sorted(SCENARIOS_DIR.glob("*.md")) if SCENARIOS_DIR.exists() else []


def _make_world_response(title: str, num_factions: int = 2) -> MagicMock:
    """Build a mock Mistral response for world extraction."""
    world_data = {
        "title": title,
        "setting": f"The world of {title}",
        "factions": [
            {"name": f"Faction{i}", "alignment": "good" if i == 0 else "evil"}
            for i in range(num_factions)
        ],
        "roles": [
            {"name": f"Role{i}", "faction": f"Faction{i % num_factions}"}
            for i in range(num_factions + 1)
        ],
        "win_conditions": [
            {"faction": f"Faction{i}", "condition": f"Win condition {i}"}
            for i in range(num_factions)
        ],
        "phases": [
            {"name": "Discussion", "duration": "5 min"},
            {"name": "Voting", "duration": "2 min"},
        ],
        "flavor_text": f"Welcome to {title}.",
    }
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps(world_data)
    return mock_resp


def _make_characters_response(num: int = 5) -> MagicMock:
    """Build a mock Mistral response for character generation."""
    chars = []
    for i in range(num):
        chars.append({
            "name": f"Character {i+1}",
            "persona": f"Persona for character {i+1}",
            "speaking_style": "formal" if i % 2 == 0 else "casual",
            "avatar_seed": f"seed-{i}",
            "public_role": "Council Member",
            "hidden_role": "Villager" if i < num * 2 // 3 else "Infiltrator",
            "faction": "Faction0" if i < num * 2 // 3 else "Faction1",
            "win_condition": "Survive" if i < num * 2 // 3 else "Deceive",
            "hidden_knowledge": [f"Secret {i}"],
            "behavioral_rules": [f"Rule {i}"],
        })
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps({"characters": chars})
    return mock_resp


@pytest.mark.skipif(not SCENARIO_FILES, reason="No scenario files found")
class TestDocumentToGamePipeline:
    """Full pipeline: read scenario -> extract world -> generate characters."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=[f.stem for f in SCENARIO_FILES])
    async def test_scenario_produces_world(self, scenario_path: Path):
        """Each scenario file produces a valid WorldModel."""
        text = scenario_path.read_text(encoding="utf-8")
        world_resp = _make_world_response(scenario_path.stem)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=world_resp)
            engine = DocumentEngine()
            world = await engine.process_text(text)

        assert isinstance(world, WorldModel)
        assert world.title
        assert len(world.factions) >= 2

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=[f.stem for f in SCENARIO_FILES])
    async def test_scenario_produces_characters(self, scenario_path: Path):
        """Each scenario produces the expected number of characters."""
        text = scenario_path.read_text(encoding="utf-8")
        world_resp = _make_world_response(scenario_path.stem)
        char_resp = _make_characters_response(5)

        with patch("backend.game.document_engine.Mistral") as MockDocMistral:
            MockDocMistral.return_value.chat.complete_async = AsyncMock(return_value=world_resp)
            engine = DocumentEngine()
            world = await engine.process_text(text)

        with patch("backend.game.character_factory.Mistral") as MockCharMistral:
            MockCharMistral.return_value.chat.complete_async = AsyncMock(return_value=char_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(world, num_characters=5)

        assert len(chars) == 5
        for char in chars:
            assert isinstance(char, Character)
            assert char.name
            assert char.faction

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=[f.stem for f in SCENARIO_FILES])
    async def test_full_pipeline_creates_game_state(self, scenario_path: Path):
        """Full pipeline creates a valid GameState in lobby."""
        text = scenario_path.read_text(encoding="utf-8")
        world_resp = _make_world_response(scenario_path.stem)
        char_resp = _make_characters_response(5)

        with patch("backend.game.document_engine.Mistral") as MockDocMistral:
            MockDocMistral.return_value.chat.complete_async = AsyncMock(return_value=world_resp)
            engine = DocumentEngine()
            world = await engine.process_text(text)

        with patch("backend.game.character_factory.Mistral") as MockCharMistral:
            MockCharMistral.return_value.chat.complete_async = AsyncMock(return_value=char_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(world, num_characters=5)

        state = GameState(
            phase="lobby",
            world=world,
            characters=chars,
        )

        assert state.phase == "lobby"
        assert state.world.title
        assert len(state.characters) == 5
        assert state.round == 1
        assert state.winner is None

    @pytest.mark.asyncio
    async def test_werewolf_scenario_factions(self):
        """Werewolf scenario has Village and Werewolf factions."""
        werewolf_path = SCENARIOS_DIR / "01-werewolf-classic.md"
        if not werewolf_path.exists():
            pytest.skip("Werewolf scenario not found")

        world_data = {
            "title": "One Night Ultimate Werewolf",
            "setting": "A village plagued by werewolves.",
            "factions": [
                {"name": "Village", "alignment": "good"},
                {"name": "Werewolf", "alignment": "evil"},
            ],
            "roles": [
                {"name": "Villager", "faction": "Village"},
                {"name": "Seer", "faction": "Village"},
                {"name": "Werewolf", "faction": "Werewolf"},
            ],
            "win_conditions": [
                {"faction": "Village", "condition": "Eliminate all werewolves"},
                {"faction": "Werewolf", "condition": "Outnumber villagers"},
            ],
            "phases": [],
            "flavor_text": "The moon rises...",
        }
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps(world_data)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            engine = DocumentEngine()
            world = await engine.process_text(werewolf_path.read_text(encoding="utf-8"))

        faction_names = {f["name"] for f in world.factions}
        assert "Village" in faction_names
        assert "Werewolf" in faction_names

    @pytest.mark.asyncio
    async def test_chinese_scenario_pipeline(self):
        """Three Kingdoms Chinese scenario works end-to-end."""
        tk_path = SCENARIOS_DIR / "04-three-kingdoms-intrigue.md"
        if not tk_path.exists():
            pytest.skip("Three Kingdoms scenario not found")

        text = tk_path.read_text(encoding="utf-8")
        assert "三国" in text or "赤壁" in text

        world_data = {
            "title": "三国赤壁密谋",
            "setting": "赤壁之战前夕",
            "factions": [
                {"name": "蜀汉", "alignment": "good"},
                {"name": "曹魏", "alignment": "evil"},
            ],
            "roles": [
                {"name": "诸葛亮", "faction": "蜀汉"},
                {"name": "周瑜", "faction": "蜀汉"},
                {"name": "曹操", "faction": "曹魏"},
            ],
            "win_conditions": [],
            "phases": [],
            "flavor_text": "赤壁之战",
        }
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps(world_data)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            engine = DocumentEngine()
            world = await engine.process_text(text)

        assert "三国" in world.title
