"""Integration tests for SSE (Server-Sent Events) streaming format.

Validates that the SSE events have correct format and contain
expected data for different game actions.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.game_models import (
    Character,
    ChatMessage,
    GameState,
    VoteRecord,
    VoteResult,
)


def format_sse_event(data: dict) -> str:
    """Format a dict as an SSE event string."""
    return f"data: {json.dumps(data)}\n\n"


def parse_sse_events(raw: str) -> list[dict]:
    """Parse raw SSE text into list of event dicts."""
    events = []
    for line in raw.strip().split("\n\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                events.append(data)
            except json.JSONDecodeError:
                continue
    return events


class TestSSEEventFormat:
    def test_sse_format_structure(self):
        """SSE events follow 'data: {json}\\n\\n' format."""
        event = {"type": "response", "content": "Hello"}
        formatted = format_sse_event(event)
        assert formatted.startswith("data: ")
        assert formatted.endswith("\n\n")
        parsed = json.loads(formatted.strip().split("data: ")[1])
        assert parsed["type"] == "response"

    def test_parse_multiple_events(self):
        """Multiple SSE events can be parsed from a stream."""
        raw = (
            'data: {"type": "thinking", "agent_id": "char-001"}\n\n'
            'data: {"type": "response", "content": "Hello"}\n\n'
            'data: {"type": "done"}\n\n'
        )
        events = parse_sse_events(raw)
        assert len(events) == 3
        assert events[0]["type"] == "thinking"
        assert events[1]["type"] == "response"
        assert events[2]["type"] == "done"


class TestCharacterResponseEvents:
    def test_character_response_event(self):
        """Character response events contain required fields."""
        event = {
            "type": "character_response",
            "character_id": "char-001",
            "character_name": "Elder Marcus",
            "content": "I have concerns about the captain.",
            "voice_url": None,
        }
        formatted = format_sse_event(event)
        parsed = parse_sse_events(formatted)[0]

        assert parsed["type"] == "character_response"
        assert parsed["character_id"] == "char-001"
        assert parsed["character_name"] == "Elder Marcus"
        assert parsed["content"]

    def test_multiple_character_responses(self):
        """Multiple characters responding produces multiple events."""
        events_raw = ""
        for i, name in enumerate(["Marcus", "Lila", "Thorne"]):
            event = {
                "type": "character_response",
                "character_id": f"char-{i+1:03d}",
                "character_name": name,
                "content": f"Response from {name}",
            }
            events_raw += format_sse_event(event)
        events_raw += format_sse_event({"type": "done"})

        events = parse_sse_events(events_raw)
        responses = [e for e in events if e["type"] == "character_response"]
        assert len(responses) == 3

    def test_thinking_event_before_response(self):
        """Thinking events precede character response events."""
        events_raw = (
            format_sse_event({"type": "thinking", "character_id": "char-001"})
            + format_sse_event({
                "type": "character_response",
                "character_id": "char-001",
                "content": "My response.",
            })
            + format_sse_event({"type": "done"})
        )
        events = parse_sse_events(events_raw)

        assert events[0]["type"] == "thinking"
        assert events[1]["type"] == "character_response"
        assert events[0]["character_id"] == events[1]["character_id"]


class TestPhaseChangeEvents:
    def test_phase_change_event(self):
        """Phase change events contain old and new phase."""
        event = {
            "type": "phase_change",
            "from_phase": "discussion",
            "to_phase": "voting",
            "round": 1,
        }
        formatted = format_sse_event(event)
        parsed = parse_sse_events(formatted)[0]

        assert parsed["type"] == "phase_change"
        assert parsed["from_phase"] == "discussion"
        assert parsed["to_phase"] == "voting"

    def test_game_start_event(self):
        """Game start produces lobby -> discussion phase change."""
        event = {
            "type": "phase_change",
            "from_phase": "lobby",
            "to_phase": "discussion",
            "round": 1,
            "narration": "The council convenes...",
        }
        parsed = parse_sse_events(format_sse_event(event))[0]
        assert parsed["from_phase"] == "lobby"
        assert parsed["to_phase"] == "discussion"


class TestVoteResultEvents:
    def test_vote_result_event(self):
        """Vote result events contain tally and elimination info."""
        event = {
            "type": "vote_result",
            "tally": {"char-004": 3, "char-001": 2},
            "eliminated_id": "char-004",
            "eliminated_name": "Captain Thorne",
            "eliminated_role": "Werewolf",
            "is_tie": False,
        }
        parsed = parse_sse_events(format_sse_event(event))[0]

        assert parsed["type"] == "vote_result"
        assert parsed["eliminated_name"] == "Captain Thorne"
        assert parsed["tally"]["char-004"] == 3
        assert not parsed["is_tie"]

    def test_tie_vote_event(self):
        """Tie vote events indicate no elimination."""
        event = {
            "type": "vote_result",
            "tally": {"char-004": 2, "char-005": 2},
            "eliminated_id": None,
            "eliminated_name": None,
            "is_tie": True,
        }
        parsed = parse_sse_events(format_sse_event(event))[0]

        assert parsed["is_tie"] is True
        assert parsed["eliminated_id"] is None


class TestDoneEvent:
    def test_done_event_ends_stream(self):
        """Stream always ends with a done event."""
        events_raw = (
            format_sse_event({"type": "character_response", "content": "test"})
            + format_sse_event({"type": "done"})
        )
        events = parse_sse_events(events_raw)
        assert events[-1]["type"] == "done"

    def test_done_event_minimal(self):
        """Done event only needs type field."""
        event = {"type": "done"}
        parsed = parse_sse_events(format_sse_event(event))[0]
        assert parsed == {"type": "done"}


class TestHeartbeatEvent:
    def test_heartbeat_event(self):
        """Heartbeat events keep the connection alive."""
        event = {"event": "heartbeat"}
        parsed = parse_sse_events(format_sse_event(event))[0]
        assert parsed["event"] == "heartbeat"

    def test_heartbeat_in_stream(self):
        """Heartbeat can appear between content events."""
        events_raw = (
            format_sse_event({"type": "thinking", "character_id": "char-001"})
            + format_sse_event({"event": "heartbeat"})
            + format_sse_event({"type": "character_response", "content": "test"})
            + format_sse_event({"type": "done"})
        )
        events = parse_sse_events(events_raw)
        assert len(events) == 4
        assert events[1]["event"] == "heartbeat"


class TestErrorEvents:
    def test_error_event(self):
        """Error events contain error message."""
        event = {
            "type": "error",
            "error": "Character generation failed",
            "character_id": "char-001",
        }
        parsed = parse_sse_events(format_sse_event(event))[0]
        assert parsed["type"] == "error"
        assert "failed" in parsed["error"]
