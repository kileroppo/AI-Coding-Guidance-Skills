"""Reflector for analyzing iteration results and proposing evolution.

This module analyzes what worked and what failed during kernel execution,
proposes evolutionary changes, and extracts learned rules from experience.
"""

from collections import Counter
from datetime import datetime, timezone
from typing import Any


class Reflector:
    """Analyzes iteration results and proposes kernel evolution.

    The reflector examines iteration data to identify patterns of success
    and failure, then proposes changes to improve the kernel's workflow.
    """

    def __init__(self, memory_dir: str, knowledge_store: Any) -> None:
        """Initialize the reflector.

        Args:
            memory_dir: Path to the memory/ directory.
            knowledge_store: A KnowledgeStore instance.
        """
        self.memory_dir = memory_dir
        self.knowledge_store = knowledge_store

    def analyze_iteration(self, iteration_data: dict) -> dict:
        """Analyze iteration data and produce a reflection dict.

        Args:
            iteration_data: Dict with keys: node, result, duration, errors.

        Returns:
            Reflection dict with: iteration, node, success, learnings, issues, timestamp.
        """
        errors = iteration_data.get("errors", [])
        result = iteration_data.get("result", "")
        success = len(errors) == 0 and result != "failed"

        learnings = []
        issues = []

        if success:
            learnings.append(
                f"Node '{iteration_data.get('node', 'unknown')}' completed successfully"
            )
            duration = iteration_data.get("duration", 0)
            if duration and duration > 0:
                learnings.append(f"Execution took {duration}s")
        else:
            for error in errors:
                issues.append(f"Error: {error}")
            if result == "failed":
                issues.append(
                    f"Node '{iteration_data.get('node', 'unknown')}' returned failure"
                )

        return {
            "iteration": iteration_data.get("iteration", 0),
            "node": iteration_data.get("node", "unknown"),
            "success": success,
            "learnings": learnings,
            "issues": issues,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def propose_evolution(self, reflections: list) -> list:
        """Analyze recent reflections and propose changes.

        Rules:
        - If same node fails 3+ times, propose removing or modifying it.
        - If a pattern of success emerges, propose adding it as a rule.

        Args:
            reflections: List of reflection dicts.

        Returns:
            List of change proposal dicts.
        """
        proposals = []

        # Count failures per node
        failure_counts: Counter = Counter()
        success_counts: Counter = Counter()
        for reflection in reflections:
            node = reflection.get("node", "unknown")
            if not reflection.get("success", True):
                failure_counts[node] += 1
            else:
                success_counts[node] += 1

        # Propose modifications for repeatedly failing nodes
        for node, count in failure_counts.items():
            if count >= 3:
                proposals.append({
                    "type": "modify_prompt",
                    "details": {
                        "node_id": node,
                        "prompt_file": f"prompts/{node}.md",
                    },
                    "reason": f"Node '{node}' has failed {count} times - prompt may need revision",
                })

        # Propose rules for consistently successful patterns
        for node, count in success_counts.items():
            if count >= 5:
                proposals.append({
                    "type": "add_rule",
                    "details": {
                        "name": f"success_pattern_{node}",
                        "description": f"Node '{node}' succeeds consistently ({count} times)",
                        "tags": ["learned", "success-pattern"],
                    },
                    "reason": f"Node '{node}' has succeeded {count} times - pattern worth preserving",
                })

        return proposals

    def extract_rules(self, reflections: list) -> list:
        """Extract learned rules from patterns in reflections.

        Args:
            reflections: List of reflection dicts.

        Returns:
            List of rule dicts suitable for KnowledgeStore.add_rule().
        """
        rules = []

        # Group learnings by node
        node_learnings: dict[str, list[str]] = {}
        for reflection in reflections:
            node = reflection.get("node", "unknown")
            if node not in node_learnings:
                node_learnings[node] = []
            node_learnings[node].extend(reflection.get("learnings", []))

        # Extract rules from repeated learnings
        for node, learnings in node_learnings.items():
            if len(learnings) >= 3:
                rules.append({
                    "name": f"learned_from_{node}",
                    "description": f"Patterns observed from node '{node}' execution",
                    "content": "\n".join(set(learnings)),
                    "tags": ["learned", node],
                    "source": "reflector",
                })

        return rules

    def summarize_progress(self, state: dict) -> str:
        """Return human-readable progress summary.

        Args:
            state: The current state dict.

        Returns:
            Human-readable progress summary string.
        """
        goal = state.get("goal", "No goal set")
        iteration = state.get("iteration_count", 0)
        max_iter = state.get("max_iterations", 30)
        status = state.get("status", "unknown")
        current_node = state.get("current_node", "unknown")
        errors = state.get("errors", [])

        lines = [
            f"Goal: {goal}",
            f"Status: {status}",
            f"Progress: iteration {iteration}/{max_iter}",
            f"Current node: {current_node}",
        ]

        if errors:
            lines.append(f"Errors ({len(errors)}): {errors[-1]}")

        return "\n".join(lines)
