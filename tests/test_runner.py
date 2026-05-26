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


class TestParseArgsExtended:
    """Tests for new CLI arguments (--ai-command, --timeout, --resume, --generate-prompt)."""

    def test_ai_command_argument(self) -> None:
        """Test parsing --ai-command argument."""
        args = runner.parse_args(["--goal", "test", "--ai-command", "claude --print"])
        assert args.ai_command == "claude --print"

    def test_ai_command_default_none(self) -> None:
        """Test that --ai-command defaults to None."""
        args = runner.parse_args(["--goal", "test"])
        assert args.ai_command is None

    def test_timeout_argument(self) -> None:
        """Test parsing --timeout argument."""
        args = runner.parse_args(["--goal", "test", "--timeout", "60"])
        assert args.timeout == 60

    def test_timeout_default(self) -> None:
        """Test that --timeout defaults to 300."""
        args = runner.parse_args(["--goal", "test"])
        assert args.timeout == 300

    def test_resume_flag(self) -> None:
        """Test parsing --resume flag."""
        args = runner.parse_args(["--goal", "test", "--resume"])
        assert args.resume is True

    def test_resume_default(self) -> None:
        """Test that --resume defaults to False."""
        args = runner.parse_args(["--goal", "test"])
        assert args.resume is False

    def test_generate_prompt_flag(self) -> None:
        """Test parsing --generate-prompt flag."""
        args = runner.parse_args(["--goal", "test", "--generate-prompt"])
        assert args.generate_prompt is True

    def test_generate_prompt_default(self) -> None:
        """Test that --generate-prompt defaults to False."""
        args = runner.parse_args(["--goal", "test"])
        assert args.generate_prompt is False

    def test_all_new_args_together(self) -> None:
        """Test parsing all new arguments together."""
        args = runner.parse_args([
            "--goal", "test",
            "--ai-command", "claude --print",
            "--timeout", "120",
            "--resume",
            "--generate-prompt",
        ])
        assert args.ai_command == "claude --print"
        assert args.timeout == 120
        assert args.resume is True
        assert args.generate_prompt is True


