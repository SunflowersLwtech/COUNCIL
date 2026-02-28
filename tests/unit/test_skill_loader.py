"""Unit tests for the SkillLoader — directory-based skill discovery, resolution, and injection."""

import pytest
from pathlib import Path

from backend.game.skill_loader import SkillLoader, SkillConfig, VALID_TARGETS


class TestSkillDiscovery:
    """Test that SkillLoader correctly discovers and parses directory-based skill definitions."""

    def test_loads_skills_from_default_dir(self):
        """SkillLoader finds skills in the default skills directory."""
        loader = SkillLoader()
        skills = loader.list_skills()
        assert len(skills) >= 1, "Should discover at least one skill"

    def test_all_skills_have_required_fields(self):
        """Every loaded skill has id, name, and description."""
        loader = SkillLoader()
        for skill_dict in loader.list_skills():
            assert "id" in skill_dict
            assert "name" in skill_dict
            assert skill_dict["id"], "Skill ID must not be empty"

    def test_all_skill_ids_returns_list(self):
        """all_skill_ids returns a list of strings."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        assert isinstance(ids, list)
        for sid in ids:
            assert isinstance(sid, str)

    def test_get_skill_returns_config(self):
        """get_skill returns a SkillConfig for a known skill."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        if not ids:
            pytest.skip("No skills available")
        config = loader.get_skill(ids[0])
        assert config is not None
        assert isinstance(config, SkillConfig)
        assert config.id == ids[0]

    def test_get_unknown_skill_returns_none(self):
        """get_skill returns None for an unknown skill ID."""
        loader = SkillLoader()
        assert loader.get_skill("nonexistent_skill_xyz") is None

    def test_skills_have_valid_targets(self):
        """All skill targets are from the valid target set."""
        loader = SkillLoader()
        for skill_dict in loader.list_skills():
            for target in skill_dict.get("targets", []):
                assert target in VALID_TARGETS, f"Invalid target '{target}' in skill '{skill_dict['id']}'"

    def test_skills_sorted_by_priority(self):
        """list_skills returns skills sorted by priority."""
        loader = SkillLoader()
        skills = loader.list_skills()
        priorities = [s["priority"] for s in skills]
        assert priorities == sorted(priorities)

    def test_empty_directory(self, tmp_path):
        """SkillLoader with empty directory loads no skills."""
        loader = SkillLoader(skills_dir=tmp_path)
        assert loader.list_skills() == []

    def test_nonexistent_directory(self, tmp_path):
        """SkillLoader with nonexistent directory logs warning, loads no skills."""
        fake_dir = tmp_path / "nonexistent"
        loader = SkillLoader(skills_dir=fake_dir)
        assert loader.list_skills() == []

    def test_skill_has_available_injections(self):
        """Loaded skills have available_injections populated from injections/ dir."""
        loader = SkillLoader()
        config = loader.get_skill("strategic_reasoning")
        if not config:
            pytest.skip("strategic_reasoning not available")
        assert "character_agent" in config.available_injections
        assert "universal" in config.available_injections["character_agent"]

    def test_deception_mastery_has_faction_variants(self):
        """deception_mastery has both evil and good variants for character_agent."""
        loader = SkillLoader()
        config = loader.get_skill("deception_mastery")
        if not config:
            pytest.skip("deception_mastery not available")
        ca_variants = config.available_injections.get("character_agent", [])
        assert "evil" in ca_variants
        assert "good" in ca_variants
        # Should NOT have universal variant for character_agent
        assert "universal" not in ca_variants


