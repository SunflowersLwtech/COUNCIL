"""Integration tests for night phase flow.

Tests the full night phase cycle including transitions, action resolution,
and multi-round flows. All Mistral API calls are mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.game_models import (
    GameState,
    Character,
    NightAction,
    VoteRecord,
    VoteResult,
)
from backend.game.state import (
    advance_to_night,
    advance_to_discussion,
    advance_to_voting,
    advance_to_reveal,
    end_game,
    eliminate_character,
    get_alive_characters,
    InvalidTransition,
)


def _make_characters():
    """Create a standard 5-character setup for testing."""
    return [
        Character(
            id="v1", name="Villager 1", persona="Farmer",
            faction="Village", hidden_role="Villager",
            voice_id="George",
        ),
        Character(
            id="v2", name="Villager 2", persona="Baker",
            faction="Village", hidden_role="Villager",
            voice_id="Sarah",
        ),
        Character(
            id="seer", name="The Seer", persona="Mystic",
            faction="Village", hidden_role="Seer",
            voice_id="Harry",
        ),
        Character(
            id="w1", name="Wolf Alpha", persona="Hunter",
            faction="Werewolf", hidden_role="Werewolf",
            voice_id="James",
        ),
        Character(
            id="w2", name="Wolf Beta", persona="Smith",
            faction="Werewolf", hidden_role="Werewolf",
            voice_id="Emily",
        ),
    ]


def _make_game_state(phase="discussion", round_num=1):
    """Create a game state at the given phase."""
    return GameState(
        session_id="test-night-flow",
        phase=phase,
        round=round_num,
        characters=_make_characters(),
    )


# ── Full Night Phase Flow ────────────────────────────────────────────


class TestNightPhaseFlow:
    def test_reveal_to_night_to_discussion(self):
        """Full flow: reveal -> night -> discussion with round increment."""
        state = _make_game_state(phase="reveal", round_num=1)

        # reveal -> night
        state = advance_to_night(state)
        assert state.phase == "night"
        assert state.night_actions == []
        assert state.round == 1  # round not incremented yet

        # night -> discussion (round increments)
        state = advance_to_discussion(state)
        assert state.phase == "discussion"
        assert state.round == 2

    def test_night_actions_recorded_then_cleared(self):
        """Night actions are recorded during night, cleared on next night."""
        state = _make_game_state(phase="reveal", round_num=1)

        # Enter night
        state = advance_to_night(state)
        assert state.night_actions == []

        # Simulate night actions
        state.night_actions = [
            NightAction(character_id="w1", action_type="kill", target_id="v1"),
            NightAction(character_id="seer", action_type="investigate", target_id="w1"),
        ]
        assert len(state.night_actions) == 2

        # Advance to discussion, then back through to night
        state = advance_to_discussion(state)
        state = advance_to_voting(state)
        state = advance_to_reveal(state)
        state = advance_to_night(state)

        # Night actions should be cleared for the new night
        assert state.night_actions == []


# ── Night Action Resolution ──────────────────────────────────────────


class TestNightActionResolution:
    def test_kill_eliminates_target(self):
        """A kill action during night eliminates the target."""
        state = _make_game_state(phase="night")
        state.night_actions = [
            NightAction(character_id="w1", action_type="kill", target_id="v1",
                        result="Villager 1 was killed."),
        ]

        # Simulate resolving the kill
        state = eliminate_character(state, "v1")

        alive = get_alive_characters(state)
        alive_ids = [c.id for c in alive]
        assert "v1" not in alive_ids
        assert len(alive) == 4

    def test_protect_saves_kill_target(self):
        """A protect action can cancel a kill (application-level logic)."""
        state = _make_game_state(phase="night")
        state.night_actions = [
            NightAction(character_id="w1", action_type="kill", target_id="v1"),
            NightAction(character_id="seer", action_type="protect", target_id="v1"),
        ]

        # Simulate resolution: kill canceled by protect
        kill_target = state.night_actions[0].target_id
        protect_targets = [
            a.target_id for a in state.night_actions
            if a.action_type == "protect"
        ]

        if kill_target in protect_targets:
            # Target is protected, do not eliminate
            pass
        else:
            state = eliminate_character(state, kill_target)

        # v1 should still be alive
        alive = get_alive_characters(state)
        alive_ids = [c.id for c in alive]
        assert "v1" in alive_ids
        assert len(alive) == 5

    def test_investigation_reveals_faction(self):
        """An investigate action records the target's faction."""
        state = _make_game_state(phase="night")
        wolf_char = next(c for c in state.characters if c.id == "w1")

        na = NightAction(
            character_id="seer",
            action_type="investigate",
            target_id="w1",
            result=f"{wolf_char.name} is a {wolf_char.faction}.",
        )
        state.night_actions.append(na)

        assert len(state.night_actions) == 1
        assert "Werewolf" in state.night_actions[0].result


