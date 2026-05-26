"""State management for the kernel execution lifecycle.

This module handles reading, updating, and persisting the kernel's state
including current node, iteration count, goals, and error tracking.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DEFAULT_STATE = {
    "current_node": "init",
    "iteration_count": 0,
    "max_iterations": 30,
    "goal": "",
    "status": "idle",
    "last_updated": "",
    "errors": [],
    "context": {
        "skills_loaded": [],
        "current_task": "",
        "phase": "startup",
    },
}


class StateManager:
    """Manages kernel execution state via filesystem persistence.

    State is stored in YAML files and updated after each node execution.
    All state is file-based to support stateless AI agent execution.
    """

    def __init__(self, state_path: str, memory_dir: str) -> None:
        """Initialize the state manager.

        Args:
            state_path: Path to the state.yaml file.
            memory_dir: Path to the memory/ directory.
        """
        self.state_path = Path(state_path)
        self.memory_dir = Path(memory_dir)
        self.state: dict[str, Any] = self.load_state()

    def load_state(self) -> dict[str, Any]:
        """Load state.yaml, create default if missing.

        Returns:
            Dict containing the current state.
        """
        if not self.state_path.exists():
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            state = dict(DEFAULT_STATE)
            state["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(self.state_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(state, f, default_flow_style=False, allow_unicode=True)
            return state
        with open(self.state_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # Merge with defaults for any missing keys
        for key, value in DEFAULT_STATE.items():
            if key not in data:
                data[key] = value
        self.state = data
        return data

    def save_state(self) -> None:
        """Write current state to state.yaml."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.state, f, default_flow_style=False, allow_unicode=True)

    def get_state(self) -> dict[str, Any]:
        """Return current state dict.

        Returns:
            The current state dictionary.
        """
        return self.state

    def set_current_node(self, node_id: str) -> None:
        """Update current node.

        Args:
            node_id: The new current node ID.
        """
        self.state["current_node"] = node_id

    def increment_iteration(self) -> None:
        """Increment iteration_count and update last_updated timestamp."""
        self.state["iteration_count"] = self.state.get("iteration_count", 0) + 1
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()

    def record_decision(self, decision: dict) -> None:
        """Append JSON line to decisions.jsonl.

        Args:
            decision: Decision dict to record.
        """
        decision.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.memory_dir / "decisions.jsonl"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(decision) + "\n")

    def record_reflection(self, reflection: dict) -> None:
        """Append JSON line to reflections.jsonl.

        Args:
            reflection: Reflection dict to record.
        """
        reflection.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.memory_dir / "reflections.jsonl"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(reflection) + "\n")

    def update_progress(self, tasks_total: int, tasks_done: int) -> None:
        """Update progress.yaml.

        Args:
            tasks_total: Total number of tasks.
            tasks_done: Number of completed tasks.
        """
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        progress_path = self.memory_dir / "progress.yaml"
        progress = {
            "iteration": self.state.get("iteration_count", 0),
            "tasks_total": tasks_total,
            "tasks_done": tasks_done,
            "status": "complete" if tasks_done >= tasks_total and tasks_total > 0 else "in_progress",
        }
        with open(progress_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(progress, f, default_flow_style=False, allow_unicode=True)

    def set_goal(self, goal: str) -> None:
        """Set goal in state and write to current_goal.md.

        Args:
            goal: The goal string.
        """
        self.state["goal"] = goal
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        goal_path = self.memory_dir / "current_goal.md"
        with open(goal_path, "w", encoding="utf-8") as f:
            f.write(f"# Current Goal\n\n{goal}\n")

    def is_complete(self) -> bool:
        """Check if execution is complete.

        Returns:
            True if status is 'complete' or tasks_done >= tasks_total (and tasks_total > 0).
        """
        if self.state.get("status") == "complete":
            return True
        # Check progress
        progress_path = self.memory_dir / "progress.yaml"
        if progress_path.exists():
            with open(progress_path, "r", encoding="utf-8") as f:
                progress = yaml.safe_load(f) or {}
            tasks_total = progress.get("tasks_total", 0)
            tasks_done = progress.get("tasks_done", 0)
            if tasks_total > 0 and tasks_done >= tasks_total:
                return True
        return False

    def reset(self) -> None:
        """Reset state to defaults."""
        self.state = dict(DEFAULT_STATE)
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.save_state()
