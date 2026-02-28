"""SkillLoader — discovers, validates, and resolves directory-based skill configs for runtime agent injection.

Skills are stored as directories with SKILL.md (YAML frontmatter) + injections/ subdirectory.
Injection content is loaded on-demand and cached, supporting faction-specific variants.
"""

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
    """A parsed skill definition loaded from a SKILL.md directory."""

    id: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    priority: int = 50
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    behavioral_rules: list[str] = field(default_factory=list)
    # Directory path for this skill
    skill_dir: Path = field(default_factory=Path)
    # Mapping: target -> list of variants (e.g. ["universal"] or ["evil", "good"])
    available_injections: dict[str, list[str]] = field(default_factory=dict)


class SkillLoader:
    """Discovers, validates, and resolves directory-based skill definitions."""

    def __init__(self, skills_dir: Path | None = None):
        self._dir = skills_dir or SKILLS_DIR
        self._skills: dict[str, SkillConfig] = {}
        self._injection_cache: dict[str, str] = {}  # "skill_id:target:variant" -> content
        self._load_all()

    def _load_all(self):
        """Scan skills directory for subdirectories containing SKILL.md."""
        if not self._dir.is_dir():
            logger.warning("Skills directory not found: %s", self._dir)
            return

        for path in sorted(self._dir.iterdir()):
            if path.is_dir() and (path / "SKILL.md").exists():
                try:
                    self._load_skill_dir(path)
                except Exception as exc:
                    logger.warning("Failed to load skill %s: %s", path.name, exc)

    def _load_skill_dir(self, path: Path):
        """Parse SKILL.md frontmatter and discover injection files."""
        skill_md = path / "SKILL.md"
        raw = self._parse_frontmatter(skill_md)

        if not isinstance(raw, dict) or "id" not in raw:
            raise ValueError(f"SKILL.md missing 'id': {path.name}")

        # Validate targets
        targets = raw.get("targets", [])
        invalid = set(targets) - VALID_TARGETS
        if invalid:
            logger.warning("Skill %s has invalid targets: %s", raw["id"], invalid)

        # Discover injection files
        available_injections = self._discover_injections(path)

        skill = SkillConfig(
            id=raw["id"],
            name=raw.get("name", raw["id"]),
            description=raw.get("description", ""),
            tags=raw.get("tags", []),
            targets=[t for t in targets if t in VALID_TARGETS],
            priority=raw.get("priority", 50),
            dependencies=raw.get("dependencies", []),
            conflicts=raw.get("conflicts", []),
            behavioral_rules=raw.get("behavioral_rules", []),
            skill_dir=path,
            available_injections=available_injections,
        )
        self._skills[skill.id] = skill

    @staticmethod
    def _parse_frontmatter(path: Path) -> dict:
        """Extract YAML frontmatter from a SKILL.md file (between --- delimiters)."""
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            raise ValueError(f"SKILL.md does not start with ---: {path}")

        # Find the closing ---
        end = text.index("---", 3)
        yaml_block = text[3:end]
        return yaml.safe_load(yaml_block) or {}

    @staticmethod
    def _discover_injections(skill_dir: Path) -> dict[str, list[str]]:
        """Scan injections/ subdirectory and build target -> variants mapping.

        File naming convention:
          - {target}.md -> "universal" variant
          - {target}_evil.md -> "evil" variant
          - {target}_good.md -> "good" variant
        """
        injections_dir = skill_dir / "injections"
        if not injections_dir.is_dir():
            return {}

        result: dict[str, list[str]] = {}
        for f in sorted(injections_dir.glob("*.md")):
            stem = f.stem  # e.g. "character_agent", "character_agent_evil"
            # Check for faction suffix
            if stem.endswith("_evil"):
                target = stem[:-5]  # strip "_evil"
                result.setdefault(target, []).append("evil")
            elif stem.endswith("_good"):
                target = stem[:-5]  # strip "_good"
                result.setdefault(target, []).append("good")
            else:
                target = stem
                result.setdefault(target, []).append("universal")

        return result

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

    # ── Injection loading ────────────────────────────────────────────

    def load_injection(self, skill_id: str, target: str, variant: str = "universal") -> str:
        """Load a single injection file on-demand, with caching.

        Args:
            skill_id: The skill ID.
            target: The injection target (e.g. "character_agent").
            variant: "universal", "evil", or "good".

        Returns:
            The injection content, or "" if the file does not exist.
        """
        cache_key = f"{skill_id}:{target}:{variant}"
        if cache_key in self._injection_cache:
            return self._injection_cache[cache_key]

        skill = self._skills.get(skill_id)
        if not skill:
            self._injection_cache[cache_key] = ""
            return ""

        injections_dir = skill.skill_dir / "injections"
        if variant == "universal":
            file_path = injections_dir / f"{target}.md"
        else:
            file_path = injections_dir / f"{target}_{variant}.md"

        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8").strip()
        else:
            content = ""

        self._injection_cache[cache_key] = content
        return content

    def build_injection_for_agent(
        self,
        target: str,
        skills: list[SkillConfig],
        faction: str,
        evil_factions: set[str],
    ) -> str:
        """Build injection text for a specific agent, filtering by faction.

        For each skill:
          1. Load the universal injection (if it exists)
          2. Load the faction-specific variant (evil or good)
          3. Combine both

        Args:
            target: The injection target (e.g. "character_agent").
            skills: List of resolved SkillConfig objects.
            faction: The agent's faction name.
            evil_factions: Set of faction names that are evil-aligned.

        Returns:
            Combined injection text for all skills.
        """
        faction_type = "evil" if faction in evil_factions else "good"
        parts: list[str] = []

        for skill in skills:
            variants = skill.available_injections.get(target, [])
            if not variants:
                continue

            # Load universal first
            if "universal" in variants:
                text = self.load_injection(skill.id, target, "universal")
                if text:
                    parts.append(text)

            # Load faction-specific variant
            if faction_type in variants:
                text = self.load_injection(skill.id, target, faction_type)
                if text:
                    parts.append(text)

        return "\n\n".join(parts)

    def build_injection(self, target: str, skills: list[SkillConfig]) -> str:
        """Build injection text without faction filtering (for GameMaster targets like narration).

        Loads only universal injection files.
        """
        parts: list[str] = []
        for skill in skills:
            variants = skill.available_injections.get(target, [])
            if "universal" in variants:
                text = self.load_injection(skill.id, target, "universal")
                if text:
                    parts.append(text)
        return "\n\n".join(parts)

    def collect_behavioral_rules(self, skills: list[SkillConfig]) -> list[str]:
        """Gather all behavioral rules from a list of active skills."""
        rules: list[str] = []
        for skill in skills:
            rules.extend(skill.behavioral_rules)
        return rules
