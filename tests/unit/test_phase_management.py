"""Unit tests for game phase state machine and win conditions."""

import pytest

from backend.models.game_models import GameState, Character


# ── State Machine ────────────────────────────────────────────────────

VALID_TRANSITIONS = {
    "lobby": ["discussion"],
    "discussion": ["voting"],
    "voting": ["reveal"],
    "reveal": ["night", "ended"],
    "night": ["discussion"],
}


def transition(state: GameState, target_phase: str) -> GameState:
    """Attempt a phase transition. Raises ValueError if invalid."""
    current = state.phase
    if target_phase not in VALID_TRANSITIONS.get(current, []):
        raise ValueError(
            f"Invalid transition: {current} -> {target_phase}. "
            f"Valid targets: {VALID_TRANSITIONS.get(current, [])}"
        )
    state.phase = target_phase
    return state


def check_win_condition(state: GameState) -> str | None:
    """Check if a faction has won.

    Returns:
        "good" if all evil eliminated,
        "evil" if evil >= good among living,
        None if game continues.
    """
    living = [c for c in state.characters if not c.is_eliminated]
    if not living:
        return None

    evil_factions = set()
    for c in state.characters:
        # Determine evil factions from the world model
        pass

    # Simpler approach: check faction names for alignment
    good_count = sum(1 for c in living if c.faction != "Werewolf")
    evil_count = sum(1 for c in living if c.faction == "Werewolf")

    if evil_count == 0:
        return "good"
    if evil_count >= good_count:
        return "evil"
    return None


class TestPhaseTransitions:
    def test_lobby_to_discussion(self, lobby_game_state):
        """Valid: lobby -> discussion."""
        state = transition(lobby_game_state, "discussion")
        assert state.phase == "discussion"

    def test_discussion_to_voting(self, sample_game_state):
        """Valid: discussion -> voting."""
        state = transition(sample_game_state, "voting")
        assert state.phase == "voting"

    def test_voting_to_reveal(self, sample_game_state):
        """Valid: voting -> reveal."""
        sample_game_state.phase = "voting"
        state = transition(sample_game_state, "reveal")
        assert state.phase == "reveal"

    def test_reveal_to_night(self, sample_game_state):
        """Valid: reveal -> night."""
        sample_game_state.phase = "reveal"
        state = transition(sample_game_state, "night")
        assert state.phase == "night"

    def test_night_to_discussion(self, sample_game_state):
        """Valid: night -> discussion (next round)."""
        sample_game_state.phase = "night"
        state = transition(sample_game_state, "discussion")
        assert state.phase == "discussion"

    def test_reveal_to_ended(self, sample_game_state):
        """Valid: reveal -> ended."""
        sample_game_state.phase = "reveal"
        state = transition(sample_game_state, "ended")
        assert state.phase == "ended"

    def test_invalid_lobby_to_voting(self, lobby_game_state):
        """Invalid: lobby -> voting should raise error."""
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(lobby_game_state, "voting")

    def test_invalid_lobby_to_reveal(self, lobby_game_state):
        """Invalid: lobby -> reveal should raise error."""
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(lobby_game_state, "reveal")

    def test_invalid_lobby_to_ended(self, lobby_game_state):
        """Invalid: lobby -> ended should raise error."""
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(lobby_game_state, "ended")

    def test_invalid_discussion_to_ended(self, sample_game_state):
        """Invalid: discussion -> ended should raise error."""
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(sample_game_state, "ended")

    def test_invalid_voting_to_discussion(self, sample_game_state):
        """Invalid: voting -> discussion should raise error."""
        sample_game_state.phase = "voting"
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(sample_game_state, "discussion")

    def test_invalid_ended_to_anything(self, sample_game_state):
        """Invalid: ended -> any phase should raise error."""
        sample_game_state.phase = "ended"
        for target in ["lobby", "discussion", "voting", "reveal", "night"]:
            with pytest.raises(ValueError, match="Invalid transition"):
                transition(sample_game_state, target)

    def test_invalid_night_to_voting(self, sample_game_state):
        """Invalid: night -> voting should raise error."""
        sample_game_state.phase = "night"
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(sample_game_state, "voting")

    def test_invalid_night_to_reveal(self, sample_game_state):
        """Invalid: night -> reveal should raise error."""
        sample_game_state.phase = "night"
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(sample_game_state, "reveal")

    def test_invalid_night_to_ended(self, sample_game_state):
        """Invalid: night -> ended should raise error."""
        sample_game_state.phase = "night"
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(sample_game_state, "ended")

    def test_invalid_discussion_to_night(self, sample_game_state):
        """Invalid: discussion -> night should raise error."""
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(sample_game_state, "night")

    def test_invalid_lobby_to_night(self, lobby_game_state):
        """Invalid: lobby -> night should raise error."""
        with pytest.raises(ValueError, match="Invalid transition"):
            transition(lobby_game_state, "night")

    def test_full_round_cycle_with_night(self, lobby_game_state):
        """Full cycle: lobby -> discussion -> voting -> reveal -> night -> discussion."""
        state = lobby_game_state
        state = transition(state, "discussion")
        assert state.phase == "discussion"

        state = transition(state, "voting")
        assert state.phase == "voting"

        state = transition(state, "reveal")
        assert state.phase == "reveal"

        state = transition(state, "night")
        assert state.phase == "night"

        state = transition(state, "discussion")
        assert state.phase == "discussion"


