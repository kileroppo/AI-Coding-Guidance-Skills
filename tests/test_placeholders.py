"""Tests for placeholder methods that raise NotImplementedError.

These tests verify that placeholder methods correctly raise NotImplementedError
as documented, and that they will be implemented in FEAT-002.
"""

from pathlib import Path

import pytest


class TestEvolutionEnginePlaceholders:
    """Tests for EvolutionEngine placeholder methods."""

    def test_propose_raises(self, kernel_root: Path) -> None:
        """Test that propose raises NotImplementedError."""
        from kernel.evolution.engine import EvolutionEngine
        eng = EvolutionEngine(kernel_root)
        with pytest.raises(NotImplementedError):
            eng.propose("change", "target.md", "content")

    def test_validate_raises(self, kernel_root: Path) -> None:
        """Test that validate raises NotImplementedError."""
        from kernel.evolution.engine import EvolutionEngine
        eng = EvolutionEngine(kernel_root)
        with pytest.raises(NotImplementedError):
            eng.validate("some_file.md")

    def test_apply_raises(self, kernel_root: Path) -> None:
        """Test that apply raises NotImplementedError."""
        from kernel.evolution.engine import EvolutionEngine
        eng = EvolutionEngine(kernel_root)
        with pytest.raises(NotImplementedError):
            eng.apply({"change": "data"})

    def test_get_history_raises(self, kernel_root: Path) -> None:
        """Test that get_history raises NotImplementedError."""
        from kernel.evolution.engine import EvolutionEngine
        eng = EvolutionEngine(kernel_root)
        with pytest.raises(NotImplementedError):
            eng.get_history()


class TestStateManagerPlaceholders:
    """Tests for StateManager placeholder methods."""

    def test_load_state_raises(self, kernel_root: Path) -> None:
        """Test that load_state raises NotImplementedError."""
        from memory.state_manager import StateManager
        sm = StateManager(kernel_root)
        with pytest.raises(NotImplementedError):
            sm.load_state()

    def test_save_state_raises(self, kernel_root: Path) -> None:
        """Test that save_state raises NotImplementedError."""
        from memory.state_manager import StateManager
        sm = StateManager(kernel_root)
        with pytest.raises(NotImplementedError):
            sm.save_state({"key": "value"})

    def test_advance_node_raises(self, kernel_root: Path) -> None:
        """Test that advance_node raises NotImplementedError."""
        from memory.state_manager import StateManager
        sm = StateManager(kernel_root)
        with pytest.raises(NotImplementedError):
            sm.advance_node({"current_node": "init"}, "plan")

    def test_record_error_raises(self, kernel_root: Path) -> None:
        """Test that record_error raises NotImplementedError."""
        from memory.state_manager import StateManager
        sm = StateManager(kernel_root)
        with pytest.raises(NotImplementedError):
            sm.record_error({"errors": []}, "test error")


class TestKnowledgeStorePlaceholders:
    """Tests for KnowledgeStore placeholder methods."""

    def test_load_rules_raises(self, kernel_root: Path) -> None:
        """Test that load_rules raises NotImplementedError."""
        from knowledge.store import KnowledgeStore
        ks = KnowledgeStore(kernel_root / "knowledge")
        with pytest.raises(NotImplementedError):
            ks.load_rules()

    def test_load_patterns_raises(self, kernel_root: Path) -> None:
        """Test that load_patterns raises NotImplementedError."""
        from knowledge.store import KnowledgeStore
        ks = KnowledgeStore(kernel_root / "knowledge")
        with pytest.raises(NotImplementedError):
            ks.load_patterns()

    def test_add_learned_rule_raises(self, kernel_root: Path) -> None:
        """Test that add_learned_rule raises NotImplementedError."""
        from knowledge.store import KnowledgeStore
        ks = KnowledgeStore(kernel_root / "knowledge")
        with pytest.raises(NotImplementedError):
            ks.add_learned_rule({"id": "test", "description": "test"})

    def test_add_pattern_raises(self, kernel_root: Path) -> None:
        """Test that add_pattern raises NotImplementedError."""
        from knowledge.store import KnowledgeStore
        ks = KnowledgeStore(kernel_root / "knowledge")
        with pytest.raises(NotImplementedError):
            ks.add_pattern({"id": "test", "description": "test"})


class TestSkillComposerPlaceholders:
    """Tests for SkillComposer placeholder methods."""

    def test_list_skills_raises(self, kernel_root: Path) -> None:
        """Test that list_skills raises NotImplementedError."""
        from knowledge.skill_composer import SkillComposer
        sc = SkillComposer(kernel_root / "knowledge" / "skills")
        with pytest.raises(NotImplementedError):
            sc.list_skills()

    def test_load_skill_raises(self, kernel_root: Path) -> None:
        """Test that load_skill raises NotImplementedError."""
        from knowledge.skill_composer import SkillComposer
        sc = SkillComposer(kernel_root / "knowledge" / "skills")
        with pytest.raises(NotImplementedError):
            sc.load_skill("test-skill")

    def test_compose_raises(self, kernel_root: Path) -> None:
        """Test that compose raises NotImplementedError."""
        from knowledge.skill_composer import SkillComposer
        sc = SkillComposer(kernel_root / "knowledge" / "skills")
        with pytest.raises(NotImplementedError):
            sc.compose(["skill-1", "skill-2"])