class TestMode3:
    """Tests for Mode 3 (real AI execution via subprocess)."""

    @pytest.fixture
    def runner_env(self, tmp_path: Path) -> Path:
        """Set up a complete runner environment in tmp_path."""
        # kernel dir
        kernel_dir = tmp_path / "kernel"
        kernel_dir.mkdir()

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
        with open(kernel_dir / "state.yaml", "w") as f:
            yaml.safe_dump(state_data, f)

        graph_data = {
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
                    "description": "Plan tasks",
                    "transitions": [
                        {"to": "code", "condition": "plan_ready"},
                        {"to": "plan", "condition": "plan_needs_revision"},
                    ],
                    "max_retries": 2,
                },
                {
                    "id": "code",
                    "prompt_file": "prompts/coder.md",
                    "description": "Write code",
                    "transitions": [],
                    "max_retries": 3,
                },
            ],
            "default_start": "init",
            "max_iterations": 30,
        }
        with open(kernel_dir / "graph.yaml", "w") as f:
            yaml.safe_dump(graph_data, f)

        (kernel_dir / "prompts").mkdir()
        (kernel_dir / "prompts" / "orchestrator.md").write_text("Orchestrator prompt")
        (kernel_dir / "prompts" / "planner.md").write_text("Planner prompt")
        (kernel_dir / "prompts" / "coder.md").write_text("Coder prompt")

        (kernel_dir / "BOOT.md").write_text("# Boot\nBoot content.")
        (kernel_dir / "philosophy").mkdir()
        (kernel_dir / "philosophy" / "dao.md").write_text("# Dao\nDao content.")
        (kernel_dir / "philosophy" / "strategy.md").write_text("# Strategy\nStrategy content.")

        # memory dir
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "decisions.jsonl").touch()
        (memory_dir / "reflections.jsonl").touch()
        (memory_dir / "current_goal.md").touch()
        with open(memory_dir / "progress.yaml", "w") as f:
            yaml.safe_dump({"iteration": 0, "tasks_total": 0, "tasks_done": 0, "status": "pending"}, f)

        # knowledge dir
        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir()
        for sub in ["rules", "skills", "patterns"]:
            (knowledge_dir / sub).mkdir()
            with open(knowledge_dir / sub / "_index.yaml", "w") as f:
                yaml.safe_dump({"items": []}, f)

        return tmp_path

    def test_mode3_advances_with_transition(self, runner_env: Path, monkeypatch) -> None:
        """Test Mode 3 advances node based on TRANSITION line in AI output."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)

        mock_result = MagicMock()
        mock_result.stdout = "Some output\nTRANSITION: goal_loaded\nMore output"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            state = runner.main([
                "--goal", "test mode3",
                "--ai-command", "echo hello",
                "--max-iterations", "1",
            ])

        mock_run.assert_called_once()
        # After init with TRANSITION: goal_loaded, should advance to "plan"
        assert state["current_node"] == "plan"

    def test_mode3_fallback_first_transition(self, runner_env: Path, monkeypatch) -> None:
        """Test Mode 3 uses first transition when no TRANSITION line found."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)

        mock_result = MagicMock()
        mock_result.stdout = "Some output without transition info"

        with patch("subprocess.run", return_value=mock_result):
            state = runner.main([
                "--goal", "test fallback",
                "--ai-command", "echo hi",
                "--max-iterations", "1",
            ])

        # Should still advance using first available transition
        assert state["current_node"] == "plan"

    def test_mode3_unmatched_transition_falls_back(self, runner_env: Path, monkeypatch) -> None:
        """Test Mode 3 falls back to first transition when condition doesn't match."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)

        mock_result = MagicMock()
        mock_result.stdout = "TRANSITION: nonexistent_condition"

        with patch("subprocess.run", return_value=mock_result):
            state = runner.main([
                "--goal", "test unmatched",
                "--ai-command", "echo hi",
                "--max-iterations", "1",
            ])

        # Should fall back to first transition
        assert state["current_node"] == "plan"

    def test_mode3_timeout_handling(self, runner_env: Path, monkeypatch) -> None:
        """Test Mode 3 handles subprocess timeout correctly."""
        from unittest.mock import patch
        import subprocess as sp

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)

        with patch("subprocess.run", side_effect=sp.TimeoutExpired("echo", 5)):
            state = runner.main([
                "--goal", "test timeout",
                "--ai-command", "echo hi",
                "--timeout", "5",
                "--max-iterations", "2",
            ])

        # Should stay on same node and record error
        assert state["current_node"] == "init"
        assert any("Timeout" in e for e in state.get("errors", []))

    def test_mode3_command_not_found(self, runner_env: Path, monkeypatch, capsys) -> None:
        """Test Mode 3 handles missing AI command gracefully."""
        from unittest.mock import patch

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            state = runner.main([
                "--goal", "test cmd not found",
                "--ai-command", "nonexistent_command --flag",
                "--max-iterations", "3",
            ])

        assert state["status"] == "error"
        assert any("not found" in e.lower() or "Command not found" in e for e in state.get("errors", []))
        captured = capsys.readouterr()
        assert "nonexistent_command" in captured.err

    def test_mode3_completes_at_terminal_node(self, runner_env: Path, monkeypatch) -> None:
        """Test Mode 3 completes when reaching a node with no transitions."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)

        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.stdout = "TRANSITION: goal_loaded"
            elif call_count[0] == 2:
                result.stdout = "TRANSITION: plan_ready"
            else:
                result.stdout = "done"
            return result

        with patch("subprocess.run", side_effect=mock_run):
            state = runner.main([
                "--goal", "test terminal",
                "--ai-command", "echo hi",
                "--max-iterations", "10",
            ])

        # Should reach "code" node which has no transitions -> complete
        assert state["status"] == "complete"
        assert state["current_node"] == "code"

    def test_mode3_subprocess_receives_context(self, runner_env: Path, monkeypatch) -> None:
        """Test that subprocess receives assembled context as stdin."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)

        captured_input = []

        def mock_run(*args, **kwargs):
            captured_input.append(kwargs.get("input", ""))
            result = MagicMock()
            result.stdout = "TRANSITION: goal_loaded"
            return result

        with patch("subprocess.run", side_effect=mock_run):
            runner.main([
                "--goal", "context test",
                "--ai-command", "claude --print",
                "--max-iterations", "1",
            ])

        assert len(captured_input) == 1
        assert "=== BOOT SEQUENCE ===" in captured_input[0]
        assert "=== CURRENT STATE ===" in captured_input[0]
        assert "=== NODE PROMPT (init) ===" in captured_input[0]

    def test_mode3_no_ai_command_falls_back_to_scaffolding(self, runner_env: Path, monkeypatch) -> None:
        """Test that no --ai-command and no --dry-run falls back to Mode 1 scaffolding."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)
        state = runner.main(["--goal", "test fallback mode", "--max-iterations", "1"])
        # Should still advance state (Mode 1 scaffolding behavior)
        assert state["iteration_count"] > 0


