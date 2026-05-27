"""Output format contract validation for kernel AI responses.

This module provides the OutputContractValidator class which validates
AI output against the formal output format specification defined in
kernel/contracts/output_format.md.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ContractResult:
    """Result of validating AI output against the output format contract.

    Attributes:
        valid: Whether the output conforms to the contract.
        transition: The parsed TRANSITION value, or None if missing.
        files_written: List of file paths reported via FILES_WRITTEN.
        errors: List of error messages reported via ERROR lines.
        status: The parsed STATUS value (success/failure), or empty string.
        violations: List of contract violation descriptions.
    """

    valid: bool
    transition: str | None = None
    files_written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    status: str = ""
    violations: list[str] = field(default_factory=list)


class OutputContractValidator:
    """Validates AI output against the kernel output format contract.

    The validator parses output for required lines (TRANSITION, STATUS)
    and optional lines (FILES_WRITTEN, ERROR), then checks that values
    are valid for the given node based on graph.yaml transitions.
    """

    def __init__(self, graph_path: str | Path | None = None) -> None:
        """Initialize the validator.

        Args:
            graph_path: Path to graph.yaml for transition validation.
                        If None, transition value validation is skipped.
        """
        self._valid_transitions: dict[str, list[str]] = {}
        if graph_path is not None:
            self._load_valid_transitions(Path(graph_path))

    def _load_valid_transitions(self, graph_path: Path) -> None:
        """Load valid transition conditions per node from graph.yaml.

        Args:
            graph_path: Path to the graph.yaml file.
        """
        if not graph_path.exists():
            return
        with open(graph_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for node in data.get("nodes", []):
            node_id = node.get("id", "")
            conditions = []
            for transition in node.get("transitions", []):
                condition = transition.get("condition", "")
                if condition:
                    conditions.append(condition)
            self._valid_transitions[node_id] = conditions

    def validate_output(self, output: str, node_id: str) -> ContractResult:
        """Validate AI output against the output format contract.

        Parses the output for TRANSITION, STATUS, FILES_WRITTEN, and ERROR
        lines, then validates values against the contract rules.

        Args:
            output: The raw AI output string.
            node_id: The current node ID for transition validation.

        Returns:
            A ContractResult with parsed values and any violations.
        """
        violations: list[str] = []
        transition = self._parse_transition(output)
        status = self._parse_status(output)
        files_written = self._parse_files_written(output)
        errors = self._parse_errors(output)

        # Validate TRANSITION
        if transition is None:
            violations.append("Missing required TRANSITION line")
        elif self._valid_transitions:
            valid_for_node = self._valid_transitions.get(node_id, [])
            if valid_for_node and transition not in valid_for_node:
                violations.append(
                    f"Invalid TRANSITION '{transition}' for node '{node_id}'. "
                    f"Valid transitions: {valid_for_node}"
                )

        # Validate STATUS
        if not status:
            violations.append("Missing required STATUS line")
        elif status not in ("success", "failure"):
            violations.append(
                f"Invalid STATUS '{status}'. Must be 'success' or 'failure'"
            )

        valid = len(violations) == 0

        return ContractResult(
            valid=valid,
            transition=transition,
            files_written=files_written,
            errors=errors,
            status=status,
            violations=violations,
        )

    def _parse_transition(self, output: str) -> str | None:
        """Parse the TRANSITION line from output.

        Args:
            output: The raw AI output.

        Returns:
            The transition condition string, or None if not found.
        """
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("TRANSITION:"):
                return stripped[len("TRANSITION:"):].strip()
        return None

    def _parse_status(self, output: str) -> str:
        """Parse the STATUS line from output.

        Args:
            output: The raw AI output.

        Returns:
            The status string, or empty string if not found.
        """
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("STATUS:"):
                return stripped[len("STATUS:"):].strip()
        return ""

    def _parse_files_written(self, output: str) -> list[str]:
        """Parse FILES_WRITTEN lines from output.

        Args:
            output: The raw AI output.

        Returns:
            List of file paths found.
        """
        files: list[str] = []
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("FILES_WRITTEN:"):
                raw = stripped[len("FILES_WRITTEN:"):].strip()
                if raw:
                    files.extend(
                        f.strip() for f in raw.split(",") if f.strip()
                    )
        return files

    def _parse_errors(self, output: str) -> list[str]:
        """Parse ERROR lines from output.

        Args:
            output: The raw AI output.

        Returns:
            List of error messages found.
        """
        errors: list[str] = []
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("ERROR:"):
                msg = stripped[len("ERROR:"):].strip()
                if msg:
                    errors.append(msg)
        return errors