class TestSkillResolution:
    """Test dependency resolution and conflict detection."""

    def test_resolve_single_skill(self):
        """Resolving a single skill with no dependencies works."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        if not ids:
            pytest.skip("No skills available")
        # Find a skill without dependencies
        for sid in ids:
            config = loader.get_skill(sid)
            if not config.dependencies:
                resolved = loader.resolve_skills([sid])
                assert any(s.id == sid for s in resolved)
                return
        pytest.skip("All skills have dependencies")

    def test_resolve_all_skills(self):
        """Resolving all available skills at once works (no conflicts in default set)."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        if not ids:
            pytest.skip("No skills available")
        resolved = loader.resolve_skills(ids)
        assert len(resolved) >= len(ids)  # May include pulled-in dependencies

    def test_dependency_resolution(self):
        """Skills with dependencies get their deps resolved first."""
        loader = SkillLoader()
        # Find a skill with dependencies
        for sid in loader.all_skill_ids():
            config = loader.get_skill(sid)
            if config.dependencies:
                resolved = loader.resolve_skills([sid])
                resolved_ids = [s.id for s in resolved]
                # Dependencies should be in the resolved list
                for dep in config.dependencies:
                    assert dep in resolved_ids, f"Dependency '{dep}' missing from resolved list"
                return
        pytest.skip("No skills with dependencies found")

    def test_unknown_skill_raises(self):
        """Resolving an unknown skill ID raises ValueError."""
        loader = SkillLoader()
        with pytest.raises(ValueError, match="Unknown skill"):
            loader.resolve_skills(["totally_fake_skill_id"])

    def test_resolved_sorted_by_priority(self):
        """Resolved skills are sorted by priority."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        if not ids:
            pytest.skip("No skills available")
        resolved = loader.resolve_skills(ids)
        priorities = [s.priority for s in resolved]
        assert priorities == sorted(priorities)


class TestSkillInjection:
    """Test prompt injection and behavioral rule collection."""

    def test_build_injection_for_known_target(self):
        """build_injection produces a string for a valid target."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        if not ids:
            pytest.skip("No skills available")
        resolved = loader.resolve_skills(ids)
        injection = loader.build_injection("character_agent", resolved)
        assert isinstance(injection, str)

    def test_build_injection_for_unknown_target_empty(self):
        """build_injection for a target with no injections returns empty string."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        if not ids:
            pytest.skip("No skills available")
        resolved = loader.resolve_skills(ids)
        injection = loader.build_injection("nonexistent_target", resolved)
        assert injection == ""

    def test_collect_behavioral_rules(self):
        """collect_behavioral_rules gathers rules from all active skills."""
        loader = SkillLoader()
        ids = loader.all_skill_ids()
        if not ids:
            pytest.skip("No skills available")
        resolved = loader.resolve_skills(ids)
        rules = loader.collect_behavioral_rules(resolved)
        assert isinstance(rules, list)
        for rule in rules:
            assert isinstance(rule, str)

    def test_build_injection_empty_skills(self):
        """build_injection with no skills returns empty string."""
        loader = SkillLoader()
        injection = loader.build_injection("character_agent", [])
        assert injection == ""


class TestFactionSpecificInjection:
    """Test faction-aware injection building."""

    def test_faction_specific_injection_evil(self):
        """Evil faction agents get evil-specific injection content, not good content."""
        loader = SkillLoader()
        resolved = loader.resolve_skills(["deception_mastery"])
        injection = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Shadow Collective",
            evil_factions={"Shadow Collective"},
        )
        assert isinstance(injection, str)
        assert len(injection) > 0
        # Evil content should be present
        assert "DEFLECTION" in injection
        assert "ALIBI BUILDING" in injection
        # Good content should NOT be present
        assert "CONSISTENCY CHECK" not in injection
        assert "VOTE PATTERN ANALYSIS" not in injection

    def test_faction_specific_injection_good(self):
        """Good faction agents get good-specific injection content, not evil content."""
        loader = SkillLoader()
        resolved = loader.resolve_skills(["deception_mastery"])
        injection = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Council of Light",
            evil_factions={"Shadow Collective"},
        )
        assert isinstance(injection, str)
        assert len(injection) > 0
        # Good content should be present
        assert "CONSISTENCY CHECK" in injection
        assert "VOTE PATTERN ANALYSIS" in injection
        # Evil content should NOT be present
        assert "DEFLECTION" not in injection
        assert "ALIBI BUILDING" not in injection

    def test_build_injection_for_agent_universal_skills(self):
        """Universal skills (no faction variants) are included for all factions."""
        loader = SkillLoader()
        resolved = loader.resolve_skills(["strategic_reasoning"])
        evil_factions = {"Shadow Collective"}

        evil_injection = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Shadow Collective", evil_factions=evil_factions,
        )
        good_injection = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Council of Light", evil_factions=evil_factions,
        )
        # Both should get the same universal content
        assert "STRATEGIC REASONING PROTOCOL" in evil_injection
        assert "STRATEGIC REASONING PROTOCOL" in good_injection
        assert evil_injection == good_injection

    def test_build_injection_for_agent_mixed_skills(self):
        """End-to-end test: multiple skills, faction filtering applied correctly."""
        loader = SkillLoader()
        resolved = loader.resolve_skills(loader.all_skill_ids())
        evil_factions = {"Shadow Collective"}

        evil_injection = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Shadow Collective", evil_factions=evil_factions,
        )
        good_injection = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Council of Light", evil_factions=evil_factions,
        )

        # Both should have universal content
        assert "STRATEGIC REASONING PROTOCOL" in evil_injection
        assert "STRATEGIC REASONING PROTOCOL" in good_injection

        # Evil should have evil deception, not good detection
        assert "DEFLECTION" in evil_injection
        assert "CONSISTENCY CHECK" not in evil_injection

        # Good should have good detection, not evil deception
        assert "CONSISTENCY CHECK" in good_injection
        assert "DEFLECTION" not in good_injection

    def test_vote_prompt_faction_filtering(self):
        """vote_prompt also gets faction-filtered for deception_mastery."""
        loader = SkillLoader()
        resolved = loader.resolve_skills(["deception_mastery"])

        evil_vote = loader.build_injection_for_agent(
            "vote_prompt", resolved,
            faction="Shadow Collective",
            evil_factions={"Shadow Collective"},
        )
        good_vote = loader.build_injection_for_agent(
            "vote_prompt", resolved,
            faction="Council of Light",
            evil_factions={"Shadow Collective"},
        )

        assert "majority protects your cover" in evil_vote
        assert "voting pattern least aligns" in good_vote

    def test_narration_build_injection_no_faction(self):
        """build_injection (non-faction) works for narration target."""
        loader = SkillLoader()
        resolved = loader.resolve_skills(["social_evaluation"])
        injection = loader.build_injection("narration", resolved)
        assert "SOCIAL DYNAMICS AWARENESS" in injection


class TestDirectoryBasedLoader:
    """Test directory-based loading with tmp_path fixtures."""

    def test_loads_from_directory_structure(self, tmp_path):
        """SkillLoader loads from a directory with SKILL.md + injections/."""
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "id: test_skill\n"
            "name: Test Skill\n"
            "description: A test skill\n"
            "tags: [test]\n"
            "targets: [character_agent]\n"
            "priority: 50\n"
            "dependencies: []\n"
            "conflicts: []\n"
            "behavioral_rules:\n"
            "  - Test rule\n"
            "---\n"
        )
        injections_dir = skill_dir / "injections"
        injections_dir.mkdir()
        (injections_dir / "character_agent.md").write_text("Test injection content")

        loader = SkillLoader(skills_dir=tmp_path)
        assert len(loader.list_skills()) == 1
        config = loader.get_skill("test_skill")
        assert config is not None
        assert config.name == "Test Skill"
        assert "character_agent" in config.available_injections
        assert "universal" in config.available_injections["character_agent"]

        # Test loading injection content
        content = loader.load_injection("test_skill", "character_agent", "universal")
        assert content == "Test injection content"

    def test_faction_variant_discovery(self, tmp_path):
        """SkillLoader discovers faction-specific injection variants."""
        skill_dir = tmp_path / "faction_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "id: faction_skill\n"
            "name: Faction Skill\n"
            "targets: [character_agent]\n"
            "---\n"
        )
        injections_dir = skill_dir / "injections"
        injections_dir.mkdir()
        (injections_dir / "character_agent_evil.md").write_text("Evil content")
        (injections_dir / "character_agent_good.md").write_text("Good content")

        loader = SkillLoader(skills_dir=tmp_path)
        config = loader.get_skill("faction_skill")
        assert config is not None
        variants = config.available_injections["character_agent"]
        assert "evil" in variants
        assert "good" in variants

        # Test faction-filtered injection
        resolved = loader.resolve_skills(["faction_skill"])
        evil_inj = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Bad Guys", evil_factions={"Bad Guys"},
        )
        good_inj = loader.build_injection_for_agent(
            "character_agent", resolved,
            faction="Good Guys", evil_factions={"Bad Guys"},
        )
        assert "Evil content" in evil_inj
        assert "Good content" not in evil_inj
        assert "Good content" in good_inj
        assert "Evil content" not in good_inj

    def test_ignores_yaml_files(self, tmp_path):
        """SkillLoader ignores .yaml files in the skills directory."""
        # Create a YAML file (old format) — should be ignored
        (tmp_path / "old_skill.yaml").write_text("id: old_skill\nname: Old Skill\n")
        loader = SkillLoader(skills_dir=tmp_path)
        assert loader.list_skills() == []

    def test_injection_caching(self, tmp_path):
        """Injection content is cached after first load."""
        skill_dir = tmp_path / "cache_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nid: cache_skill\nname: Cache Skill\ntargets: [character_agent]\n---\n"
        )
        injections_dir = skill_dir / "injections"
        injections_dir.mkdir()
        (injections_dir / "character_agent.md").write_text("Original content")

        loader = SkillLoader(skills_dir=tmp_path)
        content1 = loader.load_injection("cache_skill", "character_agent", "universal")
        assert content1 == "Original content"

        # Modify file on disk — cached value should persist
        (injections_dir / "character_agent.md").write_text("Modified content")
        content2 = loader.load_injection("cache_skill", "character_agent", "universal")
        assert content2 == "Original content"  # Still cached