class TestGeneratePrompt:
    """Tests for --generate-prompt flag."""

    @pytest.fixture
    def runner_env(self, tmp_path: Path) -> Path:
        """Set up a complete runner environment in tmp_path."""
        kernel_dir = tmp_path / "kernel"
        kernel_dir.mkdir()

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
        with open(kernel_dir / "state.yaml", "w") as f:
            yaml.safe_dump(state_data, f)

        graph_data = {
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
                    "transitions": [],
                    "max_retries": 1,
                },
            ],
            "default_start": "init",
            "max_iterations": 30,
        }
        with open(kernel_dir / "graph.yaml", "w") as f:
            yaml.safe_dump(graph_data, f)

        (kernel_dir / "prompts").mkdir()
        (kernel_dir / "prompts" / "orchestrator.md").write_text("Orchestrator prompt text.")
        (kernel_dir / "BOOT.md").write_text("# Boot\nBoot sequence content.")
        (kernel_dir / "philosophy").mkdir()
        (kernel_dir / "philosophy" / "dao.md").write_text("# Dao\nSimplicity.")
        (kernel_dir / "philosophy" / "strategy.md").write_text("# Strategy\nPlan.")

        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "decisions.jsonl").touch()
        (memory_dir / "reflections.jsonl").touch()
        (memory_dir / "current_goal.md").touch()
        with open(memory_dir / "progress.yaml", "w") as f:
            yaml.safe_dump({"iteration": 0, "tasks_total": 0, "tasks_done": 0, "status": "pending"}, f)

        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir()
        for sub in ["rules", "skills", "patterns"]:
            (knowledge_dir / sub).mkdir()
            with open(knowledge_dir / sub / "_index.yaml", "w") as f:
                yaml.safe_dump({"items": []}, f)

        return tmp_path

    def test_generate_prompt_outputs_context(self, runner_env: Path, monkeypatch, capsys) -> None:
        """Test --generate-prompt outputs assembled context to stdout."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)
        state = runner.main(["--goal", "test prompt", "--generate-prompt"])
        captured = capsys.readouterr()
        assert "=== BOOT SEQUENCE ===" in captured.out
        assert "=== CURRENT STATE ===" in captured.out
        assert "=== NODE PROMPT (init) ===" in captured.out
        assert "=== PHILOSOPHY: DAO ===" in captured.out
        assert "=== PHILOSOPHY: STRATEGY ===" in captured.out

    def test_generate_prompt_exits_without_running_loop(self, runner_env: Path, monkeypatch) -> None:
        """Test --generate-prompt does not run the main loop."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)
        state = runner.main(["--goal", "test prompt", "--generate-prompt"])
        # Iteration count should not have advanced
        assert state["iteration_count"] == 0

    def test_generate_prompt_with_invalid_node(self, runner_env: Path, monkeypatch, capsys) -> None:
        """Test --generate-prompt with invalid current node shows error."""
        # Set state to reference a non-existent node
        state_file = runner_env / "kernel" / "state.yaml"
        state_data = {
            "current_node": "nonexistent",
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

        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)
        state = runner.main(["--goal", "test", "--generate-prompt"])
        assert state["status"] == "error"
        captured = capsys.readouterr()
        assert "nonexistent" in captured.err


