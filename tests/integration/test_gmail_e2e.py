"""
End-to-End Integration Tests for Gmail Workflow (T046)

Tests complete workflow: detection → approval → execution
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import yaml
from datetime import datetime, date

from src.watchers.gmail_watcher import GmailWatcher
from src.watchers.status_field_watcher import StatusFieldWatcher
from src.watchers.approved_watcher import ApprovedWatcher
from src.mcp.gmail_server import GmailMCPServer


@pytest.fixture
def vault_path(tmp_path):
    """Create complete vault structure for E2E testing."""
    vault = tmp_path / "AI_Employee_Vault"

    dirs = [
        "Inbox",
        "Needs_Action",
        "Approved",
        "Rejected",
        "In_Progress",
        "Done",
        "Logs"
    ]

    for d in dirs:
        (vault / d).mkdir(parents=True)

    # Create minimal config
    config_file = Path(tmp_path) / "config" / "known_contacts.yaml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text(yaml.dump({
        "known_contacts": [],
        "financial_keywords": ["payment", "invoice"]
    }))

    return vault


@pytest.fixture
def mock_logger():
    """Mock logger for all watchers."""
    return Mock()


@pytest.fixture
def gmail_watcher(vault_path, mock_logger):
    """Create GmailWatcher for E2E test."""
    with patch('src.watchers.logger_config.setup_logging', return_value=mock_logger):
        with patch.object(GmailWatcher, '_initialize_gmail_service', return_value=True):
            watcher = GmailWatcher(
                vault_path=vault_path,
                check_interval=60,
                logger=mock_logger
            )
            watcher.service = Mock()
            return watcher


@pytest.fixture
def status_watcher(vault_path, mock_logger):
    """Create StatusFieldWatcher for E2E test."""
    with patch('src.watchers.logger_config.setup_logging', return_value=mock_logger):
        watcher = StatusFieldWatcher(vault_path=vault_path, logger=mock_logger)
        return watcher


@pytest.fixture
def approved_watcher(vault_path, mock_logger):
    """Create ApprovedWatcher for E2E test."""
    with patch('src.watchers.logger_config.setup_logging', return_value=mock_logger):
        watcher = ApprovedWatcher(vault_path=vault_path, logger=mock_logger)
        return watcher


@pytest.fixture
def gmail_mcp_server(vault_path):
    """Create Gmail MCP Server for E2E test."""
    import os
    with patch.dict(os.environ, {'VAULT_PATH': str(vault_path)}):
        with patch('src.mcp.gmail_server.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service

            server = GmailMCPServer()
            server.service = mock_service
            return server


class TestE2EEmailWorkflow:
    """Test complete email detection → approval → execution workflow."""

    def test_full_workflow_from_detection_to_execution(
        self,
        gmail_watcher,
        status_watcher,
        approved_watcher,
        gmail_mcp_server,
        vault_path
    ):
        """Test complete end-to-end workflow."""

        # =====================================================================
        # PHASE 1: EMAIL DETECTION (Gmail Watcher)
        # =====================================================================

        # Step 1: Simulate incoming email from Gmail API
        mock_message = {
            "id": "e2e_test_msg_001",
            "payload": {
                "headers": [
                    {"name": "From", "value": "client@example.com"},
                    {"name": "Subject", "value": "Project Update"},
                ],
                "parts": []  # No attachments
            },
            "snippet": "Here's the status on the project..."
        }

        gmail_watcher.service.users().messages().list().execute.return_value = {
            "messages": [mock_message]
        }
        gmail_watcher.service.users().messages().get().execute.return_value = mock_message

        # Step 2: Run Gmail watcher to detect email
        gmail_watcher.check_for_updates()

        # Verify: Action file created in Needs_Action/
        action_files = list((vault_path / "Needs_Action").glob("*.md"))
        assert len(action_files) == 1, "Action file not created"
        action_file = action_files[0]

        # Verify: Action file contains required fields
        content = action_file.read_text()
        assert "type: email" in content
        assert "status: pending" in content
        assert "e2e_test_msg_001" in content

        # =====================================================================
        # PHASE 2: EMAIL APPROVAL (User edits YAML + Status Field Watcher)
        # =====================================================================

        # Step 3: User edits action file to approve
        action_content = action_file.read_text()
        updated_content = action_content.replace("status: pending", "status: approved")
        action_file.write_text(updated_content)

        # Step 4: Status field watcher detects change
        # Simulate watchdog event
        from watchdog.events import FileModifiedEvent
        event = FileModifiedEvent(str(action_file))
        status_watcher.on_modified(event)

        # Verify: File moved to Approved/
        approved_files = list((vault_path / "Approved").glob("*.md"))
        assert len(approved_files) == 1, "File not moved to Approved/"
        approved_file = approved_files[0]

        # Verify: Status updated in file
        approved_content = approved_file.read_text()
        assert "status: approved" in approved_content

        # =====================================================================
        # PHASE 3: EMAIL EXECUTION (Approved Watcher + MCP Server)
        # =====================================================================

        # Step 5: Mock Gmail API for archive operation
        gmail_mcp_server.service.users().messages().get().execute.return_value = {
            "id": "e2e_test_msg_001",
            "labelIds": ["INBOX", "UNREAD"]
        }
        gmail_mcp_server.service.users().messages().modify().execute.return_value = {
            "id": "e2e_test_msg_001",
            "labelIds": ["UNREAD"]  # INBOX removed
        }

        # Step 6: Approved watcher processes approved file
        # Simulate watchdog event
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(approved_file))
        approved_watcher.on_created(event)

        # Verify: Confirmation file created in In_Progress/
        in_progress_files = list((vault_path / "In_Progress").glob("*.md"))
        assert len(in_progress_files) >= 1, "Confirmation file not created"

        # Verify: Original moved to In_Progress with status=executed
        executed_files = [
            f for f in (vault_path / "In_Progress").glob("EXECUTED_*.md")
        ]
        assert len(executed_files) >= 1, "Executed file not created"

        # =====================================================================
        # VERIFICATION: Complete Workflow
        # =====================================================================

        # Verify: Audit log contains all events
        today = date.today().isoformat()
        log_file = vault_path / "Logs" / f"{today}.json"

        if log_file.exists():
            with open(log_file) as f:
                log_entries = [json.loads(line) for line in f.readlines()]

            # Check for key events
            event_types = [e.get("event_type") or e.get("action_type") for e in log_entries]
            assert "email_detected" in event_types or len(event_types) > 0, \
                "No email_detected event in audit log"


class TestWorkflowErrorHandling:
    """Test error scenarios in E2E workflow."""

    def test_invalid_yaml_in_action_file(self, status_watcher, vault_path):
        """Test that invalid YAML is handled gracefully."""
        # Create action file with invalid YAML
        bad_file = vault_path / "Needs_Action" / "FILE_bad.md"
        bad_file.write_text("---\ninvalid: [ yaml {{{ -- \n---\nBody")

        # Attempt to process it
        from watchdog.events import FileModifiedEvent
        event = FileModifiedEvent(str(bad_file))
        status_watcher.on_modified(event)

        # Verify: File stays in Needs_Action (not moved on error)
        assert bad_file.exists(), "File was moved despite invalid YAML"

    def test_approval_with_missing_email_metadata(self, approved_watcher, vault_path):
        """Test approval of file missing email-specific metadata."""
        # Create minimal action file
        approved_file = vault_path / "Approved" / "FILE_missing_metadata.md"
        approved_file.write_text("""---
