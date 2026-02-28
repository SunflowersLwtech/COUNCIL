"""Unit tests for night phase transitions and state machine logic."""

import pytest

from backend.models.game_models import GameState, Character, NightAction
from backend.game.state import (
    TRANSITIONS,
    InvalidTransition,
    transition,
    validate_transition,
    advance_to_night,
    advance_to_discussion,
    advance_to_voting,
    advance_to_reveal,
    end_game,
    eliminate_character,
    get_alive_characters,
)


# ── TRANSITIONS map includes night ──────────────────────────────────


class TestTransitionsMap:
    def test_night_in_transitions(self):
        """'night' should be a key in the TRANSITIONS map."""
        assert "night" in TRANSITIONS

    def test_reveal_targets_include_night(self):
        """reveal phase should be able to transition to night."""
        assert "night" in TRANSITIONS["reveal"]

    def test_night_targets_include_discussion(self):
        """night phase should transition to discussion."""
        assert "discussion" in TRANSITIONS["night"]

    def test_night_does_not_go_to_voting(self):
        """night should not transition directly to voting."""
        assert "voting" not in TRANSITIONS["night"]

    def test_night_does_not_go_to_reveal(self):
        """night should not transition directly to reveal."""
        assert "reveal" not in TRANSITIONS["night"]

    def test_night_does_not_go_to_ended(self):
        """night should not transition directly to ended."""
        assert "ended" not in TRANSITIONS["night"]

    def test_night_does_not_go_to_lobby(self):
        """night should not transition back to lobby."""
        assert "lobby" not in TRANSITIONS["night"]


# ── validate_transition for night ────────────────────────────────────


class TestValidateTransitionNight:
    def test_reveal_to_night_valid(self):
        """reveal -> night is a valid transition."""
        assert validate_transition("reveal", "night") is True

    def test_night_to_discussion_valid(self):
        """night -> discussion is a valid transition."""
        assert validate_transition("night", "discussion") is True

    def test_night_to_voting_invalid(self):
        """night -> voting is invalid."""
        assert validate_transition("night", "voting") is False

    def test_discussion_to_night_invalid(self):
        """discussion -> night is invalid."""
        assert validate_transition("discussion", "night") is False

    def test_lobby_to_night_invalid(self):
        """lobby -> night is invalid."""
        assert validate_transition("lobby", "night") is False

    def test_voting_to_night_invalid(self):
        """voting -> night is invalid."""
        assert validate_transition("voting", "night") is False


# ── transition() for night ───────────────────────────────────────────


class TestTransitionNight:
    def test_reveal_to_night(self, sample_game_state):
        """transition from reveal to night succeeds."""
        sample_game_state.phase = "reveal"
        state = transition(sample_game_state, "night")
        assert state.phase == "night"

    def test_night_to_discussion(self, sample_game_state):
        """transition from night to discussion succeeds."""
        sample_game_state.phase = "night"
        state = transition(sample_game_state, "discussion")
        assert state.phase == "discussion"

    def test_night_to_voting_raises(self, sample_game_state):
        """transition from night to voting raises InvalidTransition."""
        sample_game_state.phase = "night"
        with pytest.raises(InvalidTransition):
            transition(sample_game_state, "voting")

    def test_night_to_reveal_raises(self, sample_game_state):
        """transition from night to reveal raises InvalidTransition."""
        sample_game_state.phase = "night"
        with pytest.raises(InvalidTransition):
            transition(sample_game_state, "reveal")

    def test_night_to_ended_raises(self, sample_game_state):
        """transition from night to ended raises InvalidTransition."""
        sample_game_state.phase = "night"
        with pytest.raises(InvalidTransition):
            transition(sample_game_state, "ended")

    def test_night_to_lobby_raises(self, sample_game_state):
        """transition from night to lobby raises InvalidTransition."""
        sample_game_state.phase = "night"
        with pytest.raises(InvalidTransition):
            transition(sample_game_state, "lobby")

    def test_discussion_to_night_raises(self, sample_game_state):
        """transition from discussion to night raises InvalidTransition."""
        with pytest.raises(InvalidTransition):
            transition(sample_game_state, "night")