class TestResume:
    """Tests for --resume flag."""

    @pytest.fixture
    def runner_env(self, tmp_path: Path) -> Path:
        """Set up a runner environment with existing goal in state."""
        kernel_dir = tmp_path / "kernel"
        kernel_dir.mkdir()

        state_data = {
            "current_node": "plan",
            "iteration_count": 3,
            "max_iterations": 30,
            "goal": "existing goal from previous run",
            "status": "running",
            "last_updated": "",
            "errors": [],
            "context": {"skills_loaded": [], "current_task": "", "phase": "coding"},
        }
        with open(kernel_dir / "state.yaml", "w") as f:
            yaml.safe_dump(state_data, f)

        graph_data = {
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
                    "transitions": [],
                    "max_retries": 3,
                },
            ],
            "default_start": "init",
            "max_iterations": 30,
        }
        with open(kernel_dir / "graph.yaml", "w") as f:
            yaml.safe_dump(graph_data, f)

        (kernel_dir / "prompts").mkdir()
        (kernel_dir / "prompts" / "orchestrator.md").write_text("Orchestrator")
        (kernel_dir / "prompts" / "planner.md").write_text("Planner")
        (kernel_dir / "prompts" / "coder.md").write_text("Coder")
        (kernel_dir / "BOOT.md").write_text("# Boot")
        (kernel_dir / "philosophy").mkdir()
        (kernel_dir / "philosophy" / "dao.md").write_text("# Dao")
        (kernel_dir / "philosophy" / "strategy.md").write_text("# Strategy")

        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "decisions.jsonl").touch()
        (memory_dir / "reflections.jsonl").touch()
        (memory_dir / "current_goal.md").write_text("# Current Goal\n\nexisting goal from previous run\n")
        with open(memory_dir / "progress.yaml", "w") as f:
            yaml.safe_dump({"iteration": 3, "tasks_total": 0, "tasks_done": 0, "status": "in_progress"}, f)

        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir()
        for sub in ["rules", "skills", "patterns"]:
            (knowledge_dir / sub).mkdir()
            with open(knowledge_dir / sub / "_index.yaml", "w") as f:
                yaml.safe_dump({"items": []}, f)

        return tmp_path

    def test_resume_preserves_existing_goal(self, runner_env: Path, monkeypatch) -> None:
        """Test --resume does not overwrite existing goal."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)
        state = runner.main([
            "--goal", "new goal that should be ignored",
            "--resume",
            "--dry-run",
            "--max-iterations", "1",
        ])
        assert state["goal"] == "existing goal from previous run"

    def test_no_resume_overwrites_goal(self, runner_env: Path, monkeypatch) -> None:
        """Test without --resume, goal is overwritten."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", runner_env)
        state = runner.main([
            "--goal", "new goal",
            "--dry-run",
            "--max-iterations", "1",
        ])
        assert state["goal"] == "new goal"


class TestParseTransition:
    """Tests for the _parse_transition helper function."""

    def test_parse_transition_found(self) -> None:
        """Test parsing a TRANSITION line from output."""
        output = "Some AI output\nTRANSITION: plan_ready\nMore output"
        assert runner._parse_transition(output) == "plan_ready"

    def test_parse_transition_not_found(self) -> None:
        """Test parsing output with no TRANSITION line."""
        output = "Just regular output without transition info"
        assert runner._parse_transition(output) is None

    def test_parse_transition_with_whitespace(self) -> None:
        """Test parsing TRANSITION line with extra whitespace."""
        output = "  TRANSITION:  goal_loaded  \n"
        assert runner._parse_transition(output) == "goal_loaded"

    def test_parse_transition_first_match(self) -> None:
        """Test that first TRANSITION line is used if multiple exist."""
        output = "TRANSITION: first\nTRANSITION: second"
        assert runner._parse_transition(output) == "first"

    def test_parse_transition_empty_output(self) -> None:
        """Test parsing empty output."""
        assert runner._parse_transition("") is None


