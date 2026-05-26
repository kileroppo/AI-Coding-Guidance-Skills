"""Tests for the EvolutionEngine class."""

import json
from pathlib import Path

import pytest
import yaml

from kernel.evolution.engine import EvolutionEngine, IMMUTABLE_FILES, VALID_CHANGE_TYPES
from kernel.graph_executor import GraphExecutor


@pytest.fixture
def evolution_setup(tmp_path: Path):
    """Set up a temporary kernel directory with graph for evolution tests."""
    kernel_dir = tmp_path / "kernel"
    kernel_dir.mkdir()
    (kernel_dir / "evolution").mkdir()
    (kernel_dir / "prompts").mkdir()

    # Create a graph file
    graph_file = kernel_dir / "graph.yaml"
    graph_data = {
        "version": "1.0",
        "nodes": [
            {
                "id": "init",
                "prompt_file": "prompts/orchestrator.md",
                "description": "Initialize",
                "transitions": [{"to": "plan", "condition": "goal_loaded"}],
                "max_retries": 1,
            },
            {
                "id": "plan",
                "prompt_file": "prompts/planner.md",
                "description": "Plan",
                "transitions": [{"to": "code", "condition": "plan_ready"}],
                "max_retries": 2,
            },
            {
                "id": "code",
                "prompt_file": "prompts/coder.md",
                "description": "Code",
                "transitions": [{"to": "init", "condition": "done"}],
                "max_retries": 3,
            },
        ],
        "default_start": "init",
        "max_iterations": 30,
    }
    with open(graph_file, "w") as f:
        yaml.safe_dump(graph_data, f)

    # Create prompt files
    (kernel_dir / "prompts" / "orchestrator.md").write_text("Orchestrator prompt")
    (kernel_dir / "prompts" / "planner.md").write_text("Planner prompt")
    (kernel_dir / "prompts" / "coder.md").write_text("Coder prompt")

    graph_executor = GraphExecutor(str(graph_file))
    engine = EvolutionEngine(str(kernel_dir), graph_executor)
    return engine, kernel_dir, graph_executor


class TestEvolutionEngineInit:
    """Tests for EvolutionEngine initialization."""

    def test_instantiation(self, evolution_setup) -> None:
        """Test that EvolutionEngine can be instantiated."""
        engine, kernel_dir, _ = evolution_setup
        assert engine.kernel_dir == kernel_dir

    def test_immutable_files_constant(self) -> None:
        """Test that IMMUTABLE_FILES contains the correct paths."""
        assert "kernel/BOOT.md" in IMMUTABLE_FILES
        assert "kernel/constitution.md" in IMMUTABLE_FILES
        assert "runner.py" in IMMUTABLE_FILES


class TestProposeChange:
    """Tests for propose_change."""

    def test_propose_returns_dict(self, evolution_setup) -> None:
        """Test that propose_change returns a proper dict."""
        engine, _, _ = evolution_setup
        change = engine.propose_change("add_node", {"node": {"id": "test"}}, "testing")
        assert "id" in change
        assert change["type"] == "add_node"
        assert change["reason"] == "testing"
        assert change["status"] == "proposed"
        assert "timestamp" in change

    def test_propose_generates_unique_ids(self, evolution_setup) -> None:
        """Test that each proposal gets a unique ID."""
        engine, _, _ = evolution_setup
        c1 = engine.propose_change("add_node", {}, "r1")
        c2 = engine.propose_change("add_node", {}, "r2")
        assert c1["id"] != c2["id"]


