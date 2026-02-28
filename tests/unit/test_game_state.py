"""Unit tests for GameState, Character, and WorldModel models."""

import pytest
from backend.models.game_models import (
    GameState,
    Character,
    CharacterPublicInfo,
    WorldModel,
    ChatMessage,
    VoteRecord,
    VoteResult,
    NightAction,
    GameCreateResponse,
    GameChatRequest,
    GameVoteRequest,
)


class TestGameState:
    def test_default_state(self):
        """State starts in lobby phase with round 1."""
        state = GameState()
        assert state.phase == "lobby"
        assert state.round == 1
        assert state.characters == []
        assert state.winner is None
        assert state.eliminated == []
        assert state.messages == []
        assert state.votes == []
        assert state.vote_results == []

    def test_session_id_generated(self):
        """Each state gets a unique session ID."""
        s1 = GameState()
        s2 = GameState()
        assert s1.session_id != s2.session_id
        assert len(s1.session_id) > 0

    def test_session_id_is_uuid_format(self):
        """Session ID should be a valid UUID string."""
        state = GameState()
        import uuid
        # Should not raise
        uuid.UUID(state.session_id)

    def test_state_with_characters(self, sample_characters):
        """State can be created with a list of characters."""
        state = GameState(characters=sample_characters)
        assert len(state.characters) == 5
        assert state.characters[0].name == "Elder Marcus"

    def test_state_with_world(self, sample_world):
        """State can be created with a world model."""
        state = GameState(world=sample_world)
        assert state.world.title == "Test World"
        assert len(state.world.factions) == 2

    def test_phase_values(self):
        """Only valid phase values are allowed, including night."""
        for phase in ["lobby", "discussion", "voting", "reveal", "night", "ended"]:
            state = GameState(phase=phase)
            assert state.phase == phase

    def test_invalid_phase_rejected(self):
        """Invalid phase string raises validation error."""
        with pytest.raises(Exception):
            GameState(phase="invalid_phase")

    def test_winner_initially_none(self):
        """Winner is None until game ends."""
        state = GameState()
        assert state.winner is None

    def test_winner_can_be_set(self):
        """Winner can be set to a faction name."""
        state = GameState(winner="Village")
        assert state.winner == "Village"

    def test_eliminated_list(self):
        """Eliminated tracks character IDs."""
        state = GameState(eliminated=["char-001", "char-002"])
        assert len(state.eliminated) == 2
        assert "char-001" in state.eliminated

    def test_messages_list(self):
        """Messages can be added to state."""
        msg = ChatMessage(
            speaker_id="char-001",
            speaker_name="Marcus",
            content="I suspect the wolf!",
            phase="discussion",
            round=1,
        )
        state = GameState(messages=[msg])
        assert len(state.messages) == 1
        assert state.messages[0].content == "I suspect the wolf!"

    def test_vote_results(self):
        """VoteResults track elimination outcomes."""
        vr = VoteResult(
            votes=[
                VoteRecord(voter_id="c1", voter_name="A", target_id="c2", target_name="B"),
                VoteRecord(voter_id="c3", voter_name="C", target_id="c2", target_name="B"),
            ],
            tally={"c2": 2},
            eliminated_id="c2",
            eliminated_name="B",
            is_tie=False,
        )
        state = GameState(vote_results=[vr])
        assert state.vote_results[0].eliminated_name == "B"
        assert state.vote_results[0].tally["c2"] == 2


class TestCharacter:
    def test_character_defaults(self):
        """Characters have all required defaults."""
        char = Character()
        assert char.name == ""
        assert char.is_eliminated is False
        assert char.faction == ""
        assert char.hidden_role == ""
        assert char.voice_id == "Sarah"
        assert char.hidden_knowledge == []
        assert char.behavioral_rules == []

    def test_character_id_generated(self):
        """Each character gets a unique short ID."""
        c1 = Character()
        c2 = Character()
        assert c1.id != c2.id
        assert len(c1.id) == 8

    def test_character_with_all_fields(self):
        """Character can be created with all fields populated."""
        char = Character(
            name="Test Hero",
            persona="A brave warrior",
            speaking_style="bold",
            avatar_seed="seed123",
            public_role="Knight",
            hidden_role="Spy",
            faction="Evil",
            win_condition="Survive",
            hidden_knowledge=["Secret info"],
            behavioral_rules=["Stay hidden"],
            voice_id="George",
        )
        assert char.name == "Test Hero"
        assert char.faction == "Evil"
        assert char.hidden_knowledge == ["Secret info"]

    def test_character_elimination(self):
        """Character can be marked as eliminated."""
        char = Character(is_eliminated=True)
        assert char.is_eliminated is True

    def test_character_str_coercion_none(self):
        """None values for string fields coerce to empty string."""
        char = Character(name=None, faction=None)
        assert char.name == ""
        assert char.faction == ""

    def test_character_str_coercion_dict(self):
        """Dict values for string fields coerce to JSON string."""
        char = Character(name={"first": "Test"})
        assert '"first"' in char.name

    def test_character_str_coercion_list(self):
        """List values for string fields coerce to semicolon-joined string."""
        char = Character(name=["A", "B"])
        assert "A" in char.name
        assert "B" in char.name

    def test_hidden_knowledge_coercion_none(self):
        """None hidden_knowledge coerces to empty list."""
        char = Character(hidden_knowledge=None)
        assert char.hidden_knowledge == []

    def test_hidden_knowledge_coercion_string(self):
        """String hidden_knowledge coerces to single-element list."""
        char = Character(hidden_knowledge="secret")
        assert char.hidden_knowledge == ["secret"]

    def test_hidden_knowledge_coercion_dict(self):
        """Dict hidden_knowledge coerces to key-value list."""
        char = Character(hidden_knowledge={"role": "spy"})
        assert "role: spy" in char.hidden_knowledge[0]