# ── Multi-Round Game Flow ────────────────────────────────────────────


class TestMultiRoundGameFlow:
    def test_two_rounds_with_elimination(self):
        """Two full rounds with night phase and elimination."""
        state = _make_game_state(phase="discussion", round_num=1)

        # Round 1: discussion -> voting -> reveal -> night -> discussion
        state = advance_to_voting(state)
        state = advance_to_reveal(state)

        # Eliminate a character during reveal
        state = eliminate_character(state, "v1")
        assert "v1" in state.eliminated

        state = advance_to_night(state)
        assert state.phase == "night"

        # Night actions: wolf kills another villager
        state.night_actions = [
            NightAction(character_id="w1", action_type="kill", target_id="v2"),
        ]
        state = eliminate_character(state, "v2")

        state = advance_to_discussion(state)
        assert state.round == 2
        assert len(get_alive_characters(state)) == 3  # seer + 2 wolves

    def test_game_ends_at_reveal_not_night(self):
        """Game can end at reveal without entering night phase."""
        state = _make_game_state(phase="reveal")

        # Eliminate enough characters for evil to win
        state = eliminate_character(state, "v1")
        state = eliminate_character(state, "v2")
        state = eliminate_character(state, "seer")

        # Check: 0 good alive, 2 evil alive -> evil wins
        alive = get_alive_characters(state)
        good_alive = [c for c in alive if c.faction != "Werewolf"]
        evil_alive = [c for c in alive if c.faction == "Werewolf"]
        assert len(good_alive) == 0
        assert len(evil_alive) == 2

        # End game instead of going to night
        state = end_game(state, "Werewolf")
        assert state.phase == "ended"
        assert state.winner == "Werewolf"

    def test_three_round_cycle(self):
        """Three complete rounds maintain correct round count."""
        state = _make_game_state(phase="discussion", round_num=1)

        for expected_round in range(1, 4):
            assert state.round == expected_round
            state = advance_to_voting(state)
            state = advance_to_reveal(state)
            state = advance_to_night(state)
            state = advance_to_discussion(state)

        assert state.round == 4


# ── Edge Cases ───────────────────────────────────────────────────────


class TestNightEdgeCases:
    def test_empty_night_actions(self):
        """Night phase can have zero actions."""
        state = _make_game_state(phase="reveal")
        state = advance_to_night(state)
        assert state.night_actions == []

        # Can still advance to discussion
        state = advance_to_discussion(state)
        assert state.phase == "discussion"

    def test_multiple_kills_in_one_night(self):
        """Multiple kill actions can happen in one night."""
        state = _make_game_state(phase="night")
        state.night_actions = [
            NightAction(character_id="w1", action_type="kill", target_id="v1"),
            NightAction(character_id="w2", action_type="kill", target_id="v2"),
        ]
        assert len(state.night_actions) == 2

    def test_night_does_not_increment_round(self):
        """Entering night phase does not change the round counter."""
        state = _make_game_state(phase="reveal", round_num=2)
        state = advance_to_night(state)
        assert state.round == 2  # unchanged

    def test_discussion_from_night_increments_round(self):
        """Leaving night to discussion increments the round."""
        state = _make_game_state(phase="night", round_num=2)
        state = advance_to_discussion(state)
        assert state.round == 3
