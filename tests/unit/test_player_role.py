"""Unit tests for player role assignment and related state logic."""

import pytest
from unittest.mock import patch
import random

from backend.models.game_models import (
    Character,
    GameState,
    PlayerRole,
    WorldModel,
)
from backend.game.state import eliminate_character, get_alive_characters


def _make_world():
    return WorldModel(
        title="Test World",
        setting="Test",
        factions=[
            {"name": "Village", "alignment": "good"},
            {"name": "Werewolf", "alignment": "evil"},
        ],
        roles=[
            {"name": "Villager", "faction": "Village", "ability": "None"},
            {"name": "Seer", "faction": "Village", "ability": "Investigate"},
            {"name": "Doctor", "faction": "Village", "ability": "Protect"},
            {"name": "Wolf", "faction": "Werewolf", "ability": "Kill"},
        ],
        win_conditions=[
            {"faction": "Village", "condition": "Eliminate all werewolves"},
            {"faction": "Werewolf", "condition": "Outnumber the villagers"},
        ],
    )


def _make_chars(good: int = 3, evil: int = 2) -> list[Character]:
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


class TestPlayerRoleModel:
    def test_default_player_role(self):
        """PlayerRole has safe defaults."""
        pr = PlayerRole()
        assert pr.hidden_role == ""
        assert pr.faction == ""
        assert pr.is_eliminated is False
        assert pr.eliminated_by == ""
        assert pr.allies == []

    def test_player_role_with_data(self):
        """PlayerRole stores all role data."""
        pr = PlayerRole(
            hidden_role="Seer",
            faction="Village",
            win_condition="Eliminate all werewolves",
            allies=[],
        )
        assert pr.hidden_role == "Seer"
        assert pr.faction == "Village"

    def test_evil_player_has_allies(self):
        """Evil player role includes ally character IDs."""
        pr = PlayerRole(
            hidden_role="Wolf",
            faction="Werewolf",
            win_condition="Outnumber the villagers",
            allies=["evil-0", "evil-1"],
        )
        assert len(pr.allies) == 2
        assert "evil-0" in pr.allies


class TestPlayerElimination:
    def test_player_vote_elimination(self):
        """Player can be eliminated by vote."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars)
        state.player_role = PlayerRole(
            hidden_role="Villager", faction="Village",
        )
        state = eliminate_character(state, "player")
        assert state.player_role.is_eliminated is True
        assert "player" in state.eliminated

    def test_player_night_kill_elimination(self):
        """Player can be eliminated by night kill."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars)
        state.player_role = PlayerRole(
            hidden_role="Villager", faction="Village",
        )
        state = eliminate_character(state, "player")
        state.player_role.eliminated_by = "night_kill"
        assert state.player_role.is_eliminated is True
        assert state.player_role.eliminated_by == "night_kill"

    def test_player_elimination_idempotent(self):
        """Eliminating the player twice doesn't duplicate in eliminated list."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars)
        state.player_role = PlayerRole(
            hidden_role="Villager", faction="Village",
        )
        state = eliminate_character(state, "player")
        state = eliminate_character(state, "player")
        assert state.eliminated.count("player") == 1


class TestPlayerRoleOnGameState:
    def test_game_state_player_role_default_none(self):
        """GameState.player_role is None by default."""
        state = GameState()
        assert state.player_role is None

    def test_game_state_with_player_role(self):
        """GameState can hold a PlayerRole."""
        state = GameState(
            player_role=PlayerRole(
                hidden_role="Seer", faction="Village",
                win_condition="Find the wolves",
            ),
        )
        assert state.player_role is not None
        assert state.player_role.hidden_role == "Seer"

    def test_awaiting_player_night_action_default_false(self):
        """GameState.awaiting_player_night_action defaults to False."""
        state = GameState()
        assert state.awaiting_player_night_action is False

    def test_awaiting_player_night_action_set(self):
        """GameState can flag awaiting player night action."""
        state = GameState(awaiting_player_night_action=True)
        assert state.awaiting_player_night_action is True


class TestNightActionTypeDetection:
    """Test the logic that determines what night action the player can perform."""

    def _get_action_type(self, state: GameState) -> str | None:
        """Mirror orchestrator._get_player_night_action_type logic."""
        if not state.player_role or state.player_role.is_eliminated:
            return None
        role = state.player_role.hidden_role.lower()
        evil_factions = {
            f.get("name", "")
            for f in state.world.factions
            if f.get("alignment", "").lower() == "evil"
        }
        if state.player_role.faction in evil_factions:
            return "kill"
        if "seer" in role or "investigat" in role:
            return "investigate"
        if "doctor" in role or "protect" in role:
            return "protect"
        return None

    def test_evil_player_gets_kill(self):
        state = GameState(world=_make_world())
        state.player_role = PlayerRole(hidden_role="Wolf", faction="Werewolf")
        assert self._get_action_type(state) == "kill"

    def test_seer_player_gets_investigate(self):
        state = GameState(world=_make_world())
        state.player_role = PlayerRole(hidden_role="Seer", faction="Village")
        assert self._get_action_type(state) == "investigate"

    def test_doctor_player_gets_protect(self):
        state = GameState(world=_make_world())
        state.player_role = PlayerRole(hidden_role="Doctor", faction="Village")
        assert self._get_action_type(state) == "protect"

    def test_villager_gets_none(self):
        state = GameState(world=_make_world())
        state.player_role = PlayerRole(hidden_role="Villager", faction="Village")
        assert self._get_action_type(state) is None

    def test_eliminated_player_gets_none(self):
        state = GameState(world=_make_world())
        state.player_role = PlayerRole(
            hidden_role="Seer", faction="Village", is_eliminated=True,
        )
        assert self._get_action_type(state) is None

    def test_no_player_role_gets_none(self):
        state = GameState(world=_make_world())
        assert self._get_action_type(state) is None
