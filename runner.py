"""Self-evolving AI development kernel runner.

This is the main entry point for the kernel. It orchestrates the execution loop
by reading state, determining the current node, loading the appropriate prompt,
and advancing through the workflow graph.

Usage:
    python3.12 runner.py --goal "Build a REST API" --max-iterations 30 --dry-run
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


KERNEL_ROOT = Path(__file__).parent


def load_yaml(filepath: Path) -> dict[str, Any]:
    """Load and parse a YAML file.

    Args:
        filepath: Path to the YAML file to load.

    Returns:
        Parsed YAML content as a dict.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(filepath: Path, data: dict[str, Any]) -> None:
    """Write data to a YAML file.

    Args:
        filepath: Path to the YAML file to write.
        data: Dict to serialize as YAML.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def get_node(graph: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    """Find a node in the graph by its ID.

    Args:
        graph: The parsed graph.yaml content.
        node_id: The ID of the node to find.

    Returns:
        The node dict if found, None otherwise.
    """
    for node in graph.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None


def load_prompt(node: dict[str, Any]) -> str:
    """Load the prompt file for a given node.

    Args:
        node: The node dict containing a prompt_file key.

    Returns:
        The content of the prompt file as a string.
    """
    prompt_path = KERNEL_ROOT / "kernel" / node["prompt_file"]
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return f"[Prompt file not found: {node['prompt_file']}]"


def get_next_node(node: dict[str, Any]) -> str | None:
    """Determine the next node from transitions.

    In dry-run / simulation mode, we simply pick the first transition.
    In a real execution, an AI agent would evaluate conditions.

    Args:
        node: The current node dict with transitions.

    Returns:
        The ID of the next node, or None if no transitions exist.
    """
    transitions = node.get("transitions", [])
    if transitions:
        return transitions[0]["to"]
    return None


def check_stop_conditions(state: dict[str, Any]) -> bool:
    """Check if the kernel should stop executing.

    Args:
        state: Current kernel state dict.

    Returns:
        True if execution should stop.
    """
    if state.get("status") == "complete":
        return True
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 30)
    if iteration >= max_iter:
        return True
    return False


def run_loop(goal: str, max_iterations: int, dry_run: bool = False) -> dict[str, Any]:
    """Execute the kernel's main loop.

    Args:
        goal: The development goal to work toward.
        max_iterations: Maximum number of iterations before stopping.
        dry_run: If True, only print what would be done without modifying state.

    Returns:
        The final state dict after execution completes.
    """
    state_path = KERNEL_ROOT / "kernel" / "state.yaml"
    graph_path = KERNEL_ROOT / "kernel" / "graph.yaml"

    state = load_yaml(state_path)
    graph = load_yaml(graph_path)

    # Initialize state with goal
    state["goal"] = goal
    state["max_iterations"] = max_iterations
    state["status"] = "running"
    state["last_updated"] = datetime.now(timezone.utc).isoformat()

    if dry_run:
        print(f"[DRY RUN] Goal: {goal}")
        print(f"[DRY RUN] Max iterations: {max_iterations}")
        print(f"[DRY RUN] Starting node: {state.get('current_node', 'init')}")
        print()

    while not check_stop_conditions(state):
        current_node_id = state.get("current_node", graph.get("default_start", "init"))
        node = get_node(graph, current_node_id)

        if node is None:
            state["status"] = "error"
            state.setdefault("errors", []).append(f"Node not found: {current_node_id}")
            break

        prompt_content = load_prompt(node)
        next_node_id = get_next_node(node)

        if dry_run:
            print(f"[DRY RUN] Iteration {state.get('iteration_count', 0) + 1}:")
            print(f"  Node: {current_node_id}")
            print(f"  Description: {node.get('description', 'N/A')}")
            print(f"  Prompt file: {node.get('prompt_file', 'N/A')}")
            print(f"  Prompt length: {len(prompt_content)} chars")
            print(f"  Next node: {next_node_id or 'END'}")
            print()
        else:
            # In real execution, this is where an AI agent would be invoked
            # with the prompt_content and current context.
            pass

        # Advance state
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        if next_node_id:
            state["current_node"] = next_node_id
        else:
            state["status"] = "complete"
            break

    # Mark as complete if we exited the loop normally
    if state.get("status") == "running":
        state["status"] = "complete"

    # Save final state (unless dry run)
    if not dry_run:
        save_yaml(state_path, state)

    if dry_run:
        print(f"[DRY RUN] Final status: {state.get('status')}")
        print(f"[DRY RUN] Total iterations: {state.get('iteration_count', 0)}")

    return state


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Self-evolving AI development kernel runner",
        prog="runner",
    )
    parser.add_argument(
        "--goal",
        type=str,
        required=True,
        help="The development goal to work toward",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=30,
        help="Maximum number of iterations (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without modifying state",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> dict[str, Any]:
    """Main entry point for the kernel runner.

    Args:
        argv: Optional argument list for testing (defaults to sys.argv[1:]).

    Returns:
        The final state dict after execution completes.
    """
    args = parse_args(argv)
    return run_loop(
        goal=args.goal,
        max_iterations=args.max_iterations,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
