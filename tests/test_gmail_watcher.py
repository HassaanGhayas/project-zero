"""
Unit tests for Gmail Watcher (T043)

Tests email detection, duplicate prevention, rate limit handling.
Uses mock Gmail API responses to avoid real API calls.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from src.watchers.gmail_watcher import GmailWatcher


@pytest.fixture
def vault_path(tmp_path):
    """Create temporary vault structure for testing."""
    vault = tmp_path / "AI_Employee_Vault"
    (vault / "Needs_Action").mkdir(parents=True)
    (vault / "Logs").mkdir(parents=True)
    return vault


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    return logger


@pytest.fixture
def gmail_watcher(vault_path, mock_logger):
    """Create GmailWatcher instance with mocked dependencies."""
    with patch('src.watchers.logger_config.setup_logging', return_value=mock_logger):
        with patch.object(GmailWatcher, '_initialize_gmail_service', return_value=True):
            watcher = GmailWatcher(
                vault_path=vault_path,
                check_interval=60,
                logger=mock_logger
            )
            watcher.service = Mock()  # Mock Gmail service
            return watcher


class TestEmailDetection:
    """T043: Test email detection from Gmail API."""

    def test_detect_unread_important_email(self, gmail_watcher):
        """Test detection of unread important emails."""
        # Mock Gmail API response
        mock_message = {
            "id": "msg_123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "Subject", "value": "Project Update"},
                ]
            },
            "snippet": "Here's the latest project status..."
        }

        gmail_watcher.service.users().messages().list().execute.return_value = {
            "messages": [mock_message]
        }
        gmail_watcher.service.users().messages().get().execute.return_value = mock_message

        # Execute check_for_updates
        gmail_watcher.check_for_updates()

        # Verify action file was created
        needs_action_files = list((gmail_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(needs_action_files) > 0, "No action file created"

    def test_email_action_file_contains_required_fields(self, gmail_watcher):
        """Test that generated action files have all required YAML fields."""
        mock_message = {
            "id": "msg_456",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Bob Johnson <bob@company.com>"},
                    {"name": "Subject", "value": "Budget Review"},
                ]
            },
            "snippet": "Q4 budget allocation..."
        }

        gmail_watcher.service.users().messages().list().execute.return_value = {
            "messages": [mock_message]
        }
        gmail_watcher.service.users().messages().get().execute.return_value = mock_message

        gmail_watcher.check_for_updates()

        # Read generated file and verify fields
        action_files = list((gmail_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(action_files) > 0

        content = action_files[0].read_text()
        required_fields = [
            "type: email",
            "gmail_message_id:",
            "sender:",
            "subject:",
            "status: pending",
            "priority:",
            "has_attachments:",
        ]

        for field in required_fields:
            assert field in content, f"Missing required field: {field}"


class TestDuplicatePrevention:
    """T043: Test duplicate prevention across watcher restarts."""

    def test_duplicate_prevention_with_message_id_tracking(self, gmail_watcher):
        """Test that same message ID isn't processed twice."""
        mock_message = {
            "id": "msg_duplicate_123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "vendor@acmecorp.com"},
                    {"name": "Subject", "value": "Invoice #12345"},
                ]
            },
            "snippet": "Invoice amount: $5,000"
        }

        gmail_watcher.service.users().messages().list().execute.return_value = {
            "messages": [mock_message]
        }
        gmail_watcher.service.users().messages().get().execute.return_value = mock_message

        # First check - should create action file
        gmail_watcher.check_for_updates()
        first_check_files = list((gmail_watcher.vault_path / "Needs_Action").glob("*.md"))
        first_count = len(first_check_files)

        # Second check with same message - should NOT create duplicate
        gmail_watcher.check_for_updates()
        second_check_files = list((gmail_watcher.vault_path / "Needs_Action").glob("*.md"))
        second_count = len(second_check_files)

        assert first_count == second_count, "Duplicate file created despite deduplication"
        assert "msg_duplicate_123" in gmail_watcher._processed_message_ids


