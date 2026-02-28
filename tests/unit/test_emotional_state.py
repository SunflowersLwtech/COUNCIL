"""Unit tests for character emotional state, Sims traits, and MindMirror models."""

import pytest

from backend.models.game_models import (
    Character,
    EmotionalState,
    SimsTraits,
    MindMirror,
    MindMirrorPlane,
    Relationship,
    Memory,
)


class TestEmotionalState:
    def test_defaults(self):
        """EmotionalState has balanced defaults."""
        es = EmotionalState()
        assert es.happiness == 0.5
        assert es.anger == 0.0
        assert es.fear == 0.1
        assert es.trust == 0.5
        assert es.energy == 0.8
        assert es.curiosity == 0.5

    def test_custom_values(self):
        """EmotionalState accepts custom values."""
        es = EmotionalState(happiness=0.9, anger=0.7, fear=0.3)
        assert es.happiness == 0.9
        assert es.anger == 0.7

    def test_character_has_emotional_state(self):
        """Characters have default emotional state."""
        char = Character(name="Test")
        assert isinstance(char.emotional_state, EmotionalState)
        assert char.emotional_state.happiness == 0.5


class TestSimsTraits:
    def test_defaults(self):
        """SimsTraits default to 5 each (balanced)."""
        traits = SimsTraits()
        assert traits.neat == 5
        assert traits.outgoing == 5
        assert traits.active == 5
        assert traits.playful == 5
        assert traits.nice == 5

    def test_custom_traits(self):
        """SimsTraits accept custom values."""
        traits = SimsTraits(neat=8, outgoing=2, active=7, playful=3, nice=5)
        assert traits.neat == 8
        assert traits.outgoing == 2

    def test_character_has_sims_traits(self):
        """Characters have default Sims traits."""
        char = Character(name="Test")
        assert isinstance(char.sims_traits, SimsTraits)


class TestMindMirror:
    def test_defaults(self):
        """MindMirror has 4 planes with empty defaults."""
        mm = MindMirror()
        assert isinstance(mm.bio_energy, MindMirrorPlane)
        assert isinstance(mm.emotional, MindMirrorPlane)
        assert isinstance(mm.mental, MindMirrorPlane)
        assert isinstance(mm.social, MindMirrorPlane)

    def test_plane_defaults(self):
        """MindMirrorPlane has empty dicts."""
        plane = MindMirrorPlane()
        assert plane.traits == {}
        assert plane.jazz == {}

    def test_plane_with_data(self):
        """MindMirrorPlane stores traits and jazz commentary."""
        plane = MindMirrorPlane(
            traits={"dominance": 5, "warmth": 3},
            jazz={"dominance": "naturally commanding"},
        )
        assert plane.traits["dominance"] == 5
        assert "commanding" in plane.jazz["dominance"]

    def test_plane_coercion_none(self):
        """None values for plane dicts coerce to empty dict."""
        plane = MindMirrorPlane(traits=None, jazz=None)
        assert plane.traits == {}
        assert plane.jazz == {}


class TestRelationship:
    def test_defaults(self):
        """Relationship has neutral defaults."""
        rel = Relationship()
        assert rel.target_id == ""
        assert rel.closeness == 0.0
        assert rel.trust == 0.5
        assert rel.narrative == ""

    def test_with_data(self):
        """Relationship stores interpersonal data."""
        rel = Relationship(
            target_id="c2", target_name="Bob",
            closeness=0.7, trust=0.3, narrative="Suspicious of Bob",
        )
        assert rel.target_id == "c2"
        assert rel.closeness == 0.7

    def test_character_has_relationships(self):
        """Character has empty relationships by default."""
        char = Character(name="Test")
        assert char.relationships == []


class TestMemory:
    def test_defaults(self):
        """Memory has safe defaults."""
        mem = Memory()
        assert mem.event == ""
        assert mem.mood_effect == {}
        assert mem.round == 0

    def test_with_data(self):
        """Memory stores gameplay events."""
        mem = Memory(
            event="Alice accused Bob",
            mood_effect={"anger": 0.2, "trust": -0.1},
            narrative="A heated accusation",
            round=2,
        )
        assert mem.event == "Alice accused Bob"
        assert mem.mood_effect["anger"] == 0.2

    def test_character_has_memories(self):
        """Character has empty memories by default."""
        char = Character(name="Test")
        assert char.recent_memories == []


class TestCharacterPersonality:
    """Test personality-related fields on Character model."""

    def test_personality_summary_default(self):
        char = Character(name="Test")
        assert char.personality_summary == ""
        assert char.current_mood == ""
        assert char.driving_need == ""

    def test_big_five_and_mbti(self):
        char = Character(
            name="Test", big_five="OCEAN: O=high, C=high, E=low, A=med, N=low",
            mbti="INTJ",
        )
        assert "OCEAN" in char.big_five
        assert char.mbti == "INTJ"

    def test_want_and_method(self):
        """Character stores motivation layer."""
        char = Character(
            name="Test", want="Survive at all costs",
            method="Deflect suspicion onto others",
        )
        assert "Survive" in char.want
        assert "Deflect" in char.method

    def test_moral_values(self):
        char = Character(name="Test", moral_values=["justice", "loyalty"])
        assert "justice" in char.moral_values
        assert len(char.moral_values) == 2
