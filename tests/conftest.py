"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def kernel_root() -> Path:
    """Return the root directory of the kernel project."""
    return Path(__file__).parent.parent


@pytest.fixture
def state_yaml(kernel_root: Path) -> Path:
    """Return the path to state.yaml."""
    return kernel_root / "kernel" / "state.yaml"


@pytest.fixture
def graph_yaml(kernel_root: Path) -> Path:
    """Return the path to graph.yaml."""
    return kernel_root / "kernel" / "graph.yaml"
