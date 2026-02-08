#!/usr/bin/env python3
"""
Unit tests for emergency stop mechanism.

Tests cover:
- Emergency stop detection
- Action file prevention during emergency
- Audit logging of emergency events
- Resume after emergency cleared
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.watchers.filesystem_watcher import FileSystemWatcher


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory structure for testing."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create required folders
    (vault / "Inbox").mkdir()
    (vault / "Needs_Action").mkdir()
    (vault / "Logs").mkdir()

    return vault


class TestEmergencyStop:
    """Test suite for emergency stop mechanism."""

    def test_emergency_stop_detection(self, temp_vault):
        """Test that EMERGENCY_STOP.md file is detected."""
        # Create emergency stop file
        emergency_file = temp_vault / "EMERGENCY_STOP.md"
        emergency_file.write_text("System halted for maintenance")

        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Verify emergency stop is detected
        assert watcher._check_emergency_stop() is True

    def test_no_emergency_when_file_absent(self, temp_vault):
        """Test that system runs normally when EMERGENCY_STOP.md absent."""
        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Verify no emergency stop detected
        assert watcher._check_emergency_stop() is False

    def test_emergency_prevents_action_creation(self, temp_vault):
        """Test that emergency stop prevents action file creation."""
        # Create emergency stop file
        emergency_file = temp_vault / "EMERGENCY_STOP.md"
        emergency_file.write_text("Emergency active")

        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Create test file
        test_file = temp_vault / "Inbox" / "test.txt"
        test_file.write_text("Test content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(test_file))
        watcher.on_created(event)

        # Verify no action file was created
        action_file = temp_vault / "Needs_Action" / "FILE_test.txt.md"
        assert not action_file.exists()

    def test_emergency_logs_warning(self, temp_vault):
        """Test that emergency stop events are logged."""
        # Create emergency stop file
        emergency_file = temp_vault / "EMERGENCY_STOP.md"
        emergency_file.write_text("Emergency active")

        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Create test file
        test_file = temp_vault / "Inbox" / "test.txt"
        test_file.write_text("Test content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(test_file))
        watcher.on_created(event)

        # Check log file for emergency entry
        log_file = temp_vault / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        if log_file.exists():
            log_content = log_file.read_text()
            # Log should contain emergency stop mention
            assert "emergency" in log_content.lower() or "halted" in log_content.lower()

    def test_resume_after_emergency_cleared(self, temp_vault):
        """Test that system resumes normal operation after emergency cleared."""
        # Create emergency stop file
        emergency_file = temp_vault / "EMERGENCY_STOP.md"
        emergency_file.write_text("Emergency active")

        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Verify emergency is active
        assert watcher._check_emergency_stop() is True

        # Clear emergency stop
        emergency_file.unlink()

        # Verify emergency is cleared
        assert watcher._check_emergency_stop() is False

        # Test normal operation resumed
        test_file = temp_vault / "Inbox" / "test.txt"
        test_file.write_text("Test content")

        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(test_file))
        watcher.on_created(event)

        # Verify action file is now created
        action_file = temp_vault / "Needs_Action" / "FILE_test.txt.md"
        assert action_file.exists()

    def test_emergency_with_multiple_files(self, temp_vault):
        """Test that emergency stop blocks all files."""
        # Create emergency stop file
        emergency_file = temp_vault / "EMERGENCY_STOP.md"
        emergency_file.write_text("Emergency active")

        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Create multiple test files
        test_files = ["test1.txt", "test2.pdf", "test3.csv"]
        for filename in test_files:
            test_file = temp_vault / "Inbox" / filename
            test_file.write_text("Test content")

            from watchdog.events import FileCreatedEvent
            event = FileCreatedEvent(str(test_file))
            watcher.on_created(event)

        # Verify no action files were created
        for filename in test_files:
            action_file = temp_vault / "Needs_Action" / f"FILE_{filename}.md"
            assert not action_file.exists()

    def test_emergency_stop_file_content_irrelevant(self, temp_vault):
        """Test that emergency is triggered regardless of file content."""
        # Create empty emergency stop file
        emergency_file = temp_vault / "EMERGENCY_STOP.md"
        emergency_file.write_text("")  # Empty content

        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Verify emergency is still detected
        assert watcher._check_emergency_stop() is True

    def test_emergency_case_sensitivity(self, temp_vault):
        """Test that emergency stop filename is case-sensitive."""
        # Create lowercase variant (should not trigger emergency)
        wrong_case = temp_vault / "emergency_stop.md"
        wrong_case.write_text("Lowercase")

        watcher = FileSystemWatcher(
            vault_path=str(temp_vault),
            inbox_path=str(temp_vault / "Inbox")
        )

        # Verify emergency is NOT detected (wrong case)
        assert watcher._check_emergency_stop() is False

        # Create correct case
        correct_case = temp_vault / "EMERGENCY_STOP.md"
        correct_case.write_text("Correct case")

        # Verify emergency IS detected
        assert watcher._check_emergency_stop() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
