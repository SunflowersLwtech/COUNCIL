"""Unit tests for CharacterFactory — character generation logic."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.game_models import Character, CharacterPublicInfo, WorldModel
from backend.game.character_factory import CharacterFactory, VOICE_POOL


def _make_mock_response(characters_data: list[dict]) -> MagicMock:
    """Build a mock Mistral chat response containing character JSON."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps({"characters": characters_data})
    return mock_resp


def _sample_raw_characters(n: int = 5) -> list[dict]:
    """Generate raw character dicts as the LLM would return."""
    factions = ["Village"] * 3 + ["Werewolf"] * 2
    chars = []
    for i in range(n):
        chars.append({
            "name": f"Character {i+1}",
            "persona": f"Persona {i+1}",
            "speaking_style": "formal" if i % 2 == 0 else "casual",
            "avatar_seed": f"seed-{i}",
            "public_role": "Council Member",
            "hidden_role": "Villager" if i < 3 else "Werewolf",
            "faction": factions[i] if i < len(factions) else "Village",
            "win_condition": "Eliminate evil" if i < 3 else "Outnumber good",
            "hidden_knowledge": [f"Secret {i}"],
            "behavioral_rules": [f"Rule {i}"],
        })
    return chars


class TestCharacterFactory:
    @pytest.mark.asyncio
    async def test_correct_number_generated(self, sample_world):
        """Factory generates the requested number of characters."""
        raw = _sample_raw_characters(5)
        mock_resp = _make_mock_response(raw)

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=5)

        assert len(chars) == 5

    @pytest.mark.asyncio
    async def test_all_fields_populated(self, sample_world):
        """All required fields are populated on generated characters."""
        raw = _sample_raw_characters(5)
        mock_resp = _make_mock_response(raw)

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=5)

        for char in chars:
            assert char.name, f"Character missing name: {char}"
            assert char.persona, f"Character missing persona: {char.name}"
            assert char.hidden_role, f"Character missing hidden_role: {char.name}"
            assert char.faction, f"Character missing faction: {char.name}"
            assert char.win_condition, f"Character missing win_condition: {char.name}"
            assert char.id, f"Character missing id: {char.name}"

    @pytest.mark.asyncio
    async def test_unique_ids(self, sample_world):
        """All characters have unique IDs."""
        raw = _sample_raw_characters(5)
        mock_resp = _make_mock_response(raw)

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=5)

        ids = [c.id for c in chars]
        assert len(set(ids)) == len(ids), f"Duplicate IDs found: {ids}"

    @pytest.mark.asyncio
    async def test_hidden_info_not_in_public(self, sample_world):
        """Hidden fields are not exposed in CharacterPublicInfo."""
        raw = _sample_raw_characters(3)
        mock_resp = _make_mock_response(raw)

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=3)

        for char in chars:
            public = CharacterPublicInfo(
                id=char.id,
                name=char.name,
                persona=char.persona,
                speaking_style=char.speaking_style,
                avatar_seed=char.avatar_seed,
                public_role=char.public_role,
                voice_id=char.voice_id,
                is_eliminated=char.is_eliminated,
            )
            public_dict = public.model_dump()
            assert "hidden_role" not in public_dict
            assert "hidden_knowledge" not in public_dict
            assert "faction" not in public_dict
            assert "win_condition" not in public_dict
            assert "behavioral_rules" not in public_dict

    @pytest.mark.asyncio
    async def test_voice_ids_from_valid_pool(self, sample_world):
        """Voice IDs come from the VOICE_POOL."""
        raw = _sample_raw_characters(5)
        mock_resp = _make_mock_response(raw)

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=5)

        for char in chars:
            assert char.voice_id in VOICE_POOL, (
                f"{char.name} has invalid voice_id: {char.voice_id}"
            )

    @pytest.mark.asyncio
    async def test_num_characters_clamped_min(self, sample_world):
        """Requesting fewer than 3 characters still gives at least 3."""
        raw = _sample_raw_characters(3)
        mock_resp = _make_mock_response(raw)

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=1)

        # The factory clamps to max(3, min(num, 8)), so at least 3
        assert len(chars) >= 3

    @pytest.mark.asyncio
    async def test_num_characters_clamped_max(self, sample_world):
        """Requesting more than 8 characters caps at 8."""
        raw = _sample_raw_characters(8)
        mock_resp = _make_mock_response(raw)

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=20)

        assert len(chars) <= 8

    @pytest.mark.asyncio
    async def test_fallback_on_api_failure(self, sample_world):
        """Factory falls back to default characters on API error."""
        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(
                side_effect=Exception("API error")
            )
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=5)

        assert len(chars) > 0
        for char in chars:
            assert char.name
            assert char.faction

    @pytest.mark.asyncio
    async def test_fallback_on_empty_response(self, sample_world):
        """Factory falls back if LLM returns empty characters list."""
        mock_resp = _make_mock_response([])

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(return_value=mock_resp)
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=5)

        assert len(chars) > 0

    @pytest.mark.asyncio
    async def test_fallback_characters_have_factions(self, sample_world):
        """Fallback characters have correct faction assignments."""
        with patch("backend.game.character_factory.Mistral") as MockMistral:
            MockMistral.return_value.chat.complete_async = AsyncMock(
                side_effect=Exception("API error")
            )
            factory = CharacterFactory()
            chars = await factory.generate_characters(sample_world, num_characters=5)

        factions = {c.faction for c in chars}
        assert len(factions) > 0
        for char in chars:
            assert char.faction in factions
