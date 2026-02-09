#!/usr/bin/env python3
"""
Gmail MCP Server - Model Context Protocol Server for Gmail Operations

This MCP server provides tools for Gmail email management:
- archive_email: Archive Gmail message (remove from INBOX)
- mark_as_read: Mark Gmail message as read (remove UNREAD label)

All operations are idempotent and fully compliant with gmail_mcp_api.md contract.

Constitution Compliance:
    - Section V: OAuth credentials loaded from .env, never hardcoded
    - Section VI: MCP server registration required before use
    - Section VII: All operations logged to NDJSON audit trail

Usage:
    Register in .claude/settings.local.json:
    {
      "mcp_servers": {
        "gmail": {
          "command": "python",
          "args": ["/home/hasss/projects/project-zero/src/mcp/gmail_server.py"]
        }
      }
    }
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailMCPServer:
    """MCP Server for Gmail operations."""

    def __init__(self):
        """Initialize Gmail MCP server with OAuth credentials."""
        from dotenv import load_dotenv
        load_dotenv()

        self.token_path = os.getenv('GMAIL_TOKEN_PATH', str(Path.home() / '.google' / 'token.json'))
        self.credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', str(Path.home() / '.google' / 'credentials.json'))
        self.service = None
        self.creds = None

        # Setup audit logging (T029)
        self.vault_path = Path(os.getenv('VAULT_PATH', str(Path.cwd() / 'AI_Employee_Vault')))
        self.logs_path = self.vault_path / 'Logs'
        self.logs_path.mkdir(parents=True, exist_ok=True)

    def _initialize_service(self) -> bool:
        """
        Initialize Gmail API service with OAuth2 credentials.

        Returns:
            True if service initialized successfully, False otherwise
        """
        try:
            token_path = Path(self.token_path)

            if not token_path.exists():
                return False

            # Load credentials from token.json
            self.creds = Credentials.from_authorized_user_file(
                str(token_path),
                ['https://www.googleapis.com/auth/gmail.modify']
            )

            # Refresh token if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                # Save refreshed token
                token_path.write_text(self.creds.to_json())

            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True

        except Exception as e:
            self._log_error("service_initialization_failed", str(e))
            return False

    def _log_error(self, error_code: str, message: str):
        """Log error to stderr for MCP protocol."""
        error_log = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error_code": error_code,
            "message": message
        }
        print(json.dumps(error_log), file=sys.stderr)

    def _log_audit_event(self, event_type: str, context: Dict[str, Any], status: str) -> None:
        """
        Log event to NDJSON audit trail (T029).

        Args:
            event_type: Event type identifier (gmail_archive, gmail_mark_read)
            context: Event-specific context data
            status: success | error
        """
        from datetime import date

        today = date.today().isoformat()
        log_file = self.logs_path / f"{today}.json"

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "actor": "gmail_mcp_server",
            "status": status,
            **context
        }

        # Append to NDJSON log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    def archive_email(self, message_id: str) -> Dict[str, Any]:
        """
        Archive Gmail message (remove from INBOX, preserve in All Mail).

        Args:
            message_id: Gmail message ID

        Returns:
            JSON response following contracts/gmail_mcp_api.md specification
        """
        # Initialize service if not already done
        if not self.service:
            if not self._initialize_service():
                return {
                    "status": "error",
                    "error_code": "AUTH_ERROR",
                    "error_message": "Failed to initialize Gmail service. Run scripts/setup_gmail_oauth.py to authenticate.",
                    "message_id": message_id
                }

        try:
            # Check if message exists and get current labels
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='minimal'
            ).execute()

            current_labels = message.get('labelIds', [])

            # If already archived (no INBOX label), return success
            if 'INBOX' not in current_labels:
                result = {
                    "status": "success",
                    "action": "already_archived",
                    "message_id": message_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                self._log_audit_event("gmail_archive", {"message_id": message_id, "action": "already_archived"}, "success")
                return result

            # Remove INBOX label to archive
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={
                    'removeLabelIds': ['INBOX']
                }
            ).execute()

            result = {
                "status": "success",
                "action": "archived",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            self._log_audit_event("gmail_archive", {"message_id": message_id, "action": "archived"}, "success")
            return result

        except HttpError as e:
            error_code = "NETWORK_ERROR"
            error_message = str(e)

            if e.resp.status == 404:
                error_code = "NOT_FOUND"
                error_message = f"Message {message_id} not found or was deleted"
            elif e.resp.status == 401 or e.resp.status == 403:
                error_code = "AUTH_ERROR"
                error_message = "Authentication failed. Token may be expired."
            elif e.resp.status == 429:
                error_code = "RATE_LIMIT"
                error_message = "Gmail API rate limit exceeded. Implement exponential backoff."

            result = {
                "status": "error",
                "error_code": error_code,
                "error_message": error_message,
                "message_id": message_id
            }
            # Log error to audit trail
            self._log_audit_event("gmail_api_error", {"message_id": message_id, "error_code": error_code, "error_message": error_message}, "error")
            return result

        except Exception as e:
            result = {
                "status": "error",
                "error_code": "NETWORK_ERROR",
                "error_message": str(e),
                "message_id": message_id
            }
            # Log error to audit trail
            self._log_audit_event("gmail_api_error", {"message_id": message_id, "error": str(e)}, "error")
            return result

    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark Gmail message as read (remove UNREAD label).

        Args:
            message_id: Gmail message ID

        Returns:
            JSON response following contracts/gmail_mcp_api.md specification
        """
        # Initialize service if not already done
        if not self.service:
            if not self._initialize_service():
                return {
                    "status": "error",
                    "error_code": "AUTH_ERROR",
                    "error_message": "Failed to initialize Gmail service. Run scripts/setup_gmail_oauth.py to authenticate.",
                    "message_id": message_id
                }

        try:
            # Check if message exists and get current labels
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='minimal'
            ).execute()

            current_labels = message.get('labelIds', [])

            # If already marked as read (no UNREAD label), return success
            if 'UNREAD' not in current_labels:
                result = {
                    "status": "success",
                    "action": "already_marked_as_read",
                    "message_id": message_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                self._log_audit_event("gmail_mark_read", {"message_id": message_id, "action": "already_marked_as_read"}, "success")
                return result

            # Remove UNREAD label to mark as read
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()

            result = {
                "status": "success",
                "action": "marked_as_read",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            self._log_audit_event("gmail_mark_read", {"message_id": message_id, "action": "marked_as_read"}, "success")
            return result

        except HttpError as e:
            error_code = "NETWORK_ERROR"
            error_message = str(e)

            if e.resp.status == 404:
                error_code = "NOT_FOUND"
                error_message = f"Message {message_id} not found or was deleted"
            elif e.resp.status == 401 or e.resp.status == 403:
                error_code = "AUTH_ERROR"
                error_message = "Authentication failed. Token may be expired."
            elif e.resp.status == 429:
                error_code = "RATE_LIMIT"
                error_message = "Gmail API rate limit exceeded. Implement exponential backoff."

            result = {
                "status": "error",
                "error_code": error_code,
                "error_message": error_message,
                "message_id": message_id
            }
            # Log error to audit trail
            self._log_audit_event("gmail_api_error", {"message_id": message_id, "error_code": error_code, "error_message": error_message}, "error")
            return result

        except Exception as e:
            result = {
                "status": "error",
                "error_code": "NETWORK_ERROR",
                "error_message": str(e),
                "message_id": message_id
            }
            # Log error to audit trail
            self._log_audit_event("gmail_api_error", {"message_id": message_id, "error": str(e)}, "error")
            return result

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP tool request.

        Args:
            request: MCP request with tool name and arguments

        Returns:
            Tool execution result
        """
        tool_name = request.get('tool')
        args = request.get('arguments', {})

        if tool_name == 'archive_email':
            return self.archive_email(args.get('message_id', ''))
        elif tool_name == 'mark_as_read':
            return self.mark_as_read(args.get('message_id', ''))
        else:
            return {
                "status": "error",
                "error_code": "UNKNOWN_TOOL",
                "error_message": f"Unknown tool: {tool_name}"
            }

def main():
    """Main MCP server loop."""
    server = GmailMCPServer()

    # MCP protocol: read JSON requests from stdin, write responses to stdout
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            error_response = {
                "status": "error",
                "error_code": "INVALID_JSON",
                "error_message": f"Failed to parse JSON request: {str(e)}"
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e)
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
