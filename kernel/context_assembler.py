"""Context assembler for Mode 3 AI execution.

This module assembles a full context prompt from kernel components,
suitable for piping to an AI CLI tool via subprocess.
"""

from pathlib import Path
from typing import Any

import yaml


class ContextAssembler:
    """Assembles full context prompt from kernel components."""

    def __init__(self, kernel_root: Path):
        """Initialize the context assembler.

        Args:
            kernel_root: Path to the project root directory.
        """
        self.kernel_root = kernel_root

    def assemble(self, state: dict, node: dict, graph_executor: Any,
                 knowledge_store: Any) -> str:
        """Assemble full context from BOOT.md + state + node prompt + philosophy + skills.

        Returns a single formatted string suitable for piping to an AI.

        Args:
            state: Current state dict from StateManager.
            node: Current node dict from GraphExecutor.
            graph_executor: GraphExecutor instance for prompt path resolution.
            knowledge_store: KnowledgeStore instance for skill loading.

        Returns:
            A single formatted string with all context sections.
        """
        sections = []

        # 1. BOOT.md
        boot_path = self.kernel_root / "kernel" / "BOOT.md"
        boot_content = self._read_file(boot_path)
        sections.append(f"=== BOOT SEQUENCE ===\n\n{boot_content}")

        # 2. Constitution
        const_path = self.kernel_root / "kernel" / "constitution.md"
        const_content = self._read_file(const_path)
        if const_content and not const_content.startswith("(file not found"):
            sections.append(f"=== CONSTITUTION (IMMUTABLE) ===\n\n{const_content}")

        # 3. Current state summary
        state_summary = self._format_state(state)
        sections.append(f"=== CURRENT STATE ===\n\n{state_summary}")

        # 4. Current task from tasks.yaml
        current_task = self._load_current_task()
        if current_task:
            sections.append(f"=== CURRENT TASK ===\n\n{current_task}")

        # 5. Current node's prompt file
        prompt_file = graph_executor.get_prompt_for_node(node["id"])
        if prompt_file:
            prompt_path = self.kernel_root / "kernel" / prompt_file
            prompt_content = self._read_file(prompt_path)
        else:
            prompt_content = "(no prompt file configured for this node)"
        sections.append(f"=== NODE PROMPT ({node['id']}) ===\n\n{prompt_content}")

        # 6. Philosophy - dao.md
        dao_path = self.kernel_root / "kernel" / "philosophy" / "dao.md"
        dao_content = self._read_file(dao_path)
        sections.append(f"=== PHILOSOPHY: DAO ===\n\n{dao_content}")

        # 7. Philosophy - strategy.md
        strategy_path = self.kernel_root / "kernel" / "philosophy" / "strategy.md"
        strategy_content = self._read_file(strategy_path)
        sections.append(f"=== PHILOSOPHY: STRATEGY ===\n\n{strategy_content}")

        # 8. Skills loaded in state
        skills_loaded = state.get("context", {}).get("skills_loaded", [])
        if skills_loaded:
            skills_section = self._load_skills(skills_loaded, knowledge_store)
            sections.append(f"=== LOADED SKILLS ===\n\n{skills_section}")

        # 9. Output format contract
        contract_path = self.kernel_root / "kernel" / "contracts" / "output_format.md"
        contract_content = self._read_file(contract_path)
        if not contract_content.startswith("(file not found"):
            sections.append(
                f"=== OUTPUT FORMAT CONTRACT ===\n\n{contract_content}"
            )

        # 10. Evolution history
        evolution_history = self._load_evolution_history(count=5)
        if evolution_history:
            sections.append(
                f"=== EVOLUTION HISTORY ===\n\n{evolution_history}"
            )

        # 11. Recent reflections
        recent_reflections = self._load_recent_reflections(count=3)
        if recent_reflections:
            sections.append(
                f"=== RECENT REFLECTIONS ===\n\n{recent_reflections}"
            )

        return "\n\n".join(sections)

    def _load_current_task(self) -> str:
        """Load the current task from memory/tasks.yaml.

        Uses TaskManager for consistent task selection logic. Finds the
        in_progress task first, or the first eligible pending task
        (whose dependencies are all done).

        Returns:
            Formatted task string, or empty string if no task is available.
        """
        from kernel.task_manager import TaskManager

        memory_dir = str(self.kernel_root / "memory")
        task_mgr = TaskManager(memory_dir)
        tasks = task_mgr.load_tasks()
        if not tasks:
            return ""

        # First check for in_progress task
        current = None
        for task in tasks:
            if task.get("status") == "in_progress":
                current = task
                break

        # If none in progress, get next eligible pending
        if current is None:
            current = task_mgr.get_next_task()

        if current is None:
            return ""

        lines = []
        lines.append(f"ID: {current['id']}")
        lines.append(f"Title: {current.get('title', '(no title)')}")
        lines.append(f"Status: {current.get('status', 'pending')}")
        lines.append(f"Description: {current.get('description', '(no description)')}")
        criteria = current.get("acceptance_criteria", [])
        if criteria:
            lines.append("Acceptance Criteria:")
            for criterion in criteria:
                lines.append(f"  - {criterion}")
        deps = current.get("dependencies", [])
        if deps:
            lines.append(f"Dependencies: {', '.join(deps)}")
        lines.append(f"Complexity: {current.get('complexity', 'medium')}")
        return "\n".join(lines)

    def _read_file(self, path: Path) -> str:
        """Read a file, returning placeholder if not found.

        Args:
            path: Path to the file.

        Returns:
            File content or a not-found message.
        """
        if path.exists():
            return path.read_text(encoding="utf-8")
        return f"(file not found: {path.name})"

    def _format_state(self, state: dict) -> str:
        """Format state dict as a readable summary.

        Args:
            state: The state dictionary.

        Returns:
            Formatted string representation of state.
        """
        lines = []
        lines.append(f"Goal: {state.get('goal', '(none)')}")
        lines.append(f"Current Node: {state.get('current_node', 'unknown')}")
        lines.append(f"Iteration: {state.get('iteration_count', 0)}")
        lines.append(f"Max Iterations: {state.get('max_iterations', 30)}")
        lines.append(f"Status: {state.get('status', 'unknown')}")
        workspace_path = state.get("workspace_path", "")
        if workspace_path:
            lines.append(f"Workspace: {workspace_path}")
        errors = state.get("errors", [])
        if errors:
            lines.append(f"Errors: {errors}")
        context = state.get("context", {})
        if context.get("current_task"):
            lines.append(f"Current Task: {context['current_task']}")
        if context.get("phase"):
            lines.append(f"Phase: {context['phase']}")
        return "\n".join(lines)

    def _load_skills(self, skill_names: list, knowledge_store: Any) -> str:
        """Load skill content for all listed skills using SkillComposer.

        Attempts to load actual SKILL.md content via SkillComposer. Falls back
        to descriptions if compose fails.

        Args:
            skill_names: List of skill names to load.
            knowledge_store: KnowledgeStore instance.

        Returns:
            Combined skill content or descriptions.
        """
        from knowledge.skill_composer import SkillComposer

        composer = SkillComposer(knowledge_store)
        try:
            return composer.compose(skill_names, max_tokens=4000)
        except (ValueError, FileNotFoundError):
            # Fallback to descriptions if compose fails
            parts = []
            for name in skill_names:
                try:
                    skill = knowledge_store.get_skill(name)
                    parts.append(f"- {name}: {skill.get('description', '(no description)')}")
                except KeyError:
                    parts.append(f"- {name}: (skill not found)")
            return "\n".join(parts)

    def _load_evolution_history(self, count: int = 5) -> str:
        """Load the last N entries from evolution/history.jsonl.

        Args:
            count: Number of recent history entries to load.

        Returns:
            Formatted string of recent evolution history, or empty string.
        """
        import json

        history_path = self.kernel_root / "kernel" / "evolution" / "history.jsonl"
        if not history_path.exists():
            return ""

        records: list[dict] = []
        with open(history_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        recent = records[-count:]
        if not recent:
            return ""

        lines = []
        for entry in recent:
            status = entry.get("status", "unknown")
            change_type = entry.get("type", "unknown")
            reason = entry.get("reason", "")
            timestamp = entry.get("timestamp", "")
            lines.append(f"- [{status}] {change_type}: {reason} ({timestamp})")
        return "\n".join(lines)

    def _load_recent_reflections(self, count: int = 3) -> str:
        """Load the last N reflections from memory/reflections.jsonl.

        Args:
            count: Number of recent reflections to load.

        Returns:
            Formatted string of recent reflections, or empty string.
        """
        import json

        reflections_path = self.kernel_root / "memory" / "reflections.jsonl"
        if not reflections_path.exists():
            return ""

        records: list[dict] = []
        with open(reflections_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        recent = records[-count:]
        if not recent:
            return ""

        lines = []
        for entry in recent:
            node = entry.get("node", "unknown")
            success = entry.get("success", False)
            learnings = entry.get("learnings", [])
            issues = entry.get("issues", [])
            result_str = "success" if success else "failure"
            lines.append(f"- Node '{node}' ({result_str})")
            for learning in learnings:
                lines.append(f"  Learning: {learning}")
            for issue in issues:
                lines.append(f"  Issue: {issue}")
        return "\n".join(lines)
