"""Unit tests for tension and complication injection logic."""

import pytest

from backend.models.game_models import (
    Character,
    ChatMessage,
    GameState,
    NightAction,
    WorldModel,
)


def _make_world():
    return WorldModel(
        title="Test",
        setting="Test",
        factions=[
            {"name": "Village", "alignment": "good"},
            {"name": "Werewolf", "alignment": "evil"},
        ],
    )


def _make_chars(good: int = 3, evil: int = 2) -> list[Character]:
    chars = []
    for i in range(good):
        chars.append(Character(
            id=f"g{i}", name=f"Good{i}", faction="Village", hidden_role="Villager",
        ))
    for i in range(evil):
        chars.append(Character(
            id=f"e{i}", name=f"Evil{i}", faction="Werewolf", hidden_role="Wolf",
        ))
    return chars


def _make_msg(speaker_id: str, content: str, round_: int = 1) -> ChatMessage:
    return ChatMessage(
        speaker_id=speaker_id,
        speaker_name=speaker_id,
        content=content,
        phase="discussion",
        round=round_,
    )


# ── Tension update logic (mirrors GameMaster.update_tension) ─────────

def update_tension(state: GameState) -> GameState:
    """Mirror of GameMaster.update_tension for unit testing."""
    alive = [c for c in state.characters if not c.is_eliminated]
    total = len(state.characters)
    alive_count = len(alive)

    elimination_ratio = 1.0 - (alive_count / max(total, 1))
    round_factor = min(state.round / 6.0, 1.0)

    state.tension_level = min(1.0, 0.2 + elimination_ratio * 0.4 + round_factor * 0.3)

    recent_kills = [a for a in state.night_actions if a.result == "killed"]
    if recent_kills:
        state.tension_level = min(1.0, state.tension_level + 0.15)

    return state


# ── Complication check logic (mirrors GameMaster.should_inject_complication) ──

def should_inject_complication(state: GameState) -> bool:
    """Mirror of GameMaster.should_inject_complication, deterministic parts only."""
    round_msgs = [m for m in state.messages if m.round == state.round]
    if len(round_msgs) < 6:
        return False

    recent = round_msgs[-4:]
    unique_speakers = len({m.speaker_id for m in recent})
    if unique_speakers <= 1:
        return True

    accusation_kw = {"suspect", "traitor", "lying", "accuse", "vote", "eliminate"}
    recent_text = " ".join(m.content.lower() for m in recent)
    has_accusations = any(kw in recent_text for kw in accusation_kw)
    if not has_accusations and len(round_msgs) > 8:
        return True

    return False


class TestTensionUpdate:
    def test_initial_tension(self):
        """Initial tension at round 1, no eliminations."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars, round=1)
        state = update_tension(state)
        # 0.2 + 0 * 0.4 + (1/6) * 0.3 = 0.2 + 0.05 = 0.25
        assert 0.2 <= state.tension_level <= 0.3

    def test_tension_rises_with_elimination(self):
        """Tension increases when characters are eliminated."""
        chars = _make_chars()
        chars[0].is_eliminated = True
        state = GameState(world=_make_world(), characters=chars, round=1)
        state = update_tension(state)
        # elimination_ratio = 1 - 4/5 = 0.2
        # 0.2 + 0.2*0.4 + (1/6)*0.3 = 0.2 + 0.08 + 0.05 = 0.33
        assert state.tension_level > 0.3

    def test_tension_rises_with_rounds(self):
        """Tension rises as round count increases."""
        chars = _make_chars()
        state1 = GameState(world=_make_world(), characters=chars, round=1)
        state1 = update_tension(state1)

        state2 = GameState(world=_make_world(), characters=_make_chars(), round=4)
        state2 = update_tension(state2)

        assert state2.tension_level > state1.tension_level

    def test_tension_spikes_after_night_kill(self):
        """Tension gets a 0.15 spike after a night kill."""
        chars = _make_chars()
        state = GameState(
            world=_make_world(), characters=chars, round=2,
            night_actions=[
                NightAction(character_id="e0", action_type="kill",
                            target_id="g0", result="killed"),
            ],
        )
        state = update_tension(state)
        # Should be base + 0.15 spike
        assert state.tension_level >= 0.4

    def test_tension_capped_at_one(self):
        """Tension never exceeds 1.0."""
        chars = _make_chars()
        # Eliminate all but one
        for c in chars[:-1]:
            c.is_eliminated = True
        state = GameState(
            world=_make_world(), characters=chars, round=10,
            night_actions=[
                NightAction(character_id="e0", action_type="kill",
                            target_id="g0", result="killed"),
            ],
        )
        state = update_tension(state)
        assert state.tension_level <= 1.0

    def test_tension_at_round_6_high(self):
        """At round 6, round_factor reaches 1.0 cap."""
        chars = _make_chars()
        state = GameState(world=_make_world(), characters=chars, round=6)
        state = update_tension(state)
        # 0.2 + 0 + 1.0*0.3 = 0.5
        assert state.tension_level >= 0.5

    def test_tension_no_characters(self):
        """Tension with zero characters doesn't crash."""
        state = GameState(world=_make_world(), characters=[], round=1)
        state = update_tension(state)
        # 0.2 + 0 + round_factor
        assert state.tension_level >= 0.2


class TestComplicationDetection:
    def test_no_complication_too_early(self):
        """No complication when fewer than 6 messages in round."""
        state = GameState(
            world=_make_world(), characters=_make_chars(), round=1,
            messages=[_make_msg(f"g{i}", f"msg {i}") for i in range(3)],
        )
        assert should_inject_complication(state) is False

    def test_complication_when_single_speaker(self):
        """Complication triggered when only one speaker in recent messages."""
        msgs = [_make_msg("g0", f"message {i}") for i in range(8)]
        state = GameState(
            world=_make_world(), characters=_make_chars(), round=1,
            messages=msgs,
        )
        assert should_inject_complication(state) is True

    def test_no_complication_with_accusations(self):
        """No complication when accusation keywords present (under 9 messages)."""
        msgs = [
            _make_msg("g0", "I think something is wrong"),
            _make_msg("g1", "I agree"),
            _make_msg("g2", "Let me think"),
            _make_msg("e0", "That's interesting"),
            _make_msg("e1", "I suspect g0 is lying"),
            _make_msg("g0", "I accuse e1 of being evil"),
            _make_msg("g1", "We should vote on this"),
        ]
        state = GameState(
            world=_make_world(), characters=_make_chars(), round=1,
            messages=msgs,
        )
        assert should_inject_complication(state) is False

    def test_complication_stale_discussion_no_accusations(self):
        """Complication when >8 messages but no accusation keywords."""
        msgs = [
            _make_msg(f"g{i % 3}", f"I think the weather is nice today {i}")
            for i in range(10)
        ]
        state = GameState(
            world=_make_world(), characters=_make_chars(), round=1,
            messages=msgs,
        )
        assert should_inject_complication(state) is True

    def test_exactly_six_messages_no_complication_when_varied(self):
        """Exactly 6 messages with varied speakers and accusations -> no complication."""
        msgs = [
            _make_msg("g0", "Hello everyone"),
            _make_msg("g1", "Hi there"),
            _make_msg("g2", "Greetings"),
            _make_msg("e0", "I suspect something"),
            _make_msg("e1", "I accuse g0"),
            _make_msg("g0", "I vote to eliminate e1"),
        ]
        state = GameState(
            world=_make_world(), characters=_make_chars(), round=1,
            messages=msgs,
        )
        assert should_inject_complication(state) is False
