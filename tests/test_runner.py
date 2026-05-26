"""Tests for runner.py - the kernel entry point."""

from pathlib import Path

import pytest
import yaml

import runner


class TestRunnerImport:
    """Tests for runner module import and structure."""

    def test_runner_importable(self) -> None:
        """Test that runner module can be imported."""
        assert runner is not None

    def test_runner_has_main(self) -> None:
        """Test that runner has a main function."""
        assert hasattr(runner, "main")
        assert callable(runner.main)

    def test_runner_has_parse_args(self) -> None:
        """Test that runner has parse_args function."""
        assert hasattr(runner, "parse_args")


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

    def test_main_dry_run_max_iterations(self) -> None:
        """Test main function respects max iterations in dry-run."""
        state = runner.main(["--goal", "test", "--max-iterations", "3", "--dry-run"])
        assert state["iteration_count"] <= 3

    def test_main_dry_run_does_not_modify_state(self, state_yaml: Path) -> None:
        """Test that dry run does not modify state.yaml."""
        original_content = state_yaml.read_text()
        runner.main(["--goal", "test goal", "--max-iterations", "2", "--dry-run"])
        assert state_yaml.read_text() == original_content

    def test_main_produces_output(self, capsys) -> None:
        """Test that dry run produces output."""
        runner.main(["--goal", "test goal", "--max-iterations", "1", "--dry-run"])
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "test goal" in captured.out

    def test_main_shows_node_info(self, capsys) -> None:
        """Test that dry run shows node information."""
        runner.main(["--goal", "test", "--max-iterations", "2", "--dry-run"])
        captured = capsys.readouterr()
        assert "Node:" in captured.out
        assert "Prompt file:" in captured.out

    def test_main_non_dry_run(self, tmp_path: Path, monkeypatch) -> None:
        """Test main function without dry-run modifies state."""
        import yaml
        import shutil

        # Set up temp kernel structure
        state_file = tmp_path / "kernel" / "state.yaml"
        state_file.parent.mkdir(parents=True)
        state_data = {
            "current_node": "init",
            "iteration_count": 0,
            "max_iterations": 30,
            "goal": "",
            "status": "idle",
            "last_updated": "",
            "errors": [],
            "context": {"skills_loaded": [], "current_task": "", "phase": "startup"},
        }
        with open(state_file, "w") as f:
            yaml.safe_dump(state_data, f)

        # Copy graph.yaml
        kernel_root = Path(__file__).parent.parent
        shutil.copy(kernel_root / "kernel" / "graph.yaml", tmp_path / "kernel" / "graph.yaml")

        # Copy prompts
        prompts_dir = tmp_path / "kernel" / "prompts"
        shutil.copytree(kernel_root / "kernel" / "prompts", prompts_dir)

        # Create memory dir
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "decisions.jsonl").touch()
        (memory_dir / "reflections.jsonl").touch()
        (memory_dir / "current_goal.md").touch()
        progress = {"iteration": 0, "tasks_total": 0, "tasks_done": 0, "status": "pending"}
        with open(memory_dir / "progress.yaml", "w") as f:
            yaml.safe_dump(progress, f)

        # Create knowledge dir
        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir()
        for sub in ["rules", "skills", "patterns"]:
            (knowledge_dir / sub).mkdir()
            with open(knowledge_dir / sub / "_index.yaml", "w") as f:
                yaml.safe_dump({"items": []}, f)

        monkeypatch.setattr(runner, "KERNEL_ROOT", tmp_path)
        state = runner.main(["--goal", "integration test", "--max-iterations", "2"])
        assert state["goal"] == "integration test"
        assert state["iteration_count"] > 0
        # Verify state was saved
        saved = yaml.safe_load(state_file.read_text())
        assert saved["goal"] == "integration test"
