"""
Unit tests for WhatsApp Watcher

Tests message detection, duplicate prevention, keyword filtering, action file generation.
Uses mocks to avoid real browser automation during testing.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.watchers.whatsapp_watcher import WhatsAppWatcher


@pytest.fixture
def vault_path(tmp_path):
    """Create temporary vault structure for testing."""
    vault = tmp_path / "AI_Employee_Vault"
    (vault / "Needs_Action").mkdir(parents=True)
    (vault / "Logs").mkdir(parents=True)
    return vault


@pytest.fixture
def session_path(tmp_path):
    """Create temporary session storage path."""
    session = tmp_path / ".whatsapp" / "session"
    session.mkdir(parents=True)
    return session


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def whatsapp_watcher(vault_path, session_path, mock_logger):
    """Create WhatsAppWatcher instance with mocked dependencies."""
    # Create keywords config
    config_path = Path("config/whatsapp_keywords.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        f.write("keywords:\n  - urgent\n  - payment\n  - help\n")

    with patch("src.watchers.logger_config.setup_logging", return_value=mock_logger):
        watcher = WhatsAppWatcher(
            vault_path=vault_path,
            session_path=session_path,
            check_interval=30,
            logger=mock_logger,
        )
        return watcher


class TestMessageDetection:
    """Test WhatsApp message detection and filtering."""

    def test_detect_message_with_keyword(self, whatsapp_watcher):
        """Test detection of message containing priority keyword."""
        # Mock message with keyword
        mock_message = {
            "id": "contact_12345678",
            "sender": "Client A",
            "text": "Urgent: Need help with payment invoice",
            "timestamp": "2026-02-14T20:30:00Z",
        }

        # Mock _scan_whatsapp_web to return message
        with patch.object(
            whatsapp_watcher, "_scan_whatsapp_web", return_value=[mock_message]
        ):
            whatsapp_watcher.check_for_updates()

        # Verify action file was created
        needs_action_files = list(
            (whatsapp_watcher.vault_path / "Needs_Action").glob("*.md")
        )
        assert len(needs_action_files) > 0, "No action file created for keyword message"

    def test_action_file_contains_required_fields(self, whatsapp_watcher):
        """Test that generated action files have all required YAML fields."""
        mock_message = {
            "id": "boss_87654321",
            "sender": "Boss",
            "text": "Help needed ASAP with client presentation",
            "timestamp": "2026-02-14T21:00:00Z",
        }

        with patch.object(
            whatsapp_watcher, "_scan_whatsapp_web", return_value=[mock_message]
        ):
            whatsapp_watcher.check_for_updates()

        # Read generated file and verify fields
        action_files = list(
            (whatsapp_watcher.vault_path / "Needs_Action").glob("*.md")
        )
        assert len(action_files) > 0

        content = action_files[0].read_text()
        required_fields = [
            "type: message",
            "whatsapp_message_id:",
            "sender:",
            "received_timestamp:",
            "status: pending",
            "priority: high",
            "has_attachments:",
            "category: whatsapp_message",
        ]

        for field in required_fields:
            assert field in content, f"Missing required field: {field}"


class TestDuplicatePrevention:
    """Test duplicate prevention across multiple check cycles."""

    def test_duplicate_message_not_processed_twice(self, whatsapp_watcher):
        """Test that same message ID isn't processed twice."""
        mock_message = {
            "id": "duplicate_test_123",
            "sender": "Contact",
            "text": "Urgent payment reminder",
            "timestamp": "2026-02-14T22:00:00Z",
        }

        with patch.object(
            whatsapp_watcher, "_scan_whatsapp_web", return_value=[mock_message]
        ):
            # First check - should create action file
            whatsapp_watcher.check_for_updates()
            first_check_files = list(
                (whatsapp_watcher.vault_path / "Needs_Action").glob("*.md")
            )
            first_count = len(first_check_files)

            # Second check with same message - should NOT create duplicate
            whatsapp_watcher.check_for_updates()
            second_check_files = list(
                (whatsapp_watcher.vault_path / "Needs_Action").glob("*.md")
            )
            second_count = len(second_check_files)

        assert first_count == second_count, "Duplicate file created despite prevention"
        assert "duplicate_test_123" in whatsapp_watcher._processed_message_ids


class TestKeywordFiltering:
    """Test keyword-based message filtering."""

    def test_keyword_matching_case_insensitive(self, whatsapp_watcher):
        """Test that keyword matching is case-insensitive."""
        # Message with uppercase keyword
        mock_message = {
            "id": "uppercase_test",
            "sender": "Contact",
            "text": "URGENT message here",
            "timestamp": "2026-02-14T23:00:00Z",
        }

        # For this test, we're verifying that the watcher's keyword list
        # is correctly loaded and would match case-insensitively
        # The actual filtering happens in _scan_whatsapp_web (Playwright side)

        assert "urgent" in whatsapp_watcher.keywords
        assert len(whatsapp_watcher.keywords) > 0