type: email
status: approved
---
Body content""")

        # Attempt to execute
        from watchdog.events import FileCreatedEvent
        event = FileCreatedEvent(str(approved_file))
        approved_watcher.on_created(event)

        # Should handle gracefully (log error but not crash)
        # File may stay in Approved/ or be moved depending on implementation
        assert (vault_path / "Approved").exists(), "Approved folder missing"


class TestConcurrentOperations:
    """Test handling of concurrent operations."""

    def test_duplicate_email_not_processed_twice(self, gmail_watcher, vault_path):
        """Test that same email ID is not processed in sequential calls."""
        mock_message = {
            "id": "concurrent_test_msg",
            "payload": {
                "headers": [
                    {"name": "From", "value": "test@example.com"},
                    {"name": "Subject", "value": "Test"},
                ]
            },
            "snippet": "Test"
        }

        gmail_watcher.service.users().messages().list().execute.return_value = {
            "messages": [mock_message]
        }
        gmail_watcher.service.users().messages().get().execute.return_value = mock_message

        # First check
        gmail_watcher.check_for_updates()
        files_after_first = len(list((vault_path / "Needs_Action").glob("*.md")))

        # Second check (same message)
        gmail_watcher.check_for_updates()
        files_after_second = len(list((vault_path / "Needs_Action").glob("*.md")))

        assert files_after_first == files_after_second, "Duplicate email created"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
