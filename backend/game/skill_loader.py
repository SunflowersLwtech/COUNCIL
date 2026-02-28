"""SkillLoader — discovers, validates, and resolves YAML skill configs for runtime agent injection."""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent / "skills"

VALID_TARGETS = {
    "character_agent",
    "vote_prompt",
    "night_action",
    "narration",
    "responder_selection",
    "spontaneous_reaction",
    "round_summary",
}


@dataclass
class SkillConfig:
    """A parsed skill definition loaded from YAML."""

    id: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    priority: int = 50
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    injections: dict[str, str] = field(default_factory=dict)
    behavioral_rules: list[str] = field(default_factory=list)


class SkillLoader:
    """Discovers, validates, and resolves YAML skill files from the skills directory."""

    def __init__(self, skills_dir: Path | None = None):
        self._dir = skills_dir or SKILLS_DIR
        self._skills: dict[str, SkillConfig] = {}
        self._load_all()

    def _load_all(self):
        """Scan skills directory and parse every .yaml file."""
        if not self._dir.is_dir():
            logger.warning("Skills directory not found: %s", self._dir)
            return

        for path in sorted(self._dir.glob("*.yaml")):
            try:
                self._load_file(path)
            except Exception as exc:
                logger.warning("Failed to load skill %s: %s", path.name, exc)

    def _load_file(self, path: Path):
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict) or "id" not in raw:
            raise ValueError(f"Skill YAML missing 'id': {path.name}")

        # Validate targets
        targets = raw.get("targets", [])
        invalid = set(targets) - VALID_TARGETS
        if invalid:
            logger.warning("Skill %s has invalid targets: %s", raw["id"], invalid)

        injections = raw.get("injections", {})
        if isinstance(injections, dict):
            injections = {k: str(v) for k, v in injections.items()}
        else:
            injections = {}

        skill = SkillConfig(
            id=raw["id"],
            name=raw.get("name", raw["id"]),
            description=raw.get("description", ""),
            tags=raw.get("tags", []),
            targets=[t for t in targets if t in VALID_TARGETS],
            priority=raw.get("priority", 50),
            dependencies=raw.get("dependencies", []),
            conflicts=raw.get("conflicts", []),
            injections=injections,
            behavioral_rules=raw.get("behavioral_rules", []),
        )
        self._skills[skill.id] = skill

    def get_skill(self, skill_id: str) -> SkillConfig | None:
        return self._skills.get(skill_id)

    def list_skills(self) -> list[dict]:
        """Return a summary list of all available skills."""
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "tags": s.tags,
                "priority": s.priority,
                "targets": s.targets,
            }
            for s in sorted(self._skills.values(), key=lambda s: s.priority)
        ]

    def all_skill_ids(self) -> list[str]:
        return list(self._skills.keys())

    def resolve_skills(self, skill_ids: list[str]) -> list[SkillConfig]:
        """Resolve dependencies and detect conflicts. Returns priority-sorted list.

        Raises ValueError on unresolvable conflicts or missing dependencies.
        """
        resolved_ids: set[str] = set()
        order: list[str] = []

        def _add(sid: str, chain: set[str] | None = None):
            if sid in resolved_ids:
                return
            if chain is None:
                chain = set()
            if sid in chain:
                raise ValueError(f"Circular dependency detected: {sid}")
            skill = self._skills.get(sid)
            if not skill:
                raise ValueError(f"Unknown skill: {sid}")
            chain = chain | {sid}
            for dep in skill.dependencies:
                _add(dep, chain)
            resolved_ids.add(sid)
            order.append(sid)

        for sid in skill_ids:
            _add(sid)

        # Conflict detection
        active = {sid: self._skills[sid] for sid in order}
        for sid, skill in active.items():
            for conflict_id in skill.conflicts:
                if conflict_id in active:
                    raise ValueError(
                        f"Skill conflict: '{sid}' conflicts with '{conflict_id}'"
                    )

        return sorted(
            [self._skills[sid] for sid in order],
            key=lambda s: s.priority,
        )

    def build_injection(self, target: str, skills: list[SkillConfig]) -> str:
        """Combine prompt fragments from all active skills for a given target component."""
        parts: list[str] = []
        for skill in skills:
            fragment = skill.injections.get(target, "")
            if fragment:
                parts.append(fragment)
        return "\n\n".join(parts)

    def collect_behavioral_rules(self, skills: list[SkillConfig]) -> list[str]:
        """Gather all behavioral rules from a list of active skills."""
        rules: list[str] = []
        for skill in skills:
            rules.extend(skill.behavioral_rules)
        return rules