# ── advance_to_night() ──────────────────────────────────────────────


class TestAdvanceToNight:
    def test_advance_to_night_from_reveal(self, sample_game_state):
        """advance_to_night from reveal succeeds."""
        sample_game_state.phase = "reveal"
        state = advance_to_night(sample_game_state)
        assert state.phase == "night"

    def test_advance_to_night_clears_night_actions(self, sample_game_state):
        """advance_to_night clears existing night_actions."""
        sample_game_state.phase = "reveal"
        sample_game_state.night_actions = [
            NightAction(character_id="c1", action_type="kill"),
        ]
        state = advance_to_night(sample_game_state)
        assert state.night_actions == []

    def test_advance_to_night_from_discussion_raises(self, sample_game_state):
        """advance_to_night from discussion raises InvalidTransition."""
        with pytest.raises(InvalidTransition):
            advance_to_night(sample_game_state)

    def test_advance_to_night_from_lobby_raises(self, lobby_game_state):
        """advance_to_night from lobby raises InvalidTransition."""
        with pytest.raises(InvalidTransition):
            advance_to_night(lobby_game_state)

    def test_advance_to_night_from_voting_raises(self, sample_game_state):
        """advance_to_night from voting raises InvalidTransition."""
        sample_game_state.phase = "voting"
        with pytest.raises(InvalidTransition):
            advance_to_night(sample_game_state)

    def test_advance_to_night_from_night_raises(self, sample_game_state):
        """advance_to_night from night raises InvalidTransition."""
        sample_game_state.phase = "night"
        with pytest.raises(InvalidTransition):
            advance_to_night(sample_game_state)

    def test_advance_to_night_from_ended_raises(self, sample_game_state):
        """advance_to_night from ended raises InvalidTransition."""
        sample_game_state.phase = "ended"
        with pytest.raises(InvalidTransition):
            advance_to_night(sample_game_state)


# ── advance_to_discussion from night (round increment) ──────────────


class TestAdvanceToDiscussionFromNight:
    def test_night_to_discussion_increments_round(self, sample_game_state):
        """advance_to_discussion from night increments the round counter."""
        sample_game_state.phase = "night"
        sample_game_state.round = 1
        state = advance_to_discussion(sample_game_state)
        assert state.phase == "discussion"
        assert state.round == 2

    def test_night_to_discussion_clears_votes(self, sample_game_state):
        """advance_to_discussion from night clears votes for new round."""
        from backend.models.game_models import VoteRecord

        sample_game_state.phase = "night"
        sample_game_state.votes = [
            VoteRecord(voter_id="c1", target_id="c2"),
        ]
        state = advance_to_discussion(sample_game_state)
        assert state.votes == []

    def test_reveal_to_discussion_also_increments(self, sample_game_state):
        """advance_to_discussion from reveal also increments the round."""
        sample_game_state.phase = "reveal"
        sample_game_state.round = 2
        state = advance_to_discussion(sample_game_state)
        assert state.phase == "discussion"
        assert state.round == 3

    def test_night_to_discussion_round_3(self, sample_game_state):
        """Multiple round increments from night work correctly."""
        sample_game_state.phase = "night"
        sample_game_state.round = 3
        state = advance_to_discussion(sample_game_state)
        assert state.round == 4


# ── Full cycle with night ────────────────────────────────────────────


