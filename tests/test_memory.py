"""Tests for the memory package."""

from pathlib import Path

import pytest
import yaml


class TestMemoryStructure:
    """Tests for memory directory structure."""

    def test_memory_package_importable(self) -> None:
        """Test that memory package can be imported."""
        import memory
        assert memory is not None

    def test_state_manager_importable(self) -> None:
        """Test that memory.state_manager can be imported."""
        from memory import state_manager
        assert state_manager is not None

    def test_state_manager_class_exists(self) -> None:
        """Test that StateManager class exists."""
        from memory.state_manager import StateManager
        assert StateManager is not None

    def test_state_manager_instantiation(self, kernel_root: Path) -> None:
        """Test that StateManager can be instantiated."""
        from memory.state_manager import StateManager
        sm = StateManager(kernel_root)
        assert sm.kernel_root == kernel_root

    def test_state_manager_methods_exist(self, kernel_root: Path) -> None:
        """Test that StateManager has all expected methods."""
        from memory.state_manager import StateManager
        sm = StateManager(kernel_root)
        assert hasattr(sm, "load_state")
        assert hasattr(sm, "save_state")
        assert hasattr(sm, "advance_node")
        assert hasattr(sm, "record_error")


class TestMemoryFiles:
    """Tests for memory directory files."""

    def test_progress_yaml_exists(self, kernel_root: Path) -> None:
        """Test that progress.yaml exists and is valid."""
        path = kernel_root / "memory" / "progress.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert "iteration" in data
        assert "tasks_total" in data
        assert "tasks_done" in data
        assert "status" in data

    def test_current_goal_exists(self, kernel_root: Path) -> None:
        """Test that current_goal.md exists."""
        assert (kernel_root / "memory" / "current_goal.md").exists()

    def test_plan_md_exists(self, kernel_root: Path) -> None:
        """Test that plan.md exists."""
        assert (kernel_root / "memory" / "plan.md").exists()

    def test_decisions_jsonl_exists(self, kernel_root: Path) -> None:
        """Test that decisions.jsonl exists."""
        assert (kernel_root / "memory" / "decisions.jsonl").exists()

    def test_reflections_jsonl_exists(self, kernel_root: Path) -> None:
        """Test that reflections.jsonl exists."""
        assert (kernel_root / "memory" / "reflections.jsonl").exists()
