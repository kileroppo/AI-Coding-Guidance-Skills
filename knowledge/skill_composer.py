"""Skill composition for combining and applying skills.

This module handles composing multiple skills together and applying
them in the context of a development task.
"""

from pathlib import Path
from typing import Any


class SkillComposer:
    """Composes and applies skills from the knowledge base.

    Skills are reusable capability definitions that can be combined
    to handle complex development tasks.
    """

    def __init__(self, knowledge_store: Any) -> None:
        """Initialize the skill composer.

        Args:
            knowledge_store: A KnowledgeStore instance.
        """
        self.knowledge_store = knowledge_store

    def compose(self, skill_names: list) -> str:
        """Load each skill's SKILL.md content and combine into one prompt string.

        Prefixes each with a header (## Skill: {name}).

        Args:
            skill_names: List of skill names to compose.

        Returns:
            Combined prompt string with all skill content.

        Raises:
            ValueError: If any skill is missing.
        """
        issues = self.validate_composition(skill_names)
        if issues:
            raise ValueError(f"Composition validation failed: {'; '.join(issues)}")

        ordered = self.resolve_order(skill_names)
        parts = []
        for name in ordered:
            content = self.get_skill_content(name)
            parts.append(f"## Skill: {name}\n\n{content}")

        return "\n\n---\n\n".join(parts)

    def validate_composition(self, skill_names: list) -> list:
        """Return list of issues (missing skills, etc.).

        Args:
            skill_names: List of skill names to validate.

        Returns:
            List of issue strings. Empty if all valid.
        """
        issues = []
        if not skill_names:
            issues.append("No skills specified")
            return issues
        for name in skill_names:
            try:
                self.knowledge_store.get_skill(name)
            except KeyError:
                issues.append(f"Skill not found: {name}")
        return issues

    def get_skill_content(self, skill_name: str) -> str:
        """Read the SKILL.md file for a given skill.

        Args:
            skill_name: The skill name.

        Returns:
            The content of the SKILL.md file.

        Raises:
            FileNotFoundError: If the SKILL.md file does not exist.
        """
        skill = self.knowledge_store.get_skill(skill_name)
        skill_path = Path(skill.get("path", skill_name))

        # Try relative to knowledge_root/skills/
        skill_md = self.knowledge_store.skills_dir / skill_path / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text(encoding="utf-8")

        # Try the path directly (for skills at repo root level)
        # Go up from knowledge dir to find repo root
        repo_root = self.knowledge_store.knowledge_root.parent
        alt_path = repo_root / skill_path / "SKILL.md"
        if alt_path.exists():
            return alt_path.read_text(encoding="utf-8")

        raise FileNotFoundError(
            f"SKILL.md not found for skill '{skill_name}' at {skill_md} or {alt_path}"
        )

    def resolve_order(self, skill_names: list) -> list:
        """Resolve ordering for skill composition.

        For now, returns as-is (no dependency resolution needed yet).

        Args:
            skill_names: List of skill names.

        Returns:
            Ordered list of skill names.
        """
        return list(skill_names)