class TestStuckDetection:
    """Tests for stuck detection in the runner."""

    @pytest.fixture
    def stuck_env(self, tmp_path: Path) -> Path:
        """Set up an environment where a node will get stuck (cycling graph)."""
        kernel_dir = tmp_path / "kernel"
        kernel_dir.mkdir()

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
        with open(kernel_dir / "state.yaml", "w") as f:
            yaml.safe_dump(state_data, f)

        # Graph where code cycles back to itself with max_retries=2
        graph_data = {
            "nodes": [
                {
                    "id": "init",
                    "prompt_file": "prompts/orchestrator.md",
                    "description": "Initialize",
                    "transitions": [{"to": "code", "condition": "goal_loaded"}],
                    "max_retries": 1,
                },
                {
                    "id": "code",
                    "prompt_file": "prompts/coder.md",
                    "description": "Write code",
                    "transitions": [{"to": "code", "condition": "code_needs_retry"}],
                    "max_retries": 2,
                },
            ],
            "default_start": "init",
            "max_iterations": 30,
        }
        with open(kernel_dir / "graph.yaml", "w") as f:
            yaml.safe_dump(graph_data, f)

        (kernel_dir / "prompts").mkdir()
        (kernel_dir / "prompts" / "orchestrator.md").write_text("Orchestrator prompt")
        (kernel_dir / "prompts" / "coder.md").write_text("Coder prompt")
        (kernel_dir / "BOOT.md").write_text("# Boot")
        (kernel_dir / "philosophy").mkdir()
        (kernel_dir / "philosophy" / "dao.md").write_text("# Dao")
        (kernel_dir / "philosophy" / "strategy.md").write_text("# Strategy")

        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "decisions.jsonl").touch()
        (memory_dir / "reflections.jsonl").touch()
        (memory_dir / "current_goal.md").touch()
        with open(memory_dir / "progress.yaml", "w") as f:
            yaml.safe_dump({"iteration": 0, "tasks_total": 0, "tasks_done": 0, "status": "pending"}, f)

        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir()
        for sub in ["rules", "skills", "patterns"]:
            (knowledge_dir / sub).mkdir()
            with open(knowledge_dir / sub / "_index.yaml", "w") as f:
                yaml.safe_dump({"items": []}, f)

        return tmp_path

    @pytest.fixture
    def stuck_handler_env(self, tmp_path: Path) -> Path:
        """Set up an environment with stuck_handler on the cycling node."""
        kernel_dir = tmp_path / "kernel"
        kernel_dir.mkdir()

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
        with open(kernel_dir / "state.yaml", "w") as f:
            yaml.safe_dump(state_data, f)

        # Graph where code cycles back to itself with max_retries=2 and stuck_handler
        graph_data = {
            "nodes": [
                {
                    "id": "init",
                    "prompt_file": "prompts/orchestrator.md",
                    "description": "Initialize",
                    "transitions": [{"to": "code", "condition": "goal_loaded"}],
                    "max_retries": 1,
                },
                {
                    "id": "code",
                    "prompt_file": "prompts/coder.md",
                    "description": "Write code",
                    "transitions": [{"to": "code", "condition": "code_needs_retry"}],
                    "max_retries": 2,
                    "stuck_handler": "reflect",
                },
                {
                    "id": "reflect",
                    "prompt_file": "prompts/orchestrator.md",
                    "description": "Reflect on progress",
                    "transitions": [],
                    "max_retries": 1,
                },
            ],
            "default_start": "init",
            "max_iterations": 30,
        }
        with open(kernel_dir / "graph.yaml", "w") as f:
            yaml.safe_dump(graph_data, f)

        (kernel_dir / "prompts").mkdir()
        (kernel_dir / "prompts" / "orchestrator.md").write_text("Orchestrator prompt")
        (kernel_dir / "prompts" / "coder.md").write_text("Coder prompt")
        (kernel_dir / "BOOT.md").write_text("# Boot")
        (kernel_dir / "philosophy").mkdir()
        (kernel_dir / "philosophy" / "dao.md").write_text("# Dao")
        (kernel_dir / "philosophy" / "strategy.md").write_text("# Strategy")

        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "decisions.jsonl").touch()
        (memory_dir / "reflections.jsonl").touch()
        (memory_dir / "current_goal.md").touch()
        with open(memory_dir / "progress.yaml", "w") as f:
            yaml.safe_dump({"iteration": 0, "tasks_total": 0, "tasks_done": 0, "status": "pending"}, f)

        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir()
        for sub in ["rules", "skills", "patterns"]:
            (knowledge_dir / sub).mkdir()
            with open(knowledge_dir / sub / "_index.yaml", "w") as f:
                yaml.safe_dump({"items": []}, f)

        return tmp_path

    def test_runner_detects_stuck_and_stops(self, stuck_env: Path, monkeypatch) -> None:
        """Test runner stops with 'stuck' status when max_retries exceeded."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", stuck_env)
        state = runner.main([
            "--goal", "test stuck detection",
            "--max-iterations", "20",
        ])
        assert state["status"] == "stuck"
        assert any("exceeded max_retries" in e for e in state.get("errors", []))

    def test_runner_stuck_handler_redirect(self, stuck_handler_env: Path, monkeypatch) -> None:
        """Test runner redirects to stuck_handler node when max_retries exceeded."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", stuck_handler_env)
        state = runner.main([
            "--goal", "test stuck handler",
            "--max-iterations", "20",
        ])
        # Should redirect to reflect and then complete (reflect has no transitions)
        assert state["current_node"] == "reflect"
        assert state["status"] == "complete"

    def test_runner_stuck_in_dry_run(self, stuck_env: Path, monkeypatch, capsys) -> None:
        """Test dry-run prints stuck message when max_retries exceeded."""
        monkeypatch.setattr(runner, "KERNEL_ROOT", stuck_env)
        state = runner.main([
            "--goal", "test stuck dry run",
            "--max-iterations", "20",
            "--dry-run",
        ])
        captured = capsys.readouterr()
        assert "STUCK" in captured.out
        assert "exceeded max_retries" in captured.out
        assert state["status"] == "stuck"