class TestValidateChange:
    """Tests for validate_change."""

    def test_valid_change(self, evolution_setup) -> None:
        """Test validation of a valid change."""
        engine, _, _ = evolution_setup
        change = engine.propose_change(
            "add_node", {"node": {"id": "new"}}, "Add new node"
        )
        valid, reason = engine.validate_change(change)
        assert valid is True

    def test_reject_invalid_type(self, evolution_setup) -> None:
        """Test that invalid change types are rejected."""
        engine, _, _ = evolution_setup
        change = {"type": "invalid_type", "details": {}}
        valid, reason = engine.validate_change(change)
        assert valid is False
        assert "Invalid change type" in reason

    def test_reject_protected_target_file(self, evolution_setup) -> None:
        """Test that changes to protected files are rejected."""
        engine, _, _ = evolution_setup
        change = {
            "type": "modify_prompt",
            "details": {"target_file": "kernel/BOOT.md"},
        }
        valid, reason = engine.validate_change(change)
        assert valid is False
        assert "protected file" in reason

    def test_reject_protected_runner(self, evolution_setup) -> None:
        """Test that changes to runner.py are rejected."""
        engine, _, _ = evolution_setup
        change = {
            "type": "modify_prompt",
            "details": {"target_file": "runner.py"},
        }
        valid, reason = engine.validate_change(change)
        assert valid is False

    def test_reject_protected_constitution(self, evolution_setup) -> None:
        """Test that changes to constitution.md are rejected."""
        engine, _, _ = evolution_setup
        change = {
            "type": "modify_prompt",
            "details": {"path": "kernel/constitution.md"},
        }
        valid, reason = engine.validate_change(change)
        assert valid is False

    def test_reject_remove_node_without_id(self, evolution_setup) -> None:
        """Test that remove_node without node_id is rejected."""
        engine, _, _ = evolution_setup
        change = {"type": "remove_node", "details": {}}
        valid, reason = engine.validate_change(change)
        assert valid is False
        assert "node_id" in reason

    def test_reject_add_node_without_id(self, evolution_setup) -> None:
        """Test that add_node without node.id is rejected."""
        engine, _, _ = evolution_setup
        change = {"type": "add_node", "details": {"node": {}}}
        valid, reason = engine.validate_change(change)
        assert valid is False


class TestApplyChange:
    """Tests for apply_change."""

    def test_apply_add_node(self, evolution_setup) -> None:
        """Test applying an add_node change."""
        engine, _, graph_executor = evolution_setup
        change = engine.propose_change(
            "add_node",
            {"node": {"id": "deploy", "prompt_file": "prompts/deploy.md", "description": "Deploy"}},
            "Add deployment step",
        )
        result = engine.apply_change(change)
        assert result is True
        # Verify node was added
        node = graph_executor.get_node("deploy")
        assert node["id"] == "deploy"

    def test_apply_remove_node(self, evolution_setup) -> None:
        """Test applying a remove_node change."""
        engine, _, graph_executor = evolution_setup
        # Add an isolated node first
        graph_executor.add_node({"id": "isolated", "description": "Temp"})
        change = engine.propose_change(
            "remove_node", {"node_id": "isolated"}, "Remove temp node"
        )
        result = engine.apply_change(change)
        assert result is True
        with pytest.raises(KeyError):
            graph_executor.get_node("isolated")

    def test_apply_modify_prompt(self, evolution_setup) -> None:
        """Test applying a modify_prompt change."""
        engine, kernel_dir, _ = evolution_setup
        change = engine.propose_change(
            "modify_prompt",
            {"prompt_file": "prompts/planner.md", "content": "New planner content"},
            "Update planner prompt",
        )
        result = engine.apply_change(change)
        assert result is True
        prompt_path = kernel_dir / "prompts" / "planner.md"
        assert prompt_path.read_text() == "New planner content"

    def test_apply_rejected_change(self, evolution_setup) -> None:
        """Test that applying a change targeting protected files fails."""
        engine, _, _ = evolution_setup
        change = engine.propose_change(
            "modify_prompt",
            {"target_file": "kernel/BOOT.md", "content": "hacked"},
            "Try to modify protected",
        )
        result = engine.apply_change(change)
        assert result is False

    def test_apply_logs_to_history(self, evolution_setup) -> None:
        """Test that applied changes are logged to history."""
        engine, kernel_dir, _ = evolution_setup
        change = engine.propose_change(
            "add_node",
            {"node": {"id": "logged", "description": "test"}},
            "test logging",
        )
        engine.apply_change(change)
        history = engine.get_history()
        assert len(history) >= 1
        assert history[-1]["status"] == "applied"


