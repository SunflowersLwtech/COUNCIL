"""Unit tests for DocumentEngine — document-to-WorldModel pipeline."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.game_models import WorldModel
from backend.game.document_engine import DocumentEngine


def _make_world_response(world_data: dict) -> MagicMock:
    """Build a mock Mistral chat response containing world JSON."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps(world_data)
    return mock_resp


SAMPLE_WORLD_DATA = {
    "title": "Werewolf Village",
    "setting": "A medieval village where werewolves lurk.",
    "factions": [
        {"name": "Village", "alignment": "good", "description": "Innocent villagers"},
        {"name": "Werewolf", "alignment": "evil", "description": "Hidden predators"},
    ],
    "roles": [
        {"name": "Villager", "faction": "Village", "ability": "None"},
        {"name": "Seer", "faction": "Village", "ability": "Detect evil"},
        {"name": "Werewolf", "faction": "Werewolf", "ability": "Deception"},
    ],
    "win_conditions": [
        {"faction": "Village", "condition": "Eliminate all werewolves"},
        {"faction": "Werewolf", "condition": "Outnumber villagers"},
    ],
    "phases": [
        {"name": "Discussion", "duration": "5 min"},
        {"name": "Voting", "duration": "2 min"},
    ],
    "flavor_text": "The moon rises over the village...",
}


class TestDocumentEngine:
    @pytest.mark.asyncio
    async def test_parse_markdown_text(self):
        """Process text returns a valid WorldModel."""
        mock_resp = _make_world_response(SAMPLE_WORLD_DATA)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            engine = DocumentEngine()
            world = await engine.process_text("# Werewolf\nA game about werewolves.")

        assert isinstance(world, WorldModel)
        assert world.title == "Werewolf Village"
        assert len(world.factions) == 2
        assert len(world.roles) == 3

    @pytest.mark.asyncio
    async def test_extract_factions(self):
        """Factions are correctly extracted from response."""
        mock_resp = _make_world_response(SAMPLE_WORLD_DATA)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            engine = DocumentEngine()
            world = await engine.process_text("test text")

        faction_names = {f["name"] for f in world.factions}
        assert "Village" in faction_names
        assert "Werewolf" in faction_names

    @pytest.mark.asyncio
    async def test_extract_roles(self):
        """Roles are correctly extracted from response."""
        mock_resp = _make_world_response(SAMPLE_WORLD_DATA)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            engine = DocumentEngine()
            world = await engine.process_text("test text")

        role_names = {r["name"] for r in world.roles}
        assert "Villager" in role_names
        assert "Seer" in role_names
        assert "Werewolf" in role_names

    @pytest.mark.asyncio
    async def test_extract_win_conditions(self):
        """Win conditions are correctly extracted."""
        mock_resp = _make_world_response(SAMPLE_WORLD_DATA)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            engine = DocumentEngine()
            world = await engine.process_text("test text")

        assert len(world.win_conditions) == 2

    @pytest.mark.asyncio
    async def test_chinese_text_handling(self):
        """Engine handles Chinese text (three kingdoms scenario)."""
        chinese_world = {
            "title": "三国赤壁密谋",
            "setting": "公元208年冬，曹操率八十万大军南下",
            "factions": [
                {"name": "蜀汉", "alignment": "good"},
                {"name": "曹魏", "alignment": "evil"},
            ],
            "roles": [
                {"name": "诸葛亮", "faction": "蜀汉"},
                {"name": "曹操", "faction": "曹魏"},
            ],
            "win_conditions": [{"faction": "蜀汉", "condition": "联盟抗曹"}],
            "phases": [],
            "flavor_text": "赤壁之战",
        }
        mock_resp = _make_world_response(chinese_world)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            engine = DocumentEngine()
            world = await engine.process_text("三国·赤壁密谋 — 历史社交博弈剧本")

        assert "三国" in world.title
        assert len(world.factions) >= 2

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_input(self):
        """Invalid API response triggers fallback world."""
        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(
                side_effect=Exception("Parse error")
            )
            engine = DocumentEngine()
            world = await engine.process_text("some invalid content")

        # Fallback should be Classic Werewolf
        assert isinstance(world, WorldModel)
        assert world.title == "Classic Werewolf"
        assert len(world.factions) == 2

    @pytest.mark.asyncio
    async def test_empty_text_returns_fallback(self):
        """Empty text returns fallback world without API call."""
        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock()
            engine = DocumentEngine()
            world = await engine.process_text("")

        assert isinstance(world, WorldModel)
        assert world.title == "Classic Werewolf"
        # Should NOT have called the API
        MockMistral.return_value.chat.complete_async.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_fallback(self):
        """Whitespace-only text returns fallback."""
        with patch("backend.game.document_engine.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock()
            engine = DocumentEngine()
            world = await engine.process_text("   \n\n  ")

        assert world.title == "Classic Werewolf"

    @pytest.mark.asyncio
    async def test_fallback_world_structure(self):
        """Fallback world has all required fields."""
        with patch("backend.game.document_engine.Mistral") as MockMistral:
            engine = DocumentEngine()
            world = engine._fallback_world()

        assert world.title
        assert world.setting
        assert len(world.factions) >= 2
        assert len(world.roles) >= 3
        assert len(world.win_conditions) >= 2
        assert len(world.phases) >= 2
        assert world.flavor_text

    @pytest.mark.asyncio
    async def test_process_document_fallback_on_ocr_fail(self, mock_mistral_client):
        """process_document falls back to text decode when OCR fails."""
        world_resp = _make_world_response(SAMPLE_WORLD_DATA)

        with patch("backend.game.document_engine.Mistral") as MockMistral:
            client = MockMistral.return_value
            client.files.upload_async = AsyncMock(side_effect=Exception("OCR fail"))
            client.chat.complete_async = AsyncMock(return_value=world_resp)

            engine = DocumentEngine()
            world = await engine.process_document(
                b"# Test Rules\nA werewolf game.", "test.md"
            )

        assert isinstance(world, WorldModel)

    def test_list_scenarios(self):
        """list_scenarios returns scenario metadata."""
        with patch("backend.game.document_engine.Mistral"):
            engine = DocumentEngine()
            scenarios = engine.list_scenarios()

        if len(scenarios) > 0:
            assert "id" in scenarios[0]
            assert "name" in scenarios[0]
            assert "path" in scenarios[0]

    @pytest.mark.asyncio
    async def test_load_scenario_not_found(self):
        """load_scenario raises ValueError for unknown ID."""
        with patch("backend.game.document_engine.Mistral"):
            engine = DocumentEngine()
            with pytest.raises(ValueError, match="not found"):
                await engine.load_scenario("nonexistent-scenario")
