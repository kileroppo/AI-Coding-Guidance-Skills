"""Tests for the memory package."""

import json
from pathlib import Path

import pytest
import yaml

from memory.state_manager import StateManager


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


class TestStateManagerInit:
    """Tests for StateManager initialization."""

    def test_instantiation(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test that StateManager can be instantiated."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        assert sm.state_path == tmp_state
        assert sm.memory_dir == tmp_memory

    def test_load_state_creates_default_if_missing(self, tmp_path: Path) -> None:
        """Test that load_state creates a default state file if missing."""
        state_file = tmp_path / "new_state.yaml"
        memory_dir = tmp_path / "mem"
        memory_dir.mkdir()
        sm = StateManager(str(state_file), str(memory_dir))
        state = sm.get_state()
        assert state["current_node"] == "init"
        assert state["iteration_count"] == 0
        assert state_file.exists()

    def test_load_existing_state(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test loading existing state.yaml."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        state = sm.get_state()
        assert state["current_node"] == "init"
        assert state["status"] == "idle"


class TestStateManagerOperations:
    """Tests for StateManager state operations."""

    def test_set_current_node(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test setting current node."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.set_current_node("plan")
        assert sm.state["current_node"] == "plan"

    def test_increment_iteration(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test incrementing iteration count."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        assert sm.state["iteration_count"] == 0
        sm.increment_iteration()
        assert sm.state["iteration_count"] == 1
        sm.increment_iteration()
        assert sm.state["iteration_count"] == 2

    def test_increment_updates_timestamp(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test that increment_iteration updates last_updated."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.increment_iteration()
        assert sm.state["last_updated"] != ""

    def test_save_state(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test saving state persists changes."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.set_current_node("code")
        sm.increment_iteration()
        sm.save_state()

        # Reload and verify
        sm2 = StateManager(str(tmp_state), str(tmp_memory))
        assert sm2.state["current_node"] == "code"
        assert sm2.state["iteration_count"] == 1

    def test_set_goal(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test setting a goal."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.set_goal("Build a REST API")
        assert sm.state["goal"] == "Build a REST API"
        goal_file = tmp_memory / "current_goal.md"
        assert goal_file.exists()
        assert "Build a REST API" in goal_file.read_text()

    def test_record_decision(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test recording a decision."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.record_decision({"action": "chose_library", "value": "fastapi"})
        decisions_file = tmp_memory / "decisions.jsonl"
        lines = decisions_file.read_text().strip().split("\n")
        record = json.loads(lines[-1])
        assert record["action"] == "chose_library"
        assert "timestamp" in record

    def test_record_reflection(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test recording a reflection."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.record_reflection({"node": "code", "success": True})
        reflections_file = tmp_memory / "reflections.jsonl"
        lines = reflections_file.read_text().strip().split("\n")
        record = json.loads(lines[-1])
        assert record["node"] == "code"
        assert "timestamp" in record

    def test_update_progress(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test updating progress."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.update_progress(10, 5)
        progress_file = tmp_memory / "progress.yaml"
        data = yaml.safe_load(progress_file.read_text())
        assert data["tasks_total"] == 10
        assert data["tasks_done"] == 5
        assert data["status"] == "in_progress"

    def test_update_progress_complete(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test that progress shows complete when tasks_done >= tasks_total."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.update_progress(5, 5)
        progress_file = tmp_memory / "progress.yaml"
        data = yaml.safe_load(progress_file.read_text())
        assert data["status"] == "complete"

    def test_is_complete_status(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test is_complete when status is 'complete'."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.state["status"] = "complete"
        assert sm.is_complete() is True

    def test_is_complete_progress(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test is_complete based on progress tasks."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.update_progress(5, 5)
        assert sm.is_complete() is True

    def test_is_not_complete(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test is_complete returns False when not done."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        assert sm.is_complete() is False

    def test_reset(self, tmp_state: Path, tmp_memory: Path) -> None:
        """Test resetting state to defaults."""
        sm = StateManager(str(tmp_state), str(tmp_memory))
        sm.set_current_node("code")
        sm.increment_iteration()
        sm.reset()
        assert sm.state["current_node"] == "init"
        assert sm.state["iteration_count"] == 0
        assert sm.state["status"] == "idle"


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
