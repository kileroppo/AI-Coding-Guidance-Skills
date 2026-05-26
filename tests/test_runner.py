"""Tests for runner.py - the kernel entry point."""

from pathlib import Path

import pytest
import yaml

import runner


class TestLoadYaml:
    """Tests for the load_yaml function."""

    def test_load_state_yaml(self, state_yaml: Path) -> None:
        """Test loading the state.yaml file."""
        data = runner.load_yaml(state_yaml)
        assert "current_node" in data
        assert "iteration_count" in data
        assert "status" in data

    def test_load_graph_yaml(self, graph_yaml: Path) -> None:
        """Test loading the graph.yaml file."""
        data = runner.load_yaml(graph_yaml)
        assert "nodes" in data
        assert "default_start" in data
        assert "max_iterations" in data

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            runner.load_yaml(tmp_path / "nonexistent.yaml")


class TestSaveYaml:
    """Tests for the save_yaml function."""

    def test_save_and_reload(self, tmp_path: Path) -> None:
        """Test saving and reloading a YAML file."""
        filepath = tmp_path / "test.yaml"
        data = {"key": "value", "number": 42}
        runner.save_yaml(filepath, data)
        loaded = runner.load_yaml(filepath)
        assert loaded == data


class TestGetNode:
    """Tests for the get_node function."""

    def test_find_existing_node(self, graph_yaml: Path) -> None:
        """Test finding an existing node in the graph."""
        graph = runner.load_yaml(graph_yaml)
        node = runner.get_node(graph, "init")
        assert node is not None
        assert node["id"] == "init"

    def test_find_nonexistent_node(self, graph_yaml: Path) -> None:
        """Test that a nonexistent node returns None."""
        graph = runner.load_yaml(graph_yaml)
        node = runner.get_node(graph, "nonexistent")
        assert node is None

    def test_all_graph_nodes_exist(self, graph_yaml: Path) -> None:
        """Test that all expected nodes exist in the graph."""
        graph = runner.load_yaml(graph_yaml)
        expected_nodes = ["init", "plan", "code", "test", "review", "reflect", "evolve"]
        for node_id in expected_nodes:
            node = runner.get_node(graph, node_id)
            assert node is not None, f"Node '{node_id}' not found in graph"


class TestLoadPrompt:
    """Tests for the load_prompt function."""

    def test_load_orchestrator_prompt(self, graph_yaml: Path) -> None:
        """Test loading the orchestrator prompt."""
        graph = runner.load_yaml(graph_yaml)
        node = runner.get_node(graph, "init")
        prompt = runner.load_prompt(node)
        assert "Orchestrator" in prompt
        assert len(prompt) > 0


class TestGetNextNode:
    """Tests for the get_next_node function."""

    def test_node_with_transitions(self, graph_yaml: Path) -> None:
        """Test getting next node when transitions exist."""
        graph = runner.load_yaml(graph_yaml)
        node = runner.get_node(graph, "init")
        next_id = runner.get_next_node(node)
        assert next_id == "plan"

    def test_node_without_transitions(self) -> None:
        """Test getting next node when no transitions exist."""
        node = {"id": "terminal", "transitions": []}
        next_id = runner.get_next_node(node)
        assert next_id is None


class TestCheckStopConditions:
    """Tests for the check_stop_conditions function."""

    def test_complete_status_stops(self) -> None:
        """Test that 'complete' status triggers stop."""
        state = {"status": "complete", "iteration_count": 5, "max_iterations": 30}
        assert runner.check_stop_conditions(state) is True

    def test_max_iterations_stops(self) -> None:
        """Test that reaching max iterations triggers stop."""
        state = {"status": "running", "iteration_count": 30, "max_iterations": 30}
        assert runner.check_stop_conditions(state) is True

    def test_running_below_max_continues(self) -> None:
        """Test that running below max iterations does not stop."""
        state = {"status": "running", "iteration_count": 5, "max_iterations": 30}
        assert runner.check_stop_conditions(state) is False


class TestRunLoop:
    """Tests for the run_loop function."""

    def test_dry_run_does_not_modify_state(self, state_yaml: Path) -> None:
        """Test that dry run does not modify state.yaml."""
        original_content = state_yaml.read_text()
        runner.run_loop(goal="test goal", max_iterations=3, dry_run=True)
        assert state_yaml.read_text() == original_content

    def test_dry_run_returns_state(self) -> None:
        """Test that dry run returns a valid state dict."""
        state = runner.run_loop(goal="test goal", max_iterations=3, dry_run=True)
        assert state["goal"] == "test goal"
        assert state["max_iterations"] == 3
        assert state["status"] == "complete"

    def test_run_loop_respects_max_iterations(self) -> None:
        """Test that the loop respects the max iterations limit."""
        state = runner.run_loop(goal="test", max_iterations=5, dry_run=True)
        assert state["iteration_count"] <= 5


class TestParseArgs:
    """Tests for the parse_args function."""

    def test_required_goal(self) -> None:
        """Test that --goal is required."""
        with pytest.raises(SystemExit):
            runner.parse_args([])

    def test_goal_argument(self) -> None:
        """Test parsing the --goal argument."""
        args = runner.parse_args(["--goal", "Build an API"])
        assert args.goal == "Build an API"

    def test_max_iterations_default(self) -> None:
        """Test that --max-iterations defaults to 30."""
        args = runner.parse_args(["--goal", "test"])
        assert args.max_iterations == 30

    def test_max_iterations_custom(self) -> None:
        """Test parsing custom --max-iterations."""
        args = runner.parse_args(["--goal", "test", "--max-iterations", "10"])
        assert args.max_iterations == 10

    def test_dry_run_flag(self) -> None:
        """Test parsing the --dry-run flag."""
        args = runner.parse_args(["--goal", "test", "--dry-run"])
        assert args.dry_run is True

    def test_no_dry_run_default(self) -> None:
        """Test that --dry-run defaults to False."""
        args = runner.parse_args(["--goal", "test"])
        assert args.dry_run is False


class TestMain:
    """Tests for the main function."""

    def test_main_dry_run(self) -> None:
        """Test main function with dry-run."""
        state = runner.main(["--goal", "test goal", "--dry-run"])
        assert state["goal"] == "test goal"
        assert state["status"] == "complete"
