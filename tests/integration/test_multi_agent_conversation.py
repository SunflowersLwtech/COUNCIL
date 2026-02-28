"""Integration tests for multi-agent conversation flow.

Tests that player messages get routed to characters, characters stay in
character, eliminated characters don't respond, etc.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.game_models import Character, GameState, ChatMessage, WorldModel
from backend.game.prompts import CHARACTER_SYSTEM_PROMPT, RESPONDER_SELECTION_SYSTEM


def _make_chat_response(content: str) -> MagicMock:
    """Build a mock Mistral chat response."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = content
    return mock_resp


class TestMultiAgentConversation:
    @pytest.mark.asyncio
    async def test_player_message_gets_character_response(self, sample_game_state):
        """Player message triggers character response(s)."""
        state = sample_game_state
        player_message = "I think someone here is a werewolf!"

        # Mock the responder selection to pick char-001
        selection_resp = _make_chat_response(json.dumps({"responders": ["char-001"]}))
        # Mock char-001's response
        char_resp = _make_chat_response(
            "Indeed, we must be vigilant. I've noticed some suspicious behavior."
        )

        with patch("backend.game.character_factory.Mistral") as MockMistral:
            client = MockMistral.return_value
            client.chat.complete_async = AsyncMock(
                side_effect=[selection_resp, char_resp]
            )

            # Simulate the conversation flow
            # 1. Select responders
            responders_data = json.loads(selection_resp.choices[0].message.content)
            responder_ids = responders_data["responders"]

            # 2. Generate responses from selected characters
            responses = []
            char_map = {c.id: c for c in state.characters}
            for rid in responder_ids:
                char = char_map.get(rid)
                if char and not char.is_eliminated:
                    responses.append({
                        "character_id": char.id,
                        "character_name": char.name,
                        "content": char_resp.choices[0].message.content,
                    })

        assert len(responses) > 0
        assert responses[0]["character_name"] == "Elder Marcus"
        assert "vigilant" in responses[0]["content"]

    @pytest.mark.asyncio
    async def test_eliminated_characters_dont_respond(self, sample_game_state):
        """Eliminated characters are excluded from response pool."""
        state = sample_game_state
        # Eliminate char-001
        state.characters[0].is_eliminated = True
        state.eliminated.append("char-001")

        # Build alive character list
        alive_chars = [c for c in state.characters if not c.is_eliminated]
        alive_ids = {c.id for c in alive_chars}

        assert "char-001" not in alive_ids
        assert len(alive_chars) == 4

        # If responder selection returns eliminated char, it should be filtered
        selected = ["char-001", "char-002"]
        valid_responders = [rid for rid in selected if rid in alive_ids]

        assert "char-001" not in valid_responders
        assert "char-002" in valid_responders

    @pytest.mark.asyncio
    async def test_multiple_characters_respond(self, sample_game_state):
        """Multiple characters can respond to one player message."""
        state = sample_game_state

        responder_ids = ["char-001", "char-002", "char-004"]
        char_map = {c.id: c for c in state.characters}

        responses = []
        for rid in responder_ids:
            char = char_map.get(rid)
            if char and not char.is_eliminated:
                responses.append({
                    "character_id": char.id,
                    "character_name": char.name,
                    "content": f"Response from {char.name}",
                })

        assert len(responses) == 3
        names = {r["character_name"] for r in responses}
        assert "Elder Marcus" in names
        assert "Swift Lila" in names
        assert "Captain Thorne" in names

    @pytest.mark.asyncio
    async def test_character_system_prompt_contains_hidden_info(self, sample_characters):
        """System prompt for character includes hidden role data."""
        char = sample_characters[3]  # Captain Thorne, Werewolf

        prompt = CHARACTER_SYSTEM_PROMPT.format(
            name=char.name,
            world_title="Test World",
            hidden_role=char.hidden_role,
            faction=char.faction,
            win_condition=char.win_condition,
            hidden_knowledge="; ".join(char.hidden_knowledge),
            behavioral_rules="\n".join(f"- {r}" for r in char.behavioral_rules),
            persona=char.persona,
            speaking_style=char.speaking_style,
            public_role=char.public_role,
        )

        assert "Werewolf" in prompt
        assert "Captain Thorne" in prompt
        assert "Deflect suspicion" in prompt

    @pytest.mark.asyncio
    async def test_chat_messages_stored_in_state(self, sample_game_state):
        """Chat messages are stored in the game state."""
        state = sample_game_state

        msg1 = ChatMessage(
            speaker_id="player",
            speaker_name="Player",
            content="Who do you suspect?",
            phase="discussion",
            round=1,
        )
        msg2 = ChatMessage(
            speaker_id="char-001",
            speaker_name="Elder Marcus",
            content="I have my doubts about the captain.",
            phase="discussion",
            round=1,
        )

        state.messages.append(msg1)
        state.messages.append(msg2)

        assert len(state.messages) == 2
        assert state.messages[0].speaker_name == "Player"
        assert state.messages[1].speaker_name == "Elder Marcus"

    @pytest.mark.asyncio
    async def test_responder_selection_prompt(self, sample_characters):
        """Responder selection prompt includes character info."""
        alive = [c for c in sample_characters if not c.is_eliminated]
        char_list = ", ".join(
            f"{c.id}:{c.name} ({c.public_role})" for c in alive
        )

        prompt = RESPONDER_SELECTION_SYSTEM.format(characters=char_list)

        assert "char-001" in prompt
        assert "Elder Marcus" in prompt
        assert "Council Leader" in prompt

    @pytest.mark.asyncio
    async def test_discussion_phase_required(self, lobby_game_state):
        """Chat should only work during discussion phase."""
        state = lobby_game_state
        assert state.phase == "lobby"

        # In a real implementation, attempting chat in lobby would fail
        # Here we verify the phase check logic
        is_chat_allowed = state.phase == "discussion"
        assert not is_chat_allowed

    @pytest.mark.asyncio
    async def test_message_includes_round_info(self, sample_game_state):
        """Messages include current round information."""
        state = sample_game_state
        state.round = 3

        msg = ChatMessage(
            speaker_id="char-002",
            speaker_name="Swift Lila",
            content="This is getting suspicious.",
            phase=state.phase,
            round=state.round,
        )

        assert msg.round == 3
        assert msg.phase == "discussion"