class TestFullCycleWithNight:
    def test_full_cycle_lobby_to_night_to_discussion(self, lobby_game_state):
        """Full cycle: lobby -> discussion -> voting -> reveal -> night -> discussion."""
        state = lobby_game_state

        # lobby -> discussion
        state = advance_to_discussion(state)
        assert state.phase == "discussion"
        assert state.round == 1

        # discussion -> voting
        state = advance_to_voting(state)
        assert state.phase == "voting"

        # voting -> reveal
        state = advance_to_reveal(state)
        assert state.phase == "reveal"

        # reveal -> night
        state = advance_to_night(state)
        assert state.phase == "night"
        assert state.night_actions == []

        # night -> discussion (round 2)
        state = advance_to_discussion(state)
        assert state.phase == "discussion"
        assert state.round == 2

    def test_two_full_rounds_with_night(self, lobby_game_state):
        """Two full rounds with night phase maintain correct round count."""
        state = lobby_game_state

        # Round 1
        state = advance_to_discussion(state)
        state = advance_to_voting(state)
        state = advance_to_reveal(state)
        state = advance_to_night(state)
        state = advance_to_discussion(state)
        assert state.round == 2

        # Round 2
        state = advance_to_voting(state)
        state = advance_to_reveal(state)
        state = advance_to_night(state)
        state = advance_to_discussion(state)
        assert state.round == 3

    def test_reveal_can_end_game_instead_of_night(self, lobby_game_state):
        """From reveal, game can end instead of going to night."""
        state = lobby_game_state
        state = advance_to_discussion(state)
        state = advance_to_voting(state)
        state = advance_to_reveal(state)

        # Instead of night, end the game
        state = end_game(state, "Village")
        assert state.phase == "ended"
        assert state.winner == "Village"


# ── NightAction model validation ─────────────────────────────────────


class TestNightActionModel:
    def test_night_action_defaults(self):
        """NightAction defaults match expected values."""
        na = NightAction()
        assert na.character_id == ""
        assert na.action_type == ""
        assert na.target_id is None
        assert na.result == ""

    def test_kill_action(self):
        """Kill night action stores all fields."""
        na = NightAction(
            character_id="wolf-001",
            action_type="kill",
            target_id="villager-001",
            result="The villager was eliminated.",
        )
        assert na.action_type == "kill"
        assert na.target_id == "villager-001"

    def test_investigate_action(self):
        """Investigate night action stores result."""
        na = NightAction(
            character_id="seer-001",
            action_type="investigate",
            target_id="suspect-001",
            result="suspect-001 is evil.",
        )
        assert na.action_type == "investigate"

    def test_protect_action(self):
        """Protect night action stores target."""
        na = NightAction(
            character_id="doctor-001",
            action_type="protect",
            target_id="villager-001",
            result="villager-001 was protected.",
        )
        assert na.action_type == "protect"

    def test_str_coercion_none(self):
        """None values coerce to empty string for str fields."""
        na = NightAction(character_id=None, action_type=None, result=None)
        assert na.character_id == ""
        assert na.action_type == ""
        assert na.result == ""

    def test_multiple_night_actions_on_state(self):
        """GameState can hold multiple night actions."""
        actions = [
            NightAction(character_id="w1", action_type="kill", target_id="v1"),
            NightAction(character_id="s1", action_type="investigate", target_id="w1"),
            NightAction(character_id="d1", action_type="protect", target_id="v1"),
        ]
        state = GameState(phase="night", night_actions=actions)
        assert len(state.night_actions) == 3
        types = [a.action_type for a in state.night_actions]
        assert types == ["kill", "investigate", "protect"]


# ── Night phase with character elimination ───────────────────────────


class TestNightElimination:
    def _make_game_in_night(self):
        """Helper: create a game state in night phase with characters."""
        chars = [
            Character(id="v1", name="Villager 1", faction="Village", hidden_role="Villager"),
            Character(id="v2", name="Villager 2", faction="Village", hidden_role="Villager"),
            Character(id="w1", name="Wolf 1", faction="Werewolf", hidden_role="Werewolf"),
        ]
        return GameState(phase="night", round=1, characters=chars)

    def test_eliminate_during_night(self):
        """Characters can be eliminated during night phase."""
        state = self._make_game_in_night()
        state = eliminate_character(state, "v1")
        assert "v1" in state.eliminated
        assert state.characters[0].is_eliminated is True

    def test_alive_after_night_elimination(self):
        """get_alive_characters reflects night eliminations."""
        state = self._make_game_in_night()
        state = eliminate_character(state, "v1")
        alive = get_alive_characters(state)
        alive_ids = [c.id for c in alive]
        assert "v1" not in alive_ids
        assert "v2" in alive_ids
        assert "w1" in alive_ids
