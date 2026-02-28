"""Shared fixtures for COUNCIL test suite."""

import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCENARIOS_DIR = PROJECT_ROOT.parent / "test" / "scenarios"


# ── Model Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def sample_world():
    """A minimal WorldModel for testing."""
    from backend.models.game_models import WorldModel

    return WorldModel(
        title="Test World",
        setting="A test village.",
        factions=[
            {"name": "Village", "alignment": "good", "description": "Good guys"},
            {"name": "Werewolf", "alignment": "evil", "description": "Bad guys"},
        ],
        roles=[
            {"name": "Villager", "faction": "Village", "ability": "None"},
            {"name": "Seer", "faction": "Village", "ability": "Detect evil"},
            {"name": "Wolf", "faction": "Werewolf", "ability": "Deception"},
        ],
        win_conditions=[
            {"faction": "Village", "condition": "Eliminate all werewolves"},
            {"faction": "Werewolf", "condition": "Outnumber the villagers"},
        ],
        phases=[
            {"name": "Discussion", "duration": "5 min"},
            {"name": "Voting", "duration": "2 min"},
        ],
        flavor_text="A dark and stormy night...",
    )


@pytest.fixture
def sample_characters():
    """A list of 5 Characters with mixed factions."""
    from backend.models.game_models import Character

    return [
        Character(
            id="char-001",
            name="Elder Marcus",
            persona="Wise village elder",
            speaking_style="formal",
            avatar_seed="abc123",
            public_role="Council Leader",
            hidden_role="Villager",
            faction="Village",
            win_condition="Eliminate all werewolves",
            hidden_knowledge=["You are a simple villager."],
            behavioral_rules=["Use logic to find wolves."],
            voice_id="George",
        ),
        Character(
            id="char-002",
            name="Swift Lila",
            persona="Quick-witted trader",
            speaking_style="casual",
            avatar_seed="def456",
            public_role="Merchant",
            hidden_role="Seer",
            faction="Village",
            win_condition="Eliminate all werewolves",
            hidden_knowledge=["You can detect evil."],
            behavioral_rules=["Hint at your knowledge without revealing your role."],
            voice_id="Sarah",
        ),
        Character(
            id="char-003",
            name="Brother Aldric",
            persona="Pious monk",
            speaking_style="reverent",
            avatar_seed="ghi789",
            public_role="Monk",
            hidden_role="Villager",
            faction="Village",
            win_condition="Eliminate all werewolves",
            hidden_knowledge=["You are a simple villager."],
            behavioral_rules=["Observe and deduce."],
            voice_id="Harry",
        ),
        Character(
            id="char-004",
            name="Captain Thorne",
            persona="Suspicious former military",
            speaking_style="curt",
            avatar_seed="jkl012",
            public_role="Guard Captain",
            hidden_role="Werewolf",
            faction="Werewolf",
            win_condition="Outnumber the villagers",
            hidden_knowledge=["You are a werewolf. char-005 is also a werewolf."],
            behavioral_rules=["Deflect suspicion.", "Cast doubt on others."],
            voice_id="James",
        ),
        Character(
            id="char-005",
            name="Mira the Weaver",
            persona="Gossip-loving artisan",
            speaking_style="warm but sly",
            avatar_seed="mno345",
            public_role="Artisan",
            hidden_role="Werewolf",
            faction="Werewolf",
            win_condition="Outnumber the villagers",
            hidden_knowledge=["You are a werewolf. char-004 is also a werewolf."],
            behavioral_rules=["Deflect suspicion.", "Appear helpful."],
            voice_id="Emily",
        ),
    ]


@pytest.fixture
def sample_game_state(sample_world, sample_characters):
    """A fully populated GameState in discussion phase."""
    from backend.models.game_models import GameState

    return GameState(
        session_id="test-session-001",
        phase="discussion",
        round=1,
        world=sample_world,
        characters=sample_characters,
    )


@pytest.fixture
def lobby_game_state(sample_world, sample_characters):
    """A GameState in lobby phase, ready to start."""
    from backend.models.game_models import GameState

    return GameState(
        session_id="test-session-lobby",
        phase="lobby",
        round=1,
        world=sample_world,
        characters=sample_characters,
    )


@pytest.fixture
def scenario_files():
    """Map of scenario IDs to file paths."""
    if not SCENARIOS_DIR.exists():
        pytest.skip("Scenario directory not found")
    files = {}
    for f in sorted(SCENARIOS_DIR.glob("*.md")):
        files[f.stem] = f
    return files


@pytest.fixture
def mock_mistral_client():
    """A fully mocked Mistral client for unit tests."""
    mock_client = MagicMock()

    # Mock chat.complete_async
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"title": "Test"}'
    mock_client.chat.complete_async = AsyncMock(return_value=mock_response)

    # Mock files
    mock_uploaded = MagicMock()
    mock_uploaded.id = "file-123"
    mock_client.files.upload_async = AsyncMock(return_value=mock_uploaded)

    mock_signed = MagicMock()
    mock_signed.url = "https://example.com/signed"
    mock_client.files.get_signed_url_async = AsyncMock(return_value=mock_signed)

    # Mock OCR
    mock_ocr_result = MagicMock()
    mock_page = MagicMock()
    mock_page.markdown = "# Test Document"
    mock_ocr_result.pages = [mock_page]
    mock_client.ocr.process_async = AsyncMock(return_value=mock_ocr_result)

    return mock_client
