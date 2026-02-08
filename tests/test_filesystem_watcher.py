#!/usr/bin/env python3
"""
Unit tests for FileSystemWatcher class.

Tests cover:
- File detection and action file creation
- YAML frontmatter generation
- Emergency stop mechanism
- Duplicate prevention
- Audit logging
- Signal handling
"""

import json
import logging
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

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


@pytest.fixture
def watcher(temp_vault):
    """Create a FileSystemWatcher instance for testing."""
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    return FileSystemWatcher(
        vault_path=str(temp_vault),
        inbox_path=str(temp_vault / "Inbox"),
        logger=logger
    )


class TestFileSystemWatcher:
    """Test suite for FileSystemWatcher functionality."""

    def test_initialization(self, watcher, temp_vault):
        """Test that watcher initializes correctly."""
        assert watcher.vault_path == temp_vault
        assert watcher.inbox_path == temp_vault / "Inbox"
        assert watcher.needs_action == temp_vault / "Needs_Action"
        assert watcher.logs_dir == temp_vault / "Logs"
        assert not watcher._running

    def test_action_file_creation(self, watcher, temp_vault):
        """Test that action files are created with correct frontmatter."""
        # Create a test file in Inbox
        test_file = temp_vault / "Inbox" / "test.txt"
        test_file.write_text("Sample content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(test_file))
        watcher.on_created(event)

        # Check that action file was created
        action_file = temp_vault / "Needs_Action" / "FILE_test.txt.md"
        assert action_file.exists()

        # Verify YAML frontmatter
        content = action_file.read_text()
        assert "---" in content
        assert "type:" in content
        assert "original_name: test.txt" in content
        assert "status: pending" in content
        assert "received:" in content

    def test_emergency_stop_halts_processing(self, watcher, temp_vault):
        """Test that EMERGENCY_STOP.md prevents action file creation."""
        # Create emergency stop file
        emergency_file = temp_vault / "EMERGENCY_STOP.md"
        emergency_file.write_text("Emergency stop active")

        # Create a test file in Inbox
        test_file = temp_vault / "Inbox" / "test.txt"
        test_file.write_text("Sample content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(test_file))
        watcher.on_created(event)

        # Verify no action file was created
        action_file = temp_vault / "Needs_Action" / "FILE_test.txt.md"
        assert not action_file.exists()

    def test_duplicate_prevention(self, watcher, temp_vault):
        """Test that duplicate action files are not created."""
        # Create a test file in Inbox
        test_file = temp_vault / "Inbox" / "test.txt"
        test_file.write_text("Sample content")

        # Create action file manually
        action_file = temp_vault / "Needs_Action" / "FILE_test.txt.md"
        action_file.write_text("---\nstatus: pending\n---\n")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(test_file))
        watcher.on_created(event)

        # Verify action file content wasn't overwritten
        assert action_file.read_text() == "---\nstatus: pending\n---\n"

    def test_hidden_files_ignored(self, watcher, temp_vault):
        """Test that hidden files are ignored."""
        # Create a hidden file
        hidden_file = temp_vault / "Inbox" / ".hidden.txt"
        hidden_file.write_text("Hidden content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(hidden_file))
        watcher.on_created(event)

        # Verify no action file was created
        action_file = temp_vault / "Needs_Action" / "FILE_.hidden.txt.md"
        assert not action_file.exists()

    def test_tmp_files_ignored(self, watcher, temp_vault):
        """Test that .tmp files are ignored."""
        # Create a temp file
        tmp_file = temp_vault / "Inbox" / "file.tmp"
        tmp_file.write_text("Temp content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(tmp_file))
        watcher.on_created(event)

        # Verify no action file was created
        action_file = temp_vault / "Needs_Action" / "FILE_file.tmp.md"
        assert not action_file.exists()

    def test_audit_logging(self, watcher, temp_vault):
        """Test that actions are logged to NDJSON log file."""
        # Create a test file in Inbox
        test_file = temp_vault / "Inbox" / "test.txt"
        test_file.write_text("Sample content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(test_file))
        watcher.on_created(event)

        # Check that log entry was created
        from datetime import datetime
        log_file = temp_vault / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        assert log_file.exists()

        # Verify log entry structure
        log_entries = log_file.read_text().strip().split("\n")
        assert len(log_entries) >= 1

        log_entry = json.loads(log_entries[-1])
        assert "timestamp" in log_entry
        assert "action_type" in log_entry
        assert log_entry["action_type"] in ["file_detected", "action_file_created"]
        assert "target" in log_entry
        assert "result" in log_entry

    def test_categorization_document(self, watcher, temp_vault):
        """Test that PDF files are categorized as documents."""
        # Create a PDF file
        pdf_file = temp_vault / "Inbox" / "document.pdf"
        pdf_file.write_text("PDF content")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(pdf_file))
        watcher.on_created(event)

        # Verify action file contains correct category
        action_file = temp_vault / "Needs_Action" / "FILE_document.pdf.md"
        content = action_file.read_text()
        assert "type: document" in content
        assert "category: document" in content

    def test_categorization_data(self, watcher, temp_vault):
        """Test that CSV files are categorized as data."""
        # Create a CSV file
        csv_file = temp_vault / "Inbox" / "data.csv"
        csv_file.write_text("col1,col2\n1,2")

        # Trigger file detection
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(csv_file))
        watcher.on_created(event)

        # Verify action file contains correct category
        action_file = temp_vault / "Needs_Action" / "FILE_data.csv.md"
        content = action_file.read_text()
        assert "type: data" in content
        assert "category: data" in content

    def test_graceful_shutdown(self, watcher):
        """Test that watcher can be stopped gracefully."""
        watcher._running = True
        watcher.stop()
        assert not watcher._running

    def test_start_creates_observer(self, watcher, temp_vault):
        """Test that start() creates and starts Observer."""
        with patch("watchdog.observers.Observer") as mock_observer:
            mock_instance = MagicMock()
            mock_observer.return_value = mock_instance

            # Start watcher in a separate thread
            import threading
            thread = threading.Thread(target=watcher.start, daemon=True)
            thread.start()
            time.sleep(0.1)

            # Verify Observer was created and started
            mock_observer.assert_called_once()
            mock_instance.schedule.assert_called_once()
            mock_instance.start.assert_called_once()

            # Stop watcher
            watcher.stop()
            thread.join(timeout=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
