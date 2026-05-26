"""Tests for the kernel package structure and configuration files."""

from pathlib import Path

import pytest
import yaml


class TestKernelStructure:
    """Tests for kernel directory structure."""

    def test_kernel_package_importable(self) -> None:
        """Test that kernel package can be imported."""
        import kernel
        assert kernel is not None

    def test_evolution_package_importable(self) -> None:
        """Test that kernel.evolution package can be imported."""
        from kernel.evolution import engine
        assert engine is not None

    def test_evolution_engine_class_exists(self) -> None:
        """Test that EvolutionEngine class exists."""
        from kernel.evolution.engine import EvolutionEngine
        assert EvolutionEngine is not None

    def test_evolution_engine_instantiation(self, kernel_root: Path) -> None:
        """Test that EvolutionEngine can be instantiated."""
        from kernel.evolution.engine import EvolutionEngine
        eng = EvolutionEngine(kernel_root)
        assert eng.kernel_root == kernel_root

    def test_immutable_files_defined(self) -> None:
        """Test that IMMUTABLE_FILES is defined correctly."""
        from kernel.evolution.engine import IMMUTABLE_FILES
        assert "kernel/BOOT.md" in IMMUTABLE_FILES
        assert "kernel/constitution.md" in IMMUTABLE_FILES
        assert "runner.py" in IMMUTABLE_FILES


class TestGraphYaml:
    """Tests for graph.yaml validity."""

    def test_graph_has_nodes(self, graph_yaml: Path) -> None:
        """Test that graph.yaml has a nodes list."""
        data = yaml.safe_load(graph_yaml.read_text())
        assert "nodes" in data
        assert isinstance(data["nodes"], list)
        assert len(data["nodes"]) > 0

    def test_graph_nodes_have_required_fields(self, graph_yaml: Path) -> None:
        """Test that all nodes have required fields."""
        data = yaml.safe_load(graph_yaml.read_text())
        for node in data["nodes"]:
            assert "id" in node, f"Node missing 'id': {node}"
            assert "prompt_file" in node, f"Node {node['id']} missing 'prompt_file'"
            assert "description" in node, f"Node {node['id']} missing 'description'"
            assert "transitions" in node, f"Node {node['id']} missing 'transitions'"
            assert "max_retries" in node, f"Node {node['id']} missing 'max_retries'"

    def test_graph_transitions_reference_valid_nodes(self, graph_yaml: Path) -> None:
        """Test that all transitions reference existing node IDs."""
        data = yaml.safe_load(graph_yaml.read_text())
        node_ids = {node["id"] for node in data["nodes"]}
        for node in data["nodes"]:
            for transition in node["transitions"]:
                assert transition["to"] in node_ids, (
                    f"Node '{node['id']}' has transition to unknown node '{transition['to']}'"
                )

    def test_graph_has_default_start(self, graph_yaml: Path) -> None:
        """Test that graph.yaml has a default_start field."""
        data = yaml.safe_load(graph_yaml.read_text())
        assert "default_start" in data
        node_ids = {node["id"] for node in data["nodes"]}
        assert data["default_start"] in node_ids

    def test_graph_has_max_iterations(self, graph_yaml: Path) -> None:
        """Test that graph.yaml has a max_iterations field."""
        data = yaml.safe_load(graph_yaml.read_text())
        assert "max_iterations" in data
        assert isinstance(data["max_iterations"], int)

    def test_graph_prompt_files_exist(self, kernel_root: Path, graph_yaml: Path) -> None:
        """Test that all prompt files referenced in graph.yaml exist."""
        data = yaml.safe_load(graph_yaml.read_text())
        for node in data["nodes"]:
            prompt_path = kernel_root / "kernel" / node["prompt_file"]
            assert prompt_path.exists(), f"Prompt file missing: {node['prompt_file']}"


class TestStateYaml:
    """Tests for state.yaml validity."""

    def test_state_has_current_node(self, state_yaml: Path) -> None:
        """Test that state.yaml has current_node."""
        data = yaml.safe_load(state_yaml.read_text())
        assert "current_node" in data

    def test_state_has_iteration_count(self, state_yaml: Path) -> None:
        """Test that state.yaml has iteration_count."""
        data = yaml.safe_load(state_yaml.read_text())
        assert "iteration_count" in data
        assert isinstance(data["iteration_count"], int)

    def test_state_has_status(self, state_yaml: Path) -> None:
        """Test that state.yaml has status."""
        data = yaml.safe_load(state_yaml.read_text())
        assert "status" in data
        assert data["status"] in ("idle", "running", "paused", "complete", "error")

    def test_state_initial_values(self, state_yaml: Path) -> None:
        """Test that state.yaml has correct initial values."""
        data = yaml.safe_load(state_yaml.read_text())
        assert data["current_node"] == "init"
        assert data["iteration_count"] == 0
        assert data["status"] == "idle"


class TestKernelFiles:
    """Tests for kernel file existence."""

    def test_boot_md_exists(self, kernel_root: Path) -> None:
        """Test that BOOT.md exists."""
        assert (kernel_root / "kernel" / "BOOT.md").exists()

    def test_constitution_md_exists(self, kernel_root: Path) -> None:
        """Test that constitution.md exists."""
        assert (kernel_root / "kernel" / "constitution.md").exists()

    def test_dao_md_exists(self, kernel_root: Path) -> None:
        """Test that philosophy/dao.md exists."""
        assert (kernel_root / "kernel" / "philosophy" / "dao.md").exists()

    def test_strategy_md_exists(self, kernel_root: Path) -> None:
        """Test that philosophy/strategy.md exists."""
        assert (kernel_root / "kernel" / "philosophy" / "strategy.md").exists()

    def test_all_prompt_files_exist(self, kernel_root: Path) -> None:
        """Test that all prompt files exist."""
        prompts = ["orchestrator.md", "planner.md", "coder.md", "tester.md", "reviewer.md", "reflector.md"]
        for prompt in prompts:
            path = kernel_root / "kernel" / "prompts" / prompt
            assert path.exists(), f"Missing prompt: {prompt}"
