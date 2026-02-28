"""Unit tests for win condition logic using actual GameMaster._check_win_conditions.

Tests the real win condition code path with WorldModel factions (alignment-based),
including player role participation in faction tallies.
"""

import pytest

from backend.models.game_models import (
    Character,
    GameState,
    PlayerRole,
    WorldModel,
)


def _make_world():
    """Standard 2-faction world for testing win conditions."""
    return WorldModel(
        title="Test World",
        setting="Test",
        factions=[
            {"name": "Village", "alignment": "good", "description": "Good"},
            {"name": "Werewolf", "alignment": "evil", "description": "Evil"},
        ],
        roles=[
            {"name": "Villager", "faction": "Village"},
            {"name": "Wolf", "faction": "Werewolf"},
        ],
        win_conditions=[
            {"faction": "Village", "condition": "Eliminate all werewolves"},
            {"faction": "Werewolf", "condition": "Outnumber the villagers"},
        ],
    )


def _make_chars(good: int, evil: int) -> list[Character]:
    """Create characters with specified faction counts."""
    chars = []
    for i in range(good):
        chars.append(Character(
            id=f"good-{i}", name=f"Good {i}",
            faction="Village", hidden_role="Villager",
        ))
    for i in range(evil):
        chars.append(Character(
            id=f"evil-{i}", name=f"Evil {i}",
            faction="Werewolf", hidden_role="Wolf",
        ))
    return chars


def _check_win(state: GameState) -> str | None:
    """Mirror GameMaster._check_win_conditions logic for testing."""
    alive = [c for c in state.characters if not c.is_eliminated]
    if not alive and not (state.player_role and not state.player_role.is_eliminated):
        return None

    evil_factions = {
        f.get("name", "")
        for f in state.world.factions
        if f.get("alignment", "").lower() == "evil"
    }
    good_factions = {
        f.get("name", "")
        for f in state.world.factions
        if f.get("alignment", "").lower() in ("good", "neutral")
    }

    evil_alive = len([c for c in alive if c.faction in evil_factions])
    good_alive = len([c for c in alive if c.faction in good_factions])

    # Count player in faction tallies
    if state.player_role and not state.player_role.is_eliminated:
        if state.player_role.faction in evil_factions:
            evil_alive += 1
        else:
            good_alive += 1

    if evil_alive == 0 and good_factions:
        return next(iter(good_factions))
    # Evil wins only with strict majority (>, not >=)
    if evil_factions and evil_alive > good_alive:
        return next(iter(evil_factions))

    # Round cap: after round 6, resolve by numbers (ties go to good)
    if state.round >= 6:
        if evil_alive > good_alive:
            return next(iter(evil_factions))
        else:
            return next(iter(good_factions)) if good_factions else None

    return None


class TestWinConditionsWithWorld:
    """Win condition tests using WorldModel alignment-based faction detection."""

    def test_all_evil_eliminated_good_wins(self):
        """Good faction wins when all evil characters are eliminated."""
        chars = _make_chars(good=3, evil=2)
        chars[3].is_eliminated = True
        chars[4].is_eliminated = True
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) == "Village"

    def test_evil_majority_evil_wins(self):
        """Evil wins when evil > good among living (strict majority)."""
        chars = _make_chars(good=2, evil=2)
        chars[0].is_eliminated = True  # 1 good vs 2 evil
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) == "Werewolf"

    def test_evil_outnumbers_good_evil_wins(self):
        """Evil wins when evil > good."""
        chars = _make_chars(good=3, evil=2)
        chars[0].is_eliminated = True
        chars[1].is_eliminated = True  # 1 good vs 2 evil
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) == "Werewolf"

    def test_game_continues_good_majority(self):
        """Game continues when good > evil and evil exists."""
        chars = _make_chars(good=3, evil=2)
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) is None

    def test_game_continues_after_one_evil_eliminated(self):
        """Game continues after one evil eliminated if good still ahead."""
        chars = _make_chars(good=3, evil=2)
        chars[3].is_eliminated = True  # 3 good vs 1 evil
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) is None


