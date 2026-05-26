"""Evolution engine for modifying kernel behavior.

This module handles proposing, validating, and applying evolutionary changes
to the kernel's workflow graph and prompt templates. It enforces immutability
constraints defined in the constitution.
"""

from pathlib import Path
from typing import Any


# Files that are immutable and cannot be modified by the evolution engine
IMMUTABLE_FILES = frozenset({"kernel/BOOT.md", "kernel/constitution.md", "runner.py"})


class EvolutionEngine:
    """Manages kernel self-evolution within constitutional constraints.

    The evolution engine can modify prompts, graph transitions, and knowledge
    base entries, but is explicitly prohibited from modifying files listed
    in IMMUTABLE_FILES.
    """

    def __init__(self, kernel_root: Path) -> None:
        """Initialize the evolution engine.

        Args:
            kernel_root: Path to the root directory containing the kernel.
        """
        self.kernel_root = kernel_root
        self.history_file = kernel_root / "kernel" / "evolution" / "history.jsonl"

    def propose(self, change_description: str, target_file: str, new_content: str) -> dict[str, Any]:
        """Propose an evolutionary change to the kernel.

        Args:
            change_description: Human-readable description of the change.
            target_file: Relative path to the file to modify.
            new_content: The proposed new content for the file.

        Returns:
            A dict with keys 'approved' (bool) and 'reason' (str).

        Raises:
            NotImplementedError: This method is a placeholder for FEAT-002.
        """
        raise NotImplementedError("Evolution proposal will be implemented in FEAT-002")

    def validate(self, target_file: str) -> bool:
        """Validate that a target file is allowed to be modified.

        Args:
            target_file: Relative path to the file to check.

        Returns:
            True if the file can be modified, False if it is immutable.

        Raises:
            NotImplementedError: This method is a placeholder for FEAT-002.
        """
        raise NotImplementedError("Evolution validation will be implemented in FEAT-002")

    def apply(self, change: dict[str, Any]) -> bool:
        """Apply an approved evolutionary change.

        Args:
            change: The change dict returned by propose() with approval.

        Returns:
            True if the change was applied successfully.

        Raises:
            NotImplementedError: This method is a placeholder for FEAT-002.
        """
        raise NotImplementedError("Evolution application will be implemented in FEAT-002")

    def get_history(self) -> list[dict[str, Any]]:
        """Retrieve the history of evolutionary changes.

        Returns:
            List of change records from history.jsonl.

        Raises:
            NotImplementedError: This method is a placeholder for FEAT-002.
        """
        raise NotImplementedError("Evolution history will be implemented in FEAT-002")