class TestCharacterPublicInfo:
    def test_public_info_defaults(self):
        """PublicInfo has safe defaults."""
        info = CharacterPublicInfo()
        assert info.id == ""
        assert info.name == ""
        assert info.is_eliminated is False

    def test_public_info_lacks_hidden_fields(self):
        """PublicInfo model does not have hidden fields."""
        info = CharacterPublicInfo()
        assert not hasattr(info, "hidden_role")
        assert not hasattr(info, "hidden_knowledge")
        assert not hasattr(info, "faction")
        assert not hasattr(info, "win_condition")
        assert not hasattr(info, "behavioral_rules")

    def test_public_info_from_character(self, sample_characters):
        """PublicInfo can be constructed from Character's public fields."""
        char = sample_characters[0]
        info = CharacterPublicInfo(
            id=char.id,
            name=char.name,
            persona=char.persona,
            speaking_style=char.speaking_style,
            avatar_seed=char.avatar_seed,
            public_role=char.public_role,
            voice_id=char.voice_id,
            is_eliminated=char.is_eliminated,
        )
        assert info.name == "Elder Marcus"
        assert info.public_role == "Council Leader"


class TestWorldModel:
    def test_world_model_defaults(self):
        """WorldModel has safe defaults."""
        world = WorldModel()
        assert world.title == ""
        assert world.factions == []
        assert world.roles == []
        assert world.win_conditions == []
        assert world.phases == []
        assert world.flavor_text == ""

    def test_world_model_with_data(self, sample_world):
        """WorldModel stores all fields correctly."""
        assert sample_world.title == "Test World"
        assert len(sample_world.factions) == 2
        assert len(sample_world.roles) == 3
        assert len(sample_world.win_conditions) == 2
        assert sample_world.flavor_text == "A dark and stormy night..."

    def test_world_str_coercion_none(self):
        """None values for string fields coerce to empty string."""
        world = WorldModel(title=None, setting=None)
        assert world.title == ""
        assert world.setting == ""

    def test_world_str_coercion_dict(self):
        """Dict values for string fields coerce to JSON."""
        world = WorldModel(title={"name": "test"})
        assert '"name"' in world.title

    def test_world_str_coercion_list(self):
        """List values for string fields coerce to semicolon-joined."""
        world = WorldModel(title=["A", "B"])
        assert "A" in world.title

    def test_factions_coercion_none(self):
        """None factions coerce to empty list."""
        world = WorldModel(factions=None)
        assert world.factions == []

    def test_factions_coercion_string(self):
        """String factions coerce to list with name dict."""
        world = WorldModel(factions="Village")
        assert world.factions == [{"name": "Village"}]

    def test_factions_coercion_dict(self):
        """Dict factions coerce to list of dicts."""
        world = WorldModel(factions={"Village": "Good guys", "Wolves": "Bad guys"})
        assert len(world.factions) == 2
        names = {f["name"] for f in world.factions}
        assert "Village" in names
        assert "Wolves" in names

    def test_factions_coercion_list_of_strings(self):
        """List-of-string factions coerce to list of name dicts."""
        world = WorldModel(factions=["Village", "Wolves"])
        assert world.factions == [{"name": "Village"}, {"name": "Wolves"}]

    def test_factions_json_string(self):
        """JSON string factions are parsed correctly."""
        import json
        world = WorldModel(factions=json.dumps([{"name": "A"}, {"name": "B"}]))
        assert len(world.factions) == 2


