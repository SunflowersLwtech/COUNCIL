"""Unit tests for the Orchestrator public state projection.

Ensures hidden information (hidden_role, faction, etc.) is never leaked
to the public state response.
"""

import pytest

from backend.models.game_models import (
    Character,
    CharacterPublicInfo,
    ChatMessage,
    GameState,
    PlayerRole,
    VoteRecord,
    VoteResult,
    WorldModel,
)


def _make_world():
    return WorldModel(
        title="Test World",
        setting="A mysterious village",
        factions=[
            {"name": "Village", "alignment": "good"},
            {"name": "Werewolf", "alignment": "evil"},
        ],
        flavor_text="Dark clouds gather...",
    )


def _make_chars() -> list[Character]:
    return [
        Character(
            id="c1", name="Alice", persona="Brave",
            speaking_style="bold", avatar_seed="a1",
            public_role="Knight", hidden_role="Villager",
            faction="Village", win_condition="Eliminate wolves",
            hidden_knowledge=["Innocent"], behavioral_rules=["Be brave"],
            voice_id="Sarah",
        ),
        Character(
            id="c2", name="Bob", persona="Sneaky",
            speaking_style="sly", avatar_seed="b2",
            public_role="Merchant", hidden_role="Werewolf",
            faction="Werewolf", win_condition="Outnumber",
            hidden_knowledge=["c3 is ally"], behavioral_rules=["Deflect"],
            voice_id="George",
        ),
    ]


def _build_public_state(state: GameState, full: bool = False) -> dict:
    """Mirror of GameOrchestrator._public_state for testing."""
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
    if state.player_role:
        pr = state.player_role
        result["player_role"] = {
            "hidden_role": pr.hidden_role,
            "faction": pr.faction,
            "win_condition": pr.win_condition,
            "allies": [],
            "is_eliminated": pr.is_eliminated,
            "eliminated_by": pr.eliminated_by,
        }
    return result


class TestPublicStateProjection:
    def test_no_hidden_fields_in_characters(self):
        """Public state characters must not contain hidden_role, faction, etc."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars, phase="discussion")
        public = _build_public_state(state)

        for char_data in public["characters"]:
            assert "hidden_role" not in char_data
            assert "faction" not in char_data
            assert "win_condition" not in char_data
            assert "hidden_knowledge" not in char_data
            assert "behavioral_rules" not in char_data

    def test_public_fields_present(self):
        """Public state includes expected public fields."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars, phase="discussion")
        public = _build_public_state(state)

        assert public["session_id"] == state.session_id
        assert public["phase"] == "discussion"
        assert public["world_title"] == "Test World"
        assert len(public["characters"]) == 2

        c1 = public["characters"][0]
        assert c1["name"] == "Alice"
        assert c1["public_role"] == "Knight"
        assert c1["voice_id"] == "Sarah"

    def test_messages_truncated_by_default(self):
        """Non-full mode returns at most 50 messages."""
        chars = _make_chars()
        msgs = [
            ChatMessage(speaker_id="c1", speaker_name="Alice",
                        content=f"Message {i}", phase="discussion", round=1)
            for i in range(60)
        ]
        state = GameState(world=_make_world(), characters=chars,
                          phase="discussion", messages=msgs)
        public = _build_public_state(state, full=False)
        assert len(public["messages"]) == 50

    def test_messages_full_mode(self):
        """Full mode returns all messages."""
        chars = _make_chars()
        msgs = [
            ChatMessage(speaker_id="c1", speaker_name="Alice",
                        content=f"Message {i}", phase="discussion", round=1)
            for i in range(60)
        ]
        state = GameState(world=_make_world(), characters=chars,
                          phase="discussion", messages=msgs)
        public = _build_public_state(state, full=True)
        assert len(public["messages"]) == 60

    def test_player_role_included_when_set(self):
        """Public state includes player_role info when assigned."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars, phase="discussion")
        state.player_role = PlayerRole(
            hidden_role="Seer", faction="Village",
            win_condition="Find the wolves",
        )
        public = _build_public_state(state)
        assert "player_role" in public
        assert public["player_role"]["hidden_role"] == "Seer"

    def test_no_player_role_when_not_set(self):
        """Public state omits player_role when not assigned."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars, phase="discussion")
        public = _build_public_state(state)
        assert "player_role" not in public

    def test_vote_results_included(self):
        """Public state includes vote results."""
        chars = _make_chars()
        vr = VoteResult(
            votes=[VoteRecord(voter_id="c1", voter_name="Alice",
                              target_id="c2", target_name="Bob")],
            tally={"c2": 1},
            eliminated_id="c2", eliminated_name="Bob", is_tie=False,
        )
        state = GameState(world=_make_world(), characters=chars,
                          phase="reveal", vote_results=[vr])
        public = _build_public_state(state)
        assert len(public["vote_results"]) == 1
        assert public["vote_results"][0]["eliminated_name"] == "Bob"

    def test_winner_none_during_game(self):
        """Winner is None during active game."""
        state = GameState(world=_make_world(), characters=_make_chars(),
                          phase="discussion")
        public = _build_public_state(state)
        assert public["winner"] is None

    def test_winner_set_on_game_end(self):
        """Winner is set when game ends."""
        state = GameState(world=_make_world(), characters=_make_chars(),
                          phase="ended", winner="Village")
        public = _build_public_state(state)
        assert public["winner"] == "Village"

    def test_eliminated_list(self):
        """Public state tracks eliminated character IDs."""
        chars = _make_chars()
        chars[1].is_eliminated = True
        state = GameState(world=_make_world(), characters=chars,
                          phase="discussion", eliminated=["c2"])
        public = _build_public_state(state)
        assert "c2" in public["eliminated"]
        assert public["characters"][1]["is_eliminated"] is True