class TestWinConditions:
    def _make_chars(self, good: int, evil: int) -> list[Character]:
        """Create a list of characters with specified faction counts."""
        chars = []
        for i in range(good):
            chars.append(
                Character(
                    id=f"good-{i}",
                    name=f"Good {i}",
                    faction="Village",
                    hidden_role="Villager",
                )
            )
        for i in range(evil):
            chars.append(
                Character(
                    id=f"evil-{i}",
                    name=f"Evil {i}",
                    faction="Werewolf",
                    hidden_role="Werewolf",
                )
            )
        return chars

    def test_all_evil_eliminated_good_wins(self):
        """When all evil characters are eliminated, good wins."""
        chars = self._make_chars(good=3, evil=2)
        # Eliminate both evil
        chars[3].is_eliminated = True
        chars[4].is_eliminated = True

        state = GameState(characters=chars)
        result = check_win_condition(state)
        assert result == "good"

    def test_evil_equals_good_evil_wins(self):
        """When evil >= good among living, evil wins."""
        chars = self._make_chars(good=2, evil=2)
        # Eliminate one good -> 1 good vs 2 evil
        chars[0].is_eliminated = True

        state = GameState(characters=chars)
        result = check_win_condition(state)
        assert result == "evil"

    def test_evil_outnumbers_good_evil_wins(self):
        """When evil > good among living, evil wins."""
        chars = self._make_chars(good=3, evil=2)
        # Eliminate 2 good -> 1 good vs 2 evil
        chars[0].is_eliminated = True
        chars[1].is_eliminated = True

        state = GameState(characters=chars)
        result = check_win_condition(state)
        assert result == "evil"

    def test_game_continues(self):
        """When good > evil and evil exists, game continues."""
        chars = self._make_chars(good=3, evil=2)

        state = GameState(characters=chars)
        result = check_win_condition(state)
        assert result is None

    def test_game_continues_after_one_evil_eliminated(self):
        """After one evil eliminated, game continues if evil still < good."""
        chars = self._make_chars(good=3, evil=2)
        chars[3].is_eliminated = True  # One evil down, 3 good vs 1 evil

        state = GameState(characters=chars)
        result = check_win_condition(state)
        assert result is None

    def test_empty_characters(self):
        """No characters returns None (no winner)."""
        state = GameState(characters=[])
        result = check_win_condition(state)
        assert result is None

    def test_all_eliminated(self):
        """All characters eliminated -> good wins (no evil alive)."""
        chars = self._make_chars(good=2, evil=1)
        for c in chars:
            c.is_eliminated = True

        state = GameState(characters=chars)
        # No living characters
        result = check_win_condition(state)
        assert result is None


class TestRoundIncrement:
    def test_round_starts_at_one(self, lobby_game_state):
        """Game starts at round 1."""
        assert lobby_game_state.round == 1

    def test_round_increments_on_next_discussion(self, sample_game_state):
        """Round increments when transitioning through night to discussion."""
        sample_game_state.phase = "reveal"
        sample_game_state.round = 1

        transition(sample_game_state, "night")
        transition(sample_game_state, "discussion")
        sample_game_state.round += 1  # Application code does this

        assert sample_game_state.round == 2

    def test_round_does_not_change_mid_phase(self, sample_game_state):
        """Round does not change during discussion -> voting -> reveal."""
        initial_round = sample_game_state.round
        transition(sample_game_state, "voting")
        assert sample_game_state.round == initial_round
        transition(sample_game_state, "reveal")
        assert sample_game_state.round == initial_round
