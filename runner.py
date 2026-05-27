"""Self-evolving AI development kernel runner.

This is the main entry point for the kernel. It orchestrates the execution loop
by reading state, determining the current node, loading the appropriate prompt,
and advancing through the workflow graph.

Three execution modes exist:

Mode 1 (runner.py): Dry-run/scaffolding mode that traverses the graph mechanically.
    The runner does not call an LLM. It always takes the first available transition
    from each node to advance state. This is useful for verifying graph structure
    and prompt loading without requiring AI integration.

    Usage: python3.12 runner.py --goal "Build a REST API" --max-iterations 30 --dry-run

Mode 2 (AI reads BOOT.md directly): An AI agent reads kernel/BOOT.md as its
    system prompt and evaluates transition conditions itself. In this mode the
    runner is not involved and the AI manages state.yaml directly.

Mode 3 (Real AI execution via subprocess): The runner assembles context from
    kernel components and pipes it to an AI CLI tool via subprocess. The AI
    output is parsed for transition decisions.

    Usage: python3.12 runner.py --goal "Build a REST API" --ai-command "claude --print"
"""

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from kernel.bootstrap import BootstrapGenerator
from kernel.context_assembler import ContextAssembler
from kernel.contracts import OutputContractValidator
from kernel.evolution.engine import EvolutionEngine
from kernel.evolution.metrics import EvolutionMetrics
from kernel.feedback_loop import FeedbackLoop
from kernel.graph_executor import GraphExecutor
from kernel.reflector import Reflector
from kernel.skill_selector import select_skills_for_goal
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
    parser.add_argument(
        "--ai-command",
        type=str,
        default=None,
        help="AI CLI command for Mode 3 execution (e.g., 'claude --print')",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per iteration in seconds for Mode 3 (default: 300)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from saved state instead of starting fresh",
    )
    parser.add_argument(
        "--generate-prompt",
        action="store_true",
        help="Output assembled prompt to stdout and exit",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=None,
        help="Manual workspace project name override (default: derived from goal)",
    )
    parser.add_argument(
        "--skills",
        type=str,
        default=None,
        help="Comma-separated list of skill names to load (overrides auto-selection)",
    )
    return parser.parse_args(argv)


def _parse_transition(output: str) -> str | None:
    """Parse AI output for a TRANSITION line.

    Args:
        output: The AI subprocess stdout.

    Returns:
        The transition condition string, or None if not found.
    """
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("TRANSITION:"):
            return stripped[len("TRANSITION:"):].strip()
    return None


