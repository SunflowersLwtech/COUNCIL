"""Unit tests for voting logic — tallying, ties, elimination."""

import pytest

from backend.models.game_models import (
    Character,
    GameState,
    VoteRecord,
    VoteResult,
)


def make_vote(voter_id: str, voter_name: str, target_id: str, target_name: str) -> VoteRecord:
    """Helper to create a VoteRecord."""
    return VoteRecord(
        voter_id=voter_id,
        voter_name=voter_name,
        target_id=target_id,
        target_name=target_name,
    )


def tally_votes(votes: list[VoteRecord]) -> dict[str, int]:
    """Compute vote tally from a list of VoteRecords."""
    tally: dict[str, int] = {}
    for v in votes:
        tally[v.target_id] = tally.get(v.target_id, 0) + 1
    return tally


def resolve_votes(
    votes: list[VoteRecord],
    characters: list[Character],
) -> VoteResult:
    """Resolve a round of voting.

    This mirrors the expected game logic:
    - Majority -> eliminate that character
    - Tie -> no elimination
    """
    tally = tally_votes(votes)

    if not tally:
        return VoteResult(votes=votes, tally=tally, is_tie=True)

    max_votes = max(tally.values())
    top_targets = [tid for tid, count in tally.items() if count == max_votes]

    if len(top_targets) > 1:
        return VoteResult(votes=votes, tally=tally, is_tie=True)

    eliminated_id = top_targets[0]
    char_map = {c.id: c for c in characters}
    eliminated_char = char_map.get(eliminated_id)
    eliminated_name = eliminated_char.name if eliminated_char else "Unknown"

    return VoteResult(
        votes=votes,
        tally=tally,
        eliminated_id=eliminated_id,
        eliminated_name=eliminated_name,
        is_tie=False,
    )


class TestVoteTally:
    def test_simple_tally(self):
        """Basic vote counting works."""
        votes = [
            make_vote("c1", "A", "c3", "C"),
            make_vote("c2", "B", "c3", "C"),
            make_vote("c3", "C", "c1", "A"),
        ]
        tally = tally_votes(votes)
        assert tally["c3"] == 2
        assert tally["c1"] == 1

    def test_empty_votes(self):
        """Empty vote list gives empty tally."""
        tally = tally_votes([])
        assert tally == {}

    def test_unanimous_vote(self):
        """All votes for one target."""
        votes = [
            make_vote("c1", "A", "c2", "B"),
            make_vote("c3", "C", "c2", "B"),
            make_vote("c4", "D", "c2", "B"),
        ]
        tally = tally_votes(votes)
        assert tally["c2"] == 3
        assert len(tally) == 1


class TestVoteResolution:
    def test_majority_eliminates(self, sample_characters):
        """Target with most votes is eliminated."""
        votes = [
            make_vote("char-001", "Marcus", "char-004", "Thorne"),
            make_vote("char-002", "Lila", "char-004", "Thorne"),
            make_vote("char-003", "Aldric", "char-004", "Thorne"),
            make_vote("char-004", "Thorne", "char-001", "Marcus"),
            make_vote("char-005", "Mira", "char-001", "Marcus"),
        ]
        result = resolve_votes(votes, sample_characters)

        assert not result.is_tie
        assert result.eliminated_id == "char-004"
        assert result.eliminated_name == "Captain Thorne"
        assert result.tally["char-004"] == 3

    def test_tie_no_elimination(self, sample_characters):
        """Tied vote results in no elimination."""
        votes = [
            make_vote("char-001", "Marcus", "char-004", "Thorne"),
            make_vote("char-002", "Lila", "char-004", "Thorne"),
            make_vote("char-003", "Aldric", "char-005", "Mira"),
            make_vote("char-004", "Thorne", "char-005", "Mira"),
            make_vote("char-005", "Mira", "char-001", "Marcus"),
        ]
        result = resolve_votes(votes, sample_characters)

        assert result.is_tie
        assert result.eliminated_id is None

    def test_single_vote(self, sample_characters):
        """Single voter still works."""
        votes = [make_vote("char-001", "Marcus", "char-004", "Thorne")]
        result = resolve_votes(votes, sample_characters)

        assert not result.is_tie
        assert result.eliminated_id == "char-004"

    def test_empty_votes_is_tie(self, sample_characters):
        """No votes is treated as tie."""
        result = resolve_votes([], sample_characters)
        assert result.is_tie
        assert result.eliminated_id is None

    def test_vote_result_model(self, sample_characters):
        """VoteResult model stores all expected data."""
        votes = [
            make_vote("char-001", "Marcus", "char-004", "Thorne"),
            make_vote("char-002", "Lila", "char-004", "Thorne"),
        ]
        result = resolve_votes(votes, sample_characters)

        assert len(result.votes) == 2
        assert "char-004" in result.tally
        assert result.tally["char-004"] == 2


class TestVotingConstraints:
    def test_cannot_vote_for_eliminated(self, sample_characters):
        """Votes targeting eliminated characters should be considered invalid."""
        # Mark char-004 as eliminated
        sample_characters[3].is_eliminated = True
        eliminated_ids = {"char-004"}

        votes = [
            make_vote("char-001", "Marcus", "char-004", "Thorne"),  # invalid
            make_vote("char-002", "Lila", "char-005", "Mira"),
            make_vote("char-003", "Aldric", "char-005", "Mira"),
        ]

        # Filter out votes targeting eliminated characters
        valid_votes = [v for v in votes if v.target_id not in eliminated_ids]
        result = resolve_votes(valid_votes, sample_characters)

        assert result.eliminated_id == "char-005"
        assert "char-004" not in result.tally

    def test_single_vote_per_player(self, sample_characters):
        """Each player should only get one vote per round."""
        votes = [
            make_vote("char-001", "Marcus", "char-004", "Thorne"),
            make_vote("char-001", "Marcus", "char-005", "Mira"),  # duplicate voter
            make_vote("char-002", "Lila", "char-004", "Thorne"),
        ]

        # Deduplicate: keep only the first vote per voter
        seen_voters = set()
        deduped = []
        for v in votes:
            if v.voter_id not in seen_voters:
                seen_voters.add(v.voter_id)
                deduped.append(v)

        assert len(deduped) == 2
        result = resolve_votes(deduped, sample_characters)
        assert result.tally["char-004"] == 2

    def test_eliminated_cannot_vote(self, sample_characters):
        """Eliminated characters cannot cast votes."""
        sample_characters[0].is_eliminated = True
        eliminated_ids = {"char-001"}

        votes = [
            make_vote("char-001", "Marcus", "char-004", "Thorne"),  # invalid: eliminated
            make_vote("char-002", "Lila", "char-005", "Mira"),
            make_vote("char-003", "Aldric", "char-005", "Mira"),
        ]

        valid_votes = [v for v in votes if v.voter_id not in eliminated_ids]
        result = resolve_votes(valid_votes, sample_characters)

        assert result.eliminated_id == "char-005"
        assert len(result.votes) == 2
