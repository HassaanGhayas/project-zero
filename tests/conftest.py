"""
Shared pytest fixtures for all test files.

Provides common vault directory structure fixtures used across
multiple test suites.
"""

import pytest
from pathlib import Path


@pytest.fixture
def vault_path(tmp_path):
    """
    Create a temporary vault directory structure for testing.

    Creates all required folders for complete workflow testing:
    - Inbox/ (file drops)
    - Needs_Action/ (pending actions)
    - Approved/ (approved actions)
    - Rejected/ (rejected actions)
    - In_Progress/ (executing actions with confirmations)
    - Done/ (completed actions)
    - Logs/ (NDJSON audit logs)
    """
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create all workflow folders
    folders = [
        "Inbox",
        "Needs_Action",
        "Approved",
        "Rejected",
        "In_Progress",
        "Done",
        "Logs",
    ]

    for folder in folders:
        (vault / folder).mkdir()

    return vault


@pytest.fixture
def inbox_path(vault_path):
    """Return path to Inbox/ folder."""
    return vault_path / "Inbox"


@pytest.fixture
def needs_action_path(vault_path):
    """Return path to Needs_Action/ folder."""
    return vault_path / "Needs_Action"


@pytest.fixture
def approved_path(vault_path):
    """Return path to Approved/ folder."""
    return vault_path / "Approved"


@pytest.fixture
def rejected_path(vault_path):
    """Return path to Rejected/ folder."""
    return vault_path / "Rejected"


@pytest.fixture
def in_progress_path(vault_path):
    """Return path to In_Progress/ folder."""
    return vault_path / "In_Progress"


@pytest.fixture
def done_path(vault_path):
    """Return path to Done/ folder."""
    return vault_path / "Done"


@pytest.fixture
def logs_path(vault_path):
    """Return path to Logs/ folder."""
    return vault_path / "Logs"