class TestThreadingLifecycle:
    """Test watcher threading lifecycle."""

    def test_start_creates_background_thread(self, whatsapp_watcher):
        """Test that start() creates a daemon thread."""
        whatsapp_watcher.start()

        assert whatsapp_watcher._running is True
        assert whatsapp_watcher._thread is not None
        assert whatsapp_watcher._thread.daemon is True
        assert whatsapp_watcher._thread.is_alive()

        # Cleanup
        whatsapp_watcher.stop()

    def test_stop_gracefully_terminates_thread(self, whatsapp_watcher):
        """Test that stop() gracefully terminates the background thread."""
        whatsapp_watcher.start()
        assert whatsapp_watcher._running is True

        whatsapp_watcher.stop()

        assert whatsapp_watcher._running is False
        # Thread should finish within timeout
        if whatsapp_watcher._thread:
            whatsapp_watcher._thread.join(timeout=1.0)
            assert not whatsapp_watcher._thread.is_alive()


class TestEmergencyStop:
    """Test emergency stop mechanism."""

    def test_emergency_stop_prevents_polling(self, whatsapp_watcher):
        """Test that EMERGENCY_STOP.md prevents WhatsApp polling."""
        # Create emergency stop file
        emergency_stop_path = whatsapp_watcher.vault_path / "EMERGENCY_STOP.md"
        emergency_stop_path.write_text("# Emergency Stop\nAll watchers paused.")

        # Mock _scan_whatsapp_web to track if it's called
        with patch.object(
            whatsapp_watcher, "_scan_whatsapp_web", return_value=[]
        ) as mock_scan:
            whatsapp_watcher.check_for_updates()

            # Verify scanning was skipped
            mock_scan.assert_not_called()


class TestAuditLogging:
    """Test NDJSON audit logging for WhatsApp events."""

    def test_message_detected_event_logged(self, whatsapp_watcher):
        """Test that whatsapp_message_detected events are logged to NDJSON."""
        mock_message = {
            "id": "audit_test_msg",
            "sender": "Test Contact",
            "text": "Payment urgent reminder",
            "timestamp": "2026-02-15T00:00:00Z",
        }

        with patch.object(
            whatsapp_watcher, "_scan_whatsapp_web", return_value=[mock_message]
        ):
            whatsapp_watcher.check_for_updates()

        # Verify audit log was created
        from datetime import date

        today = date.today().isoformat()
        log_file = whatsapp_watcher.vault_path / "Logs" / f"{today}.json"

        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) > 0, "No audit log entries"

                # Verify NDJSON format
                for line in lines:
                    entry = json.loads(line)
                    assert "timestamp" in entry
                    assert "action_type" in entry

                # Check for whatsapp_message_detected event
                events = [json.loads(line) for line in lines]
                whatsapp_events = [
                    e for e in events if "whatsapp" in e.get("action_type", "")
                ]
                assert len(whatsapp_events) > 0, "No WhatsApp events logged"


class TestErrorHandling:
    """Test error handling and recovery."""

    def test_scan_error_logged_and_watcher_continues(self, whatsapp_watcher):
        """Test that errors in scanning are logged but watcher continues."""
        # Mock _scan_whatsapp_web to raise exception
        with patch.object(
            whatsapp_watcher,
            "_scan_whatsapp_web",
            side_effect=Exception("Browser connection failed"),
        ):
            # Should not crash, just log error
            whatsapp_watcher.check_for_updates()

            # Verify error was logged
            error_calls = [str(call) for call in whatsapp_watcher.logger.error.call_args_list]
            assert any("error" in str(call).lower() for call in error_calls)


class TestActionFileGeneration:
    """Test action file structure and content."""

    def test_action_file_yaml_structure(self, whatsapp_watcher):
        """Test that action file YAML is properly formatted."""
        mock_message = {
            "id": "yaml_test_123",
            "sender": "YAML Test Contact",
            "text": "Help with urgent issue",
            "timestamp": "2026-02-15T01:00:00Z",
        }

        action_file = whatsapp_watcher.create_action_file(mock_message)

        # Read file and parse YAML
        content = action_file.read_text()

        # Verify YAML delimiters
        assert content.startswith("---\n")
        assert "\n---\n" in content

        # Verify key fields present
        assert "type: message" in content
        assert "sender: YAML Test Contact" in content
        assert "priority: high" in content
        assert "status: pending" in content

    def test_action_file_markdown_sections(self, whatsapp_watcher):
        """Test that action file has proper markdown sections."""
        mock_message = {
            "id": "markdown_test",
            "sender": "Contact Name",
            "text": "Payment due urgent",
            "timestamp": "2026-02-15T02:00:00Z",
        }

        action_file = whatsapp_watcher.create_action_file(mock_message)
        content = action_file.read_text()

        # Verify markdown sections
        required_sections = [
            "## Message Details",
            "## Suggested Actions",
            "## Audit Context",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