def _sanitize_project_name(goal: str) -> str:
    """Derive a sanitized project name from a goal string.

    Lowercases the goal, replaces spaces with hyphens, removes special
    characters, and truncates to 50 characters.

    Args:
        goal: The goal string to sanitize.

    Returns:
        A filesystem-safe project name.
    """
    name = goal.lower().replace(" ", "-")
    name = re.sub(r"[^a-z0-9-]", "", name)
    return name[:50]


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
        if args.resume and state_mgr.state.get("goal"):
            # When resuming, do not overwrite existing goal
            pass
        elif args.dry_run:
            state_mgr.state["goal"] = args.goal
        else:
            state_mgr.set_goal(args.goal)

    # Initialize workspace
    if args.workspace:
        project_name = args.workspace
    else:
        goal = state_mgr.state.get("goal", "")
        project_name = _sanitize_project_name(goal) if goal else ""
    if project_name and not args.dry_run:
        state_mgr.set_workspace(project_name)
    elif project_name and args.dry_run:
        state_mgr.state["workspace_path"] = f"./workspace/{project_name}/"

    # Reset node_visits on resume so stale counts don't trigger false stuck detection
    if args.resume:
        state_mgr.state["node_visits"] = {}

    # Skill auto-selection
    if hasattr(args, "skills") and args.skills is not None:
        # Manual override: use provided skill list
        selected_skills = [s.strip() for s in args.skills.split(",") if s.strip()]
    else:
        # Auto-select skills based on goal
        available_skills = knowledge.list_skills()
        goal_text = state_mgr.state.get("goal", "")
        selected_skills = select_skills_for_goal(goal_text, available_skills)
    state_mgr.state.setdefault("context", {})["skills_loaded"] = selected_skills

    state_mgr.state["max_iterations"] = args.max_iterations
    state_mgr.state["status"] = "running"

    # Handle --generate-prompt: assemble and print context, then exit
    if args.generate_prompt:
        gen = BootstrapGenerator(KERNEL_ROOT)
        prompt = gen.generate(state_path, graph_path, knowledge_dir)
        print(prompt)
        return state_mgr.get_state()

    # Determine execution mode
    mode3 = args.ai_command is not None and not args.dry_run

    if args.dry_run:
        print(f"[DRY RUN] Goal: {args.goal}")
        print(f"[DRY RUN] Max iterations: {args.max_iterations}")
        print(f"[DRY RUN] Starting node: {state_mgr.state.get('current_node', 'init')}")
        print()

    if mode3:
        assembler = ContextAssembler(KERNEL_ROOT)
        validator = OutputContractValidator(
            str(KERNEL_ROOT / "kernel" / "graph.yaml")
        )
        reflector = Reflector(memory_dir, knowledge)
        evolution_engine = EvolutionEngine(
            str(KERNEL_ROOT / "kernel"), graph
        )
        evolution_metrics = EvolutionMetrics()
        feedback_loop = FeedbackLoop(
            memory_dir, reflector, evolution_engine, evolution_metrics
        )

    # Build max_retries_map from graph nodes
    max_retries_map = {
        node["id"]: node.get("max_retries", 10)
        for node in graph.graph.get("nodes", [])
    }

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

        if mode3:
            # Mode 3: Real AI execution via subprocess
            context_prompt = assembler.assemble(state, node, graph, knowledge)
            try:
                result = subprocess.run(
                    shlex.split(args.ai_command),
                    input=context_prompt,
                    capture_output=True,
                    text=True,
                    timeout=args.timeout,
                )
                if result.returncode != 0:
                    print(
                        f"[ERROR] AI command exited with code {result.returncode}: "
                        f"{result.stderr.strip()}",
                        file=sys.stderr,
                    )
                    state_mgr.state.setdefault("errors", []).append(
                        f"AI command exited with code {result.returncode} on node {node['id']}"
                    )
                    # Run feedback loop on failure
                    iteration_data = {
                        "node": node["id"],
                        "result": "failed",
                        "errors": [f"AI command exited with code {result.returncode}"],
                        "iteration": state_mgr.state.get("iteration_count", 0),
                    }
                    feedback_loop.run_cycle(iteration_data)
                    # Do not parse stdout for transitions on failure
                    continue
                ai_output = result.stdout
                transition_condition = _parse_transition(ai_output)
            except subprocess.TimeoutExpired:
                state_mgr.state.setdefault("errors", []).append(
                    f"Timeout after {args.timeout}s on node {node['id']}"
                )
                # Stay on same node - do not advance
                continue
            except FileNotFoundError:
                print(
                    f"Error: AI command not found: '{shlex.split(args.ai_command)[0]}'. "
                    f"Please verify the command is installed and in your PATH.",
                    file=sys.stderr,
                )
                state_mgr.state["status"] = "error"
                state_mgr.state.setdefault("errors", []).append(
                    f"Command not found: {shlex.split(args.ai_command)[0]}"
                )
                break

            # Validate output against contract
            contract_result = validator.validate_output(ai_output, node["id"])
            if not contract_result.valid:
                for violation in contract_result.violations:
                    print(
                        f"[CONTRACT VIOLATION] {violation}",
                        file=sys.stderr,
                    )
                state_mgr.state.setdefault("errors", []).append(
                    f"Contract violations on node {node['id']}: "
                    f"{contract_result.violations}"
                )
                # Stay on same node - do not advance
                continue

            # Determine next node
            transitions = graph.get_available_transitions(node["id"])
            if transitions:
                if transition_condition:
                    # Try to match the AI-provided condition
                    matched = False
                    for t in transitions:
                        if t.get("condition") == transition_condition:
                            next_node_id = t["to"]
                            matched = True
                            break
                    if not matched:
                        # Fallback to first transition
                        next_node_id = transitions[0]["to"]
                        print(
                            f"[WARNING] TRANSITION condition '{transition_condition}' "
                            f"does not match any available transition, "
                            f"falling back to first transition: {next_node_id}",
                            file=sys.stderr,
                        )
                else:
                    # No TRANSITION line - fallback to first transition
                    next_node_id = transitions[0]["to"]
                    print(
                        f"[WARNING] No TRANSITION line found in AI output, "
                        f"falling back to first transition: {next_node_id}",
                        file=sys.stderr,
                    )
                    state_mgr.state.setdefault("errors", []).append(
                        f"No TRANSITION line in AI output on node {node['id']}, "
                        f"fell back to: {next_node_id}"
                    )
                state_mgr.set_current_node(next_node_id)

                # Run feedback loop on successful iteration
                iteration_data = {
                    "node": node["id"],
                    "result": "success",
                    "errors": [],
                    "iteration": state_mgr.state.get("iteration_count", 0),
                }
                feedback_loop.run_cycle(iteration_data)

                # Track visit and check stuck
                state_mgr.track_node_visit(next_node_id)
                is_stuck, stuck_node, visits = state_mgr.check_stuck(max_retries_map)
                if is_stuck:
                    # Check for stuck_handler
                    try:
                        stuck_node_def = graph.get_node(stuck_node)
                        handler = stuck_node_def.get("stuck_handler")
                    except KeyError:
                        handler = None
                    if handler:
                        state_mgr.set_current_node(handler)
                    else:
                        state_mgr.state["status"] = "stuck"
                        state_mgr.state.setdefault("errors", []).append(
                            f"Node '{stuck_node}' exceeded max_retries "
                            f"(visited {visits} times, max {max_retries_map.get(stuck_node)})"
                        )
                        break
            else:
                state_mgr.state["status"] = "complete"
                break
        else:
            # SCAFFOLDING: In this mode (Mode 1), the runner always picks the first
            # available transition without evaluating conditions. This is intentional:
            # the runner does not call an LLM and cannot evaluate conditions like
            # "tests_pass" or "plan_ready". For actual condition evaluation, an AI
            # agent should read BOOT.md directly (Mode 2) and decide transitions itself.
            transitions = graph.get_available_transitions(node["id"])
            if transitions:
                next_node_id = transitions[0]["to"]
                state_mgr.set_current_node(next_node_id)

                # Track visit and check stuck
                state_mgr.track_node_visit(next_node_id)
                is_stuck, stuck_node, visits = state_mgr.check_stuck(max_retries_map)
                if is_stuck:
                    # Check for stuck_handler
                    try:
                        stuck_node_def = graph.get_node(stuck_node)
                        handler = stuck_node_def.get("stuck_handler")
                    except KeyError:
                        handler = None
                    if handler:
                        if args.dry_run:
                            print(
                                f"  STUCK: Node '{stuck_node}' exceeded max_retries "
                                f"(visited {visits} times, max {max_retries_map.get(stuck_node)})"
                            )
                            print(f"  Redirecting to stuck_handler: {handler}")
                            print()
                        state_mgr.set_current_node(handler)
                    else:
                        if args.dry_run:
                            print(
                                f"  STUCK: Node '{stuck_node}' exceeded max_retries "
                                f"(visited {visits} times, max {max_retries_map.get(stuck_node)})"
                            )
                            print()
                        state_mgr.state["status"] = "stuck"
                        state_mgr.state.setdefault("errors", []).append(
                            f"Node '{stuck_node}' exceeded max_retries "
                            f"(visited {visits} times, max {max_retries_map.get(stuck_node)})"
                        )
                        break
                else:
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