class TestChatMessage:
    def test_chat_message_defaults(self):
        """ChatMessage has safe defaults."""
        msg = ChatMessage()
        assert msg.speaker_id == ""
        assert msg.content == ""
        assert msg.is_public is True
        assert msg.round == 0

    def test_chat_message_str_coercion(self):
        """None string fields coerce to empty string."""
        msg = ChatMessage(speaker_id=None, content=None)
        assert msg.speaker_id == ""
        assert msg.content == ""


class TestVoteRecord:
    def test_vote_record_defaults(self):
        """VoteRecord has empty string defaults."""
        vr = VoteRecord()
        assert vr.voter_id == ""
        assert vr.target_id == ""

    def test_vote_record_str_coercion(self):
        """None values coerce to empty string."""
        vr = VoteRecord(voter_id=None, target_name=None)
        assert vr.voter_id == ""
        assert vr.target_name == ""


class TestVoteResult:
    def test_vote_result_defaults(self):
        """VoteResult has safe defaults."""
        vr = VoteResult()
        assert vr.votes == []
        assert vr.tally == {}
        assert vr.eliminated_id is None
        assert vr.is_tie is False

    def test_vote_result_with_data(self):
        """VoteResult stores elimination data."""
        vr = VoteResult(
            eliminated_id="c1",
            eliminated_name="Marcus",
            tally={"c1": 3, "c2": 1},
            is_tie=False,
        )
        assert vr.eliminated_name == "Marcus"
        assert vr.tally["c1"] == 3


class TestRequestModels:
    def test_game_create_response(self):
        """GameCreateResponse has expected defaults."""
        resp = GameCreateResponse()
        assert resp.session_id == ""
        assert resp.phase == "lobby"
        assert resp.characters == []

    def test_game_chat_request(self):
        """GameChatRequest stores message."""
        req = GameChatRequest(message="Hello council")
        assert req.message == "Hello council"
        assert req.target_character_id is None

    def test_game_vote_request(self):
        """GameVoteRequest stores target."""
        req = GameVoteRequest(target_character_id="char-001")
        assert req.target_character_id == "char-001"


class TestNightAction:
    def test_night_action_defaults(self):
        """NightAction has safe empty defaults."""
        na = NightAction()
        assert na.character_id == ""
        assert na.action_type == ""
        assert na.target_id is None
        assert na.result == ""

    def test_night_action_with_data(self):
        """NightAction stores kill action data."""
        na = NightAction(
            character_id="char-004",
            action_type="kill",
            target_id="char-001",
            result="Elder Marcus was attacked.",
        )
        assert na.character_id == "char-004"
        assert na.action_type == "kill"
        assert na.target_id == "char-001"
        assert na.result == "Elder Marcus was attacked."

    def test_night_action_investigate(self):
        """NightAction stores investigate action."""
        na = NightAction(
            character_id="char-002",
            action_type="investigate",
            target_id="char-004",
            result="Captain Thorne is evil.",
        )
        assert na.action_type == "investigate"
        assert na.target_id == "char-004"

    def test_night_action_protect(self):
        """NightAction stores protect action."""
        na = NightAction(
            character_id="char-003",
            action_type="protect",
            target_id="char-001",
            result="Elder Marcus was protected.",
        )
        assert na.action_type == "protect"
        assert na.target_id == "char-001"

    def test_night_action_str_coercion_none(self):
        """None string fields coerce to empty string."""
        na = NightAction(character_id=None, action_type=None, result=None)
        assert na.character_id == ""
        assert na.action_type == ""
        assert na.result == ""

    def test_night_action_target_id_optional(self):
        """target_id can be None for actions without a target."""
        na = NightAction(
            character_id="char-002",
            action_type="investigate",
            target_id=None,
        )
        assert na.target_id is None


class TestGameStateNightActions:
    def test_night_actions_default_empty(self):
        """GameState.night_actions defaults to empty list."""
        state = GameState()
        assert state.night_actions == []

    def test_night_actions_with_data(self):
        """GameState can hold night actions."""
        actions = [
            NightAction(character_id="c1", action_type="kill", target_id="c2"),
            NightAction(character_id="c3", action_type="protect", target_id="c2"),
        ]
        state = GameState(night_actions=actions)
        assert len(state.night_actions) == 2
        assert state.night_actions[0].action_type == "kill"
        assert state.night_actions[1].action_type == "protect"

    def test_night_phase_with_night_actions(self):
        """GameState in night phase can hold night actions."""
        state = GameState(
            phase="night",
            night_actions=[
                NightAction(character_id="c1", action_type="kill", target_id="c2"),
            ],
        )
        assert state.phase == "night"
        assert len(state.night_actions) == 1