class TestGetHistory:
    """Tests for get_history."""

    def test_empty_history(self, evolution_setup) -> None:
        """Test getting history when no changes have been made."""
        engine, kernel_dir, _ = evolution_setup
        # Clear history file
        history_file = kernel_dir / "evolution" / "history.jsonl"
        history_file.write_text("")
        history = engine.get_history()
        assert history == []

    def test_history_after_changes(self, evolution_setup) -> None:
        """Test that history contains applied changes."""
        engine, _, _ = evolution_setup
        change = engine.propose_change(
            "add_node",
            {"node": {"id": "hist_test", "description": "test"}},
            "testing history",
        )
        engine.apply_change(change)
        history = engine.get_history()
        assert len(history) >= 1


class TestRollback:
    """Tests for rollback."""

    def test_rollback_add_node(self, evolution_setup) -> None:
        """Test rolling back an add_node change."""
        engine, _, graph_executor = evolution_setup
        change = engine.propose_change(
            "add_node",
            {"node": {"id": "rollback_test", "description": "test"}},
            "will rollback",
        )
        engine.apply_change(change)
        # Verify node exists
        node = graph_executor.get_node("rollback_test")
        assert node is not None

        # Rollback
        result = engine.rollback(change["id"])
        assert result is True
        with pytest.raises(KeyError):
            graph_executor.get_node("rollback_test")

    def test_rollback_nonexistent_change(self, evolution_setup) -> None:
        """Test rolling back a non-existent change ID."""
        engine, _, _ = evolution_setup
        result = engine.rollback("nonexistent-id")
        assert result is False

    def test_rollback_unapplied_change(self, evolution_setup) -> None:
        """Test rolling back a change that was never applied."""
        engine, _, _ = evolution_setup
        # Manually log a rejected change
        change = engine.propose_change("add_node", {"node": {"id": "x"}}, "test")
        change["status"] = "rejected"
        engine._log_change(change)
        result = engine.rollback(change["id"])
        assert result is False


class TestApplyReorder:
    """Tests for reorder change type."""

    def test_apply_reorder(self, evolution_setup) -> None:
        """Test applying a reorder change."""
        engine, _, graph_executor = evolution_setup
        original_ids = [n["id"] for n in graph_executor.graph["nodes"]]
        reversed_ids = list(reversed(original_ids))
        change = engine.propose_change(
            "reorder", {"order": reversed_ids}, "Reverse node order"
        )
        result = engine.apply_change(change)
        assert result is True
        new_ids = [n["id"] for n in graph_executor.graph["nodes"]]
        assert new_ids == reversed_ids

    def test_apply_add_skill_type(self, evolution_setup) -> None:
        """Test applying an add_skill change (logged only)."""
        engine, _, _ = evolution_setup
        change = engine.propose_change(
            "add_skill", {"name": "test-skill"}, "Add skill"
        )
        result = engine.apply_change(change)
        assert result is True

    def test_apply_add_rule_type(self, evolution_setup) -> None:
        """Test applying an add_rule change (logged only)."""
        engine, _, _ = evolution_setup
        change = engine.propose_change(
            "add_rule", {"name": "test-rule"}, "Add rule"
        )
        result = engine.apply_change(change)
        assert result is True

    def test_apply_change_failure(self, evolution_setup) -> None:
        """Test applying a change that fails (e.g., duplicate node)."""
        engine, _, _ = evolution_setup
        change = engine.propose_change(
            "add_node",
            {"node": {"id": "init"}},  # Already exists
            "Duplicate node",
        )
        result = engine.apply_change(change)
        assert result is False
        history = engine.get_history()
        assert history[-1]["status"] == "failed"
