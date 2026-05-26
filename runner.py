"""Self-evolving AI development kernel runner.

This is the main entry point for the kernel. It orchestrates the execution loop
by reading state, determining the current node, loading the appropriate prompt,
and advancing through the workflow graph.

Two execution modes exist:

Mode 1 (runner.py): Dry-run/scaffolding mode that traverses the graph mechanically.
    The runner does not call an LLM. It always takes the first available transition
    from each node to advance state. This is useful for verifying graph structure
    and prompt loading without requiring AI integration.

    Usage: python3.12 runner.py --goal "Build a REST API" --max-iterations 30 --dry-run

Mode 2 (AI reads BOOT.md directly): An AI agent reads kernel/BOOT.md as its
    system prompt and evaluates transition conditions itself. In this mode the
    runner is not involved and the AI manages state.yaml directly.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from kernel.graph_executor import GraphExecutor
from knowledge.store import KnowledgeStore
from memory.state_manager import StateManager


KERNEL_ROOT = Path(__file__).parent


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

    state_path = str(KERNEL_ROOT / "kernel" / "state.yaml")
    memory_dir = str(KERNEL_ROOT / "memory")
    graph_path = str(KERNEL_ROOT / "kernel" / "graph.yaml")
    knowledge_dir = str(KERNEL_ROOT / "knowledge")

    state_mgr = StateManager(state_path, memory_dir)
    graph = GraphExecutor(graph_path)
    knowledge = KnowledgeStore(knowledge_dir)

    if args.goal:
        if args.dry_run:
            state_mgr.state["goal"] = args.goal
        else:
            state_mgr.set_goal(args.goal)

    state_mgr.state["max_iterations"] = args.max_iterations
    state_mgr.state["status"] = "running"

    if args.dry_run:
        print(f"[DRY RUN] Goal: {args.goal}")
        print(f"[DRY RUN] Max iterations: {args.max_iterations}")
        print(f"[DRY RUN] Starting node: {state_mgr.state.get('current_node', 'init')}")
        print()

    for i in range(args.max_iterations):
        state = state_mgr.get_state()

        if state_mgr.is_complete():
            break

        try:
            node = graph.get_current_node(state)
        except KeyError as e:
            state_mgr.state["status"] = "error"
            state_mgr.state.setdefault("errors", []).append(str(e))
            break

        prompt_path = graph.get_prompt_for_node(node["id"])

        if args.dry_run:
            print(f"[DRY RUN] Iteration {state.get('iteration_count', 0) + 1}:")
            print(f"  Node: {node['id']}")
            print(f"  Description: {node.get('description', 'N/A')}")
            print(f"  Prompt file: {prompt_path}")

            # Load prompt to show length
            full_prompt_path = KERNEL_ROOT / "kernel" / prompt_path
            if full_prompt_path.exists():
                prompt_content = full_prompt_path.read_text(encoding="utf-8")
                print(f"  Prompt length: {len(prompt_content)} chars")
            else:
                print(f"  Prompt file: [not found]")

        state_mgr.increment_iteration()

        # SCAFFOLDING: In this mode (Mode 1), the runner always picks the first
        # available transition without evaluating conditions. This is intentional:
        # the runner does not call an LLM and cannot evaluate conditions like
        # "tests_pass" or "plan_ready". For actual condition evaluation, an AI
        # agent should read BOOT.md directly (Mode 2) and decide transitions itself.
        transitions = graph.get_available_transitions(node["id"])
        if transitions:
            next_node_id = transitions[0]["to"]
            state_mgr.set_current_node(next_node_id)
            if args.dry_run:
                print(f"  Next node: {next_node_id}")
                print()
        else:
            state_mgr.state["status"] = "complete"
            if args.dry_run:
                print(f"  Next node: END")
                print()
            break

    # Mark as complete if we finished the loop
    if state_mgr.state.get("status") == "running":
        state_mgr.state["status"] = "complete"

    if not args.dry_run:
        state_mgr.save_state()

    if args.dry_run:
        print(f"[DRY RUN] Final status: {state_mgr.state.get('status')}")
        print(f"[DRY RUN] Total iterations: {state_mgr.state.get('iteration_count', 0)}")

    return state_mgr.get_state()


if __name__ == "__main__":
    main()
