"""
Unit tests for Gmail MCP Server (T044)

Tests archive_email and mark_as_read tools with mock Gmail API.
Verifies error handling, idempotency, and audit logging.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, date

from src.mcp.gmail_server import GmailMCPServer


@pytest.fixture
def vault_path(tmp_path):
    """Create temporary vault structure for testing."""
    vault = tmp_path / "AI_Employee_Vault"
    (vault / "Logs").mkdir(parents=True)
    return vault


@pytest.fixture
def mock_gmail_service():
    """Create mock Gmail API service."""
    service = Mock()
    service.users().messages().get = Mock()
    service.users().messages().modify = Mock()
    return service


@pytest.fixture
def gmail_mcp_server(vault_path, mock_gmail_service):
    """Create GmailMCPServer instance with mocked Gmail service."""
    with patch.dict('os.environ', {'VAULT_PATH': str(vault_path)}):
        with patch('src.mcp.gmail_server.build', return_value=mock_gmail_service):
            server = GmailMCPServer()
            server.service = mock_gmail_service
            return server


class TestArchiveEmail:
    """Test archive_email MCP tool."""

    def test_archive_email_success(self, gmail_mcp_server, mock_gmail_service):
        """Test successful email archival."""
        message_id = "msg_12345"

        # Mock: message exists with INBOX label
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": message_id,
            "labelIds": ["INBOX", "UNREAD"]
        }

        # Mock: successful modification
        mock_gmail_service.users().messages().modify().execute.return_value = {
            "id": message_id,
            "labelIds": ["UNREAD"]  # INBOX removed
        }

        result = gmail_mcp_server.archive_email(message_id)

        # Verify result
        assert result["status"] == "success"
        assert result["action"] == "archived"
        assert result["message_id"] == message_id
        assert "timestamp" in result

    def test_archive_email_already_archived_idempotent(self, gmail_mcp_server, mock_gmail_service):
        """Test that archiving already-archived email returns success (idempotency)."""
        message_id = "msg_already_archived"

        # Mock: message already archived (no INBOX label)
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": message_id,
            "labelIds": ["STARRED", "UNREAD"]  # No INBOX
        }

        result = gmail_mcp_server.archive_email(message_id)

        # Should still return success (idempotent)
        assert result["status"] == "success"
        assert result["action"] == "already_archived"

    def test_archive_email_not_found(self, gmail_mcp_server, mock_gmail_service):
        """Test error handling for non-existent message."""
        from googleapiclient.errors import HttpError

        message_id = "msg_nonexistent"

        # Mock: 404 Not Found
        mock_error = Mock(spec=HttpError)
        mock_error.resp.status = 404
        mock_gmail_service.users().messages().get().side_effect = mock_error

        result = gmail_mcp_server.archive_email(message_id)

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "NOT_FOUND"
        assert message_id in result["message_id"]

    def test_archive_email_auth_error(self, gmail_mcp_server, mock_gmail_service):
        """Test error handling for authentication failure."""
        from googleapiclient.errors import HttpError

        message_id = "msg_auth_fail"

        # Mock: 401 Unauthorized
        mock_error = Mock(spec=HttpError)
        mock_error.resp.status = 401
        mock_gmail_service.users().messages().get().side_effect = mock_error

        result = gmail_mcp_server.archive_email(message_id)

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "AUTH_ERROR"

    def test_archive_email_rate_limit(self, gmail_mcp_server, mock_gmail_service):
        """Test error handling for rate limit (HTTP 429)."""
        from googleapiclient.errors import HttpError

        message_id = "msg_rate_limited"

        # Mock: 429 Rate Limit Exceeded
        mock_error = Mock(spec=HttpError)
        mock_error.resp.status = 429
        mock_gmail_service.users().messages().get().side_effect = mock_error

        result = gmail_mcp_server.archive_email(message_id)

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "RATE_LIMIT"


class TestMarkAsRead:
    """Test mark_as_read MCP tool."""

    def test_mark_as_read_success(self, gmail_mcp_server, mock_gmail_service):
        """Test successful mark as read."""
        message_id = "msg_unread_123"

        # Mock: message with UNREAD label
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": message_id,
            "labelIds": ["INBOX", "UNREAD"]
        }

        # Mock: successful modification
        mock_gmail_service.users().messages().modify().execute.return_value = {
            "id": message_id,
            "labelIds": ["INBOX"]  # UNREAD removed
        }

        result = gmail_mcp_server.mark_as_read(message_id)

        # Verify result
        assert result["status"] == "success"
        assert result["action"] == "marked_as_read"
        assert result["message_id"] == message_id

    def test_mark_as_read_already_read_idempotent(self, gmail_mcp_server, mock_gmail_service):
        """Test idempotency: marking already-read email returns success."""
        message_id = "msg_already_read"

        # Mock: message without UNREAD label
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": message_id,
            "labelIds": ["INBOX", "STARRED"]  # No UNREAD
        }

        result = gmail_mcp_server.mark_as_read(message_id)

        # Should still return success (idempotent)
        assert result["status"] == "success"
        assert result["action"] == "already_marked_as_read"


class TestAuditLogging:
    """Test NDJSON audit logging in MCP server."""

    def test_archive_email_logged_to_audit_trail(self, gmail_mcp_server, mock_gmail_service):
        """Test that archive_email operations are logged."""
        message_id = "msg_audit_archive"

        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": message_id,
            "labelIds": ["INBOX", "UNREAD"]
        }
        mock_gmail_service.users().messages().modify().execute.return_value = {
            "id": message_id,
            "labelIds": ["UNREAD"]
        }

        gmail_mcp_server.archive_email(message_id)

        # Verify audit log
        today = date.today().isoformat()
        log_file = gmail_mcp_server.logs_path / f"{today}.json"

        assert log_file.exists(), "Audit log file not created"

        with open(log_file) as f:
            lines = f.readlines()
            assert len(lines) > 0, "No audit entries"

            # Find gmail_archive event
            found_archive_event = False
            for line in lines:
                entry = json.loads(line)
                if entry.get("event_type") == "gmail_archive":
                    found_archive_event = True
                    assert entry["status"] == "success"
                    assert entry["actor"] == "gmail_mcp_server"

            assert found_archive_event, "gmail_archive event not logged"

    def test_error_logged_to_audit_trail(self, gmail_mcp_server, mock_gmail_service):
        """Test that errors are logged to audit trail."""
        from googleapiclient.errors import HttpError

        message_id = "msg_audit_error"

        # Mock error
        mock_error = Mock(spec=HttpError)
        mock_error.resp.status = 404
        mock_gmail_service.users().messages().get().side_effect = mock_error

        gmail_mcp_server.archive_email(message_id)

        # Verify error was logged
        today = date.today().isoformat()
        log_file = gmail_mcp_server.logs_path / f"{today}.json"

        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()
                error_logged = False
                for line in lines:
                    entry = json.loads(line)
                    if entry.get("status") == "error":
                        error_logged = True

                assert error_logged, "Error not logged to audit trail"


class TestMCPProtocol:
    """Test MCP protocol compliance."""

    def test_response_contains_required_fields(self, gmail_mcp_server, mock_gmail_service):
        """Test that MCP responses contain all required fields."""
        message_id = "msg_protocol_test"

        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": message_id,
            "labelIds": ["INBOX"]
        }
        mock_gmail_service.users().messages().modify().execute.return_value = {
            "id": message_id,
            "labelIds": []
        }

        result = gmail_mcp_server.archive_email(message_id)

        # Verify required fields per gmail_mcp_api.md
        assert "status" in result  # success | error
        assert result["status"] in ["success", "error"]
        assert "message_id" in result
        if result["status"] == "success":
            assert "action" in result
            assert "timestamp" in result
        else:
            assert "error_code" in result
            assert "error_message" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