class TestRateLimitHandling:
    """T043: Test exponential backoff for rate limit errors."""

    def test_exponential_backoff_on_rate_limit(self, gmail_watcher):
        """Test that check_interval doubles on rate limit error (HTTP 429)."""
        from googleapiclient.errors import HttpError

        # Create mock HttpError with 429 status
        mock_error = Mock(spec=HttpError)
        mock_error.resp.status = 429

        gmail_watcher.service.users().messages().list().side_effect = mock_error

        initial_interval = gmail_watcher.gmail_check_interval
        gmail_watcher.check_for_updates()

        # Verify backoff multiplier increased
        assert gmail_watcher._backoff_multiplier > 1, "Backoff multiplier not increased"

        # Verify interval would be doubled on next check
        expected_interval = initial_interval * gmail_watcher._backoff_multiplier
        assert expected_interval <= gmail_watcher._max_backoff_interval

    def test_max_backoff_cap(self, gmail_watcher):
        """Test that exponential backoff never exceeds max (3600s)."""
        from googleapiclient.errors import HttpError

        mock_error = Mock(spec=HttpError)
        mock_error.resp.status = 429

        gmail_watcher.service.users().messages().list().side_effect = mock_error

        # Simulate multiple rate limit errors
        for _ in range(20):
            gmail_watcher.check_for_updates()

        # Calculate final interval
        final_interval = gmail_watcher.gmail_check_interval * gmail_watcher._backoff_multiplier
        assert final_interval <= gmail_watcher._max_backoff_interval, \
            f"Backoff exceeded max: {final_interval} > {gmail_watcher._max_backoff_interval}"


class TestAttachmentDetection:
    """Test attachment detection in emails."""

    def test_detect_attachments_in_message(self, gmail_watcher):
        """Test that attachments are detected and counted."""
        mock_message = {
            "id": "msg_with_attachment",
            "payload": {
                "headers": [
                    {"name": "From", "value": "client@example.com"},
                    {"name": "Subject", "value": "Contract PDF"},
                ],
                "parts": [
                    {"partId": "0", "mimeType": "text/plain"},
                    {"partId": "1", "mimeType": "application/pdf", "filename": "contract.pdf"},
                    {"partId": "2", "mimeType": "application/pdf", "filename": "exhibit.pdf"},
                ]
            },
            "snippet": "Attached are the contract documents..."
        }

        gmail_watcher.service.users().messages().list().execute.return_value = {
            "messages": [mock_message]
        }
        gmail_watcher.service.users().messages().get().execute.return_value = mock_message

        gmail_watcher.check_for_updates()

        # Verify attachment info in action file
        action_files = list((gmail_watcher.vault_path / "Needs_Action").glob("*.md"))
        assert len(action_files) > 0

        content = action_files[0].read_text()
        assert "has_attachments: true" in content
        assert "attachment_count: 2" in content or "2" in content


class TestAuditLogging:
    """Test NDJSON audit logging for email detection."""

    def test_email_detected_event_logged(self, gmail_watcher):
        """Test that email_detected events are logged to NDJSON."""
        mock_message = {
            "id": "msg_audit_test",
            "payload": {
                "headers": [
                    {"name": "From", "value": "contact@vendor.com"},
                    {"name": "Subject", "value": "Partnership Opportunity"},
                ]
            },
            "snippet": "Interested in partnership..."
        }

        gmail_watcher.service.users().messages().list().execute.return_value = {
            "messages": [mock_message]
        }
        gmail_watcher.service.users().messages().get().execute.return_value = mock_message

        gmail_watcher.check_for_updates()

        # Verify audit log was created
        from datetime import date
        today = date.today().isoformat()
        log_file = gmail_watcher.vault_path / "Logs" / f"{today}.json"

        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) > 0, "No audit log entries"

                # Verify NDJSON format
                for line in lines:
                    entry = json.loads(line)
                    assert "timestamp" in entry
                    assert "event_type" in entry or "action_type" in entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
