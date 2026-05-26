"""Tests for the knowledge package."""

from pathlib import Path

import pytest
import yaml


class TestKnowledgeStructure:
    """Tests for knowledge directory structure."""

    def test_knowledge_package_importable(self) -> None:
        """Test that knowledge package can be imported."""
        import knowledge
        assert knowledge is not None

    def test_store_importable(self) -> None:
        """Test that knowledge.store can be imported."""
        from knowledge import store
        assert store is not None

    def test_knowledge_store_class_exists(self) -> None:
        """Test that KnowledgeStore class exists."""
        from knowledge.store import KnowledgeStore
        assert KnowledgeStore is not None

    def test_knowledge_store_instantiation(self, kernel_root: Path) -> None:
        """Test that KnowledgeStore can be instantiated."""
        from knowledge.store import KnowledgeStore
        ks = KnowledgeStore(kernel_root / "knowledge")
        assert ks.knowledge_root == kernel_root / "knowledge"

    def test_skill_composer_importable(self) -> None:
        """Test that knowledge.skill_composer can be imported."""
        from knowledge.skill_composer import SkillComposer
        assert SkillComposer is not None

    def test_skill_composer_instantiation(self, kernel_root: Path) -> None:
        """Test that SkillComposer can be instantiated."""
        from knowledge.skill_composer import SkillComposer
        sc = SkillComposer(kernel_root / "knowledge" / "skills")
        assert sc.skills_dir == kernel_root / "knowledge" / "skills"


class TestKnowledgeFiles:
    """Tests for knowledge directory files."""

    def test_rules_index_exists(self, kernel_root: Path) -> None:
        """Test that rules/_index.yaml exists and is valid."""
        path = kernel_root / "knowledge" / "rules" / "_index.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert "items" in data

    def test_skills_index_exists(self, kernel_root: Path) -> None:
        """Test that skills/_index.yaml exists and is valid."""
        path = kernel_root / "knowledge" / "skills" / "_index.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert "items" in data

    def test_patterns_index_exists(self, kernel_root: Path) -> None:
        """Test that patterns/_index.yaml exists and is valid."""
        path = kernel_root / "knowledge" / "patterns" / "_index.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert "items" in data

    def test_rules_manual_dir_exists(self, kernel_root: Path) -> None:
        """Test that rules/manual/ directory exists."""
        assert (kernel_root / "knowledge" / "rules" / "manual").is_dir()

    def test_rules_learned_dir_exists(self, kernel_root: Path) -> None:
        """Test that rules/learned/ directory exists."""
        assert (kernel_root / "knowledge" / "rules" / "learned").is_dir()

    def test_patterns_dir_exists(self, kernel_root: Path) -> None:
        """Test that patterns/ directory exists."""
        assert (kernel_root / "knowledge" / "patterns").is_dir()