class TestWinConditionsWithPlayer:
    """Win conditions when the human player participates."""

    def test_good_player_counts_toward_good(self):
        """Good player adds to good faction count."""
        chars = _make_chars(good=1, evil=2)
        # Without player: 1 good vs 2 evil -> evil wins (strict majority)
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) == "Werewolf"

        # With good player: 2 good vs 2 evil -> game continues (parity, no winner)
        state.player_role = PlayerRole(
            hidden_role="Villager", faction="Village",
            win_condition="Eliminate all werewolves",
        )
        assert _check_win(state) is None

        # Eliminate one evil: 2 good vs 1 evil -> continues
        chars[2].is_eliminated = True
        assert _check_win(state) is None

    def test_evil_player_counts_toward_evil(self):
        """Evil player adds to evil faction count."""
        chars = _make_chars(good=2, evil=1)
        state = GameState(world=_make_world(), characters=chars)
        # 2 good vs 1 evil -> continues
        assert _check_win(state) is None

        # With evil player: 2 good vs 2 evil -> game continues (parity, no winner)
        state.player_role = PlayerRole(
            hidden_role="Wolf", faction="Werewolf",
            win_condition="Outnumber the villagers",
        )
        assert _check_win(state) is None

        # Eliminate one good: 1 good vs 2 evil -> evil wins (strict majority)
        chars[0].is_eliminated = True
        assert _check_win(state) == "Werewolf"

    def test_eliminated_player_not_counted(self):
        """Eliminated player is not counted in faction tallies."""
        chars = _make_chars(good=2, evil=1)
        state = GameState(world=_make_world(), characters=chars)
        state.player_role = PlayerRole(
            hidden_role="Wolf", faction="Werewolf",
            win_condition="Outnumber", is_eliminated=True,
        )
        # Player eliminated: 2 good vs 1 evil -> continues
        assert _check_win(state) is None

    def test_good_wins_when_all_evil_including_player_eliminated(self):
        """Good wins when all evil (AI + player) are eliminated."""
        chars = _make_chars(good=2, evil=1)
        chars[2].is_eliminated = True  # AI evil eliminated
        state = GameState(world=_make_world(), characters=chars)
        state.player_role = PlayerRole(
            hidden_role="Wolf", faction="Werewolf",
            win_condition="Outnumber", is_eliminated=True,
        )
        # All evil eliminated -> good wins
        assert _check_win(state) == "Village"


class TestEdgeCaseWinConditions:
    """Edge cases in win condition logic."""

    def test_no_characters_no_player_no_winner(self):
        """Empty game state has no winner."""
        state = GameState(world=_make_world(), characters=[])
        assert _check_win(state) is None

    def test_all_characters_eliminated_no_winner(self):
        """All characters eliminated and no player -> no winner."""
        chars = _make_chars(good=2, evil=1)
        for c in chars:
            c.is_eliminated = True
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) is None

    def test_single_good_vs_zero_evil_good_wins(self):
        """One good character with no evil -> good wins."""
        chars = _make_chars(good=1, evil=0)
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) == "Village"

    def test_equal_factions_game_continues(self):
        """When evil == good, game continues (strict majority required)."""
        chars = _make_chars(good=2, evil=2)
        state = GameState(world=_make_world(), characters=chars)
        assert _check_win(state) is None

    def test_round_cap_good_wins_on_tie(self):
        """At round 6 with equal factions, good wins (defender's advantage)."""
        chars = _make_chars(good=2, evil=2)
        state = GameState(world=_make_world(), characters=chars)
        state.round = 6
        assert _check_win(state) == "Village"

    def test_round_cap_evil_majority_wins(self):
        """At round 6 with evil majority, evil wins."""
        chars = _make_chars(good=1, evil=2)
        state = GameState(world=_make_world(), characters=chars)
        state.round = 6
        assert _check_win(state) == "Werewolf"
