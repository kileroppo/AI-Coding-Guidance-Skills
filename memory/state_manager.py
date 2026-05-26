"""State management for the kernel execution lifecycle.

This module handles reading, updating, and persisting the kernel's state
including current node, iteration count, goals, and error tracking.
"""

import copy
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
    "node_visits": {},
    "progress_history": [],
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
            state = copy.deepcopy(DEFAULT_STATE)
            state["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(self.state_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(state, f, default_flow_style=False, allow_unicode=True)
            return state
        with open(self.state_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # Merge with defaults for any missing keys
        for key, value in DEFAULT_STATE.items():
            if key not in data:
                data[key] = copy.deepcopy(value)
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
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.save_state()

    def track_node_visit(self, node_id: str) -> int:
        """Increment and return the visit count for a node.

        Args:
            node_id: The node being visited.

        Returns:
            The new visit count for this node.
        """
        if "node_visits" not in self.state:
            self.state["node_visits"] = {}
        self.state["node_visits"][node_id] = self.state["node_visits"].get(node_id, 0) + 1
        return self.state["node_visits"][node_id]

    def check_stuck(self, max_retries_map: dict) -> tuple[bool, str | None, int]:
        """Check if any node has exceeded its max_retries.

        Args:
            max_retries_map: Dict of {node_id: max_retries_allowed}

        Returns:
            Tuple of (is_stuck, stuck_node_id_or_None, visit_count)
        """
        node_visits = self.state.get("node_visits", {})
        for node_id, visits in node_visits.items():
            max_allowed = max_retries_map.get(node_id, float('inf'))
            if visits > max_allowed:
                return (True, node_id, visits)
        return (False, None, 0)

    def check_convergence(self, lookback: int = 5) -> tuple[bool, int]:
        """Check if progress has stalled (tasks_done unchanged over lookback iterations).

        Looks at the progress_history list in state. If the last `lookback` entries
        all have the same tasks_done value and iteration_count > lookback, progress
        is considered stalled.

        Args:
            lookback: Number of iterations without progress to consider stalled.

        Returns:
            Tuple of (is_stalled, stale_iterations_count).
        """
        history = self.state.get("progress_history", [])
        if len(history) < lookback:
            return (False, 0)
        recent = history[-lookback:]
        # All recent entries have same tasks_done value
        if all(entry == recent[0] for entry in recent):
            iteration_count = self.state.get("iteration_count", 0)
            if iteration_count > lookback:
                return (True, lookback)
        return (False, 0)
