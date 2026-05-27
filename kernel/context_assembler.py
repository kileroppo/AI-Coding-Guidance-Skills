"""Context assembler for Mode 3 AI execution.

This module assembles a full context prompt from kernel components,
suitable for piping to an AI CLI tool via subprocess.
"""

from pathlib import Path
from typing import Any


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

        # 3. Current node's prompt file
        prompt_file = graph_executor.get_prompt_for_node(node["id"])
        if prompt_file:
            prompt_path = self.kernel_root / "kernel" / prompt_file
            prompt_content = self._read_file(prompt_path)
        else:
            prompt_content = "(no prompt file configured for this node)"
        sections.append(f"=== NODE PROMPT ({node['id']}) ===\n\n{prompt_content}")

        # 4. Philosophy - dao.md
        dao_path = self.kernel_root / "kernel" / "philosophy" / "dao.md"
        dao_content = self._read_file(dao_path)
        sections.append(f"=== PHILOSOPHY: DAO ===\n\n{dao_content}")

        # 5. Philosophy - strategy.md
        strategy_path = self.kernel_root / "kernel" / "philosophy" / "strategy.md"
        strategy_content = self._read_file(strategy_path)
        sections.append(f"=== PHILOSOPHY: STRATEGY ===\n\n{strategy_content}")

        # 6. Skills loaded in state
        skills_loaded = state.get("context", {}).get("skills_loaded", [])
        if skills_loaded:
            skills_section = self._load_skills(skills_loaded, knowledge_store)
            sections.append(f"=== LOADED SKILLS ===\n\n{skills_section}")

        # 7. Output format contract
        contract_path = self.kernel_root / "kernel" / "contracts" / "output_format.md"
        contract_content = self._read_file(contract_path)
        if not contract_content.startswith("(file not found"):
            sections.append(
                f"=== OUTPUT FORMAT CONTRACT ===\n\n{contract_content}"
            )

        return "\n\n".join(sections)

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
        """Load skill content for all listed skills.

        Args:
            skill_names: List of skill names to load.
            knowledge_store: KnowledgeStore instance.

        Returns:
            Combined skill descriptions.
        """
        parts = []
        for name in skill_names:
            try:
                skill = knowledge_store.get_skill(name)
                parts.append(f"- {name}: {skill.get('description', '(no description)')}")
            except KeyError:
                parts.append(f"- {name}: (skill not found)")
        return "\n".join(parts)
