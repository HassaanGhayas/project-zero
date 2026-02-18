"""
Gmail Watcher - Monitors Gmail for unread important messages.

Extends BaseWatcher to poll Gmail API and generate action files for emails
requiring human review. Implements exponential backoff for rate limits,
duplicate prevention via message ID tracking, and OAuth token refresh.

Constitution Compliance:
    - Section V: OAuth credentials loaded from .env
    - Section VII: All detections logged to NDJSON audit trail
    - Section VIII: Graceful error recovery with exponential backoff
    - Section XII: All emails require human approval via action files

Usage:
    watcher = GmailWatcher(vault_path="/path/to/vault", check_interval=120)
    watcher.run()
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base_watcher import BaseWatcher
from .email_categorizer import EmailCategorizer
from .utils import (
    create_yaml_frontmatter,
    write_ndjson_log,
    get_iso8601_timestamp,
    sanitize_filename,
)


class GmailWatcher(BaseWatcher):
    """
    Gmail watcher that polls Gmail API for unread important messages.

    Attributes:
        service: Gmail API service instance
        creds: OAuth2 credentials
        _processed_message_ids: Set of already-processed message IDs
        _backoff_multiplier: Current backoff multiplier for rate limiting
        gmail_check_interval: Configured Gmail polling interval
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 120,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Absolute path to vault root
            check_interval: Seconds between Gmail API polls (default: 120)
            logger: Optional logger instance
        """
        super().__init__(vault_path, check_interval, logger)

        # Load Gmail-specific configuration
        self.credentials_path = os.getenv(
            "GMAIL_CREDENTIALS_PATH", str(Path.home() / ".google" / "credentials.json")
        )
        self.token_path = os.getenv(
            "GMAIL_TOKEN_PATH", str(Path.home() / ".google" / "token.json")
        )
        self.gmail_check_interval = int(os.getenv("GMAIL_CHECK_INTERVAL", "120"))

        # Gmail API service (initialized on first check)
        self.service = None
        self.creds = None

        # Duplicate prevention: track processed message IDs
        self._processed_message_ids: Set[str] = set()

        # Rate limiting: exponential backoff state
        self._backoff_multiplier = 1
        self._max_backoff_interval = 3600  # 1 hour max

        # Email categorizer for priority determination (T039)
        categorizer_config_path = (
            Path(vault_path).parent / "config" / "known_contacts.yaml"
        )
        self.categorizer = EmailCategorizer(categorizer_config_path, logger=self.logger)

        self.logger.info(
            f"GmailWatcher initialized (check_interval={self.gmail_check_interval}s)"
        )

        # Threading state for start/stop
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """
        Start the Gmail watcher in a background thread.

        Creates a daemon thread that polls Gmail API at gmail_check_interval.
        Thread runs until stop() is called or process terminates.
        """
        if self._running:
            self.logger.warning("Gmail watcher is already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.logger.info("Gmail watcher thread started")

    def stop(self) -> None:
        """
        Stop the Gmail watcher gracefully.

        Signals the background thread to stop and waits for it to finish.
        """
        if not self._running:
            return

        self.logger.info("Stopping Gmail watcher...")
        self._running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self.logger.info("Gmail watcher stopped")

    def _run_loop(self) -> None:
        """
        Background thread loop that polls Gmail API periodically.

        Runs check_for_updates() every gmail_check_interval seconds until stopped.
        Applies exponential backoff interval when rate limited.
        """
        while self._running and not self._stop_event.is_set():
            try:
                self.check_for_updates()
            except Exception as e:
                self.logger.error(f"Error in Gmail watcher loop: {e}", exc_info=True)

            # Calculate sleep interval with backoff multiplier
            sleep_interval = min(
                self.gmail_check_interval * self._backoff_multiplier,
                self._max_backoff_interval,
            )

            # Interruptible sleep using stop_event
            self._stop_event.wait(timeout=sleep_interval)

    def _initialize_gmail_service(self) -> bool:
        """
        Initialize Gmail API service with OAuth2 credentials.

        Returns:
            True if service initialized successfully, False otherwise

        Handles:
            - Token loading from token.json
            - Token refresh if expired
            - Service construction with Gmail API v1
        """
        try:
            token_path = Path(self.token_path)

            if not token_path.exists():
                self.logger.error(
                    f"Gmail token not found at {token_path}. "
                    "Run scripts/setup_gmail_oauth.py to authenticate."
                )
                self._log_audit_event(
                    "gmail_initialization_failed",
                    {"error": "token_not_found", "token_path": str(token_path)},
                    "error",
                )
                return False

            # Load existing token
            self.creds = Credentials.from_authorized_user_file(
                str(token_path), ["https://www.googleapis.com/auth/gmail.modify"]
            )

            # Refresh if expired
            if self.creds.expired and self.creds.refresh_token:
                self.logger.info("Refreshing expired Gmail token...")
                self.creds.refresh(Request())
                # Save refreshed token
                token_path.write_text(self.creds.to_json())
                self.logger.info("Token refreshed successfully")

            # Build Gmail API service
            self.service = build("gmail", "v1", credentials=self.creds)
            self.logger.info("Gmail service initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}", exc_info=True)
            self._log_audit_event(
                "gmail_initialization_failed", {"error": str(e)}, "error"
            )
            return False

    def _handle_rate_limit_error(self) -> None:
        """
        Handle Gmail API rate limit error with exponential backoff.

        Doubles the check_interval up to a maximum of 3600 seconds (1 hour).
        Logs backoff event to audit trail.

        Constitution Section VIII: Graceful degradation with exponential backoff.
        """
        # Double the backoff multiplier
        self._backoff_multiplier *= 2

        # Calculate new check interval
        new_interval = min(
            self.gmail_check_interval * self._backoff_multiplier,
            self._max_backoff_interval,
        )

        self.logger.warning(
            f"Rate limit hit. Backing off to {new_interval}s check interval "
            f"(multiplier: {self._backoff_multiplier}x)"
        )

        self._log_audit_event(
            "gmail_rate_limit_backoff",
            {
                "old_interval": self.check_interval,
                "new_interval": new_interval,
                "backoff_multiplier": self._backoff_multiplier,
            },
            "warning",
        )

        # Update check interval
        self.check_interval = new_interval

    def _reset_backoff(self) -> None:
        """Reset exponential backoff to normal check interval after successful API call."""
        if self._backoff_multiplier > 1:
            self.logger.info(
                f"Resetting backoff to normal interval ({self.gmail_check_interval}s)"
            )
            self._backoff_multiplier = 1
            self.check_interval = self.gmail_check_interval

    def check_for_updates(self) -> None:
        """
        Poll Gmail API for unread important messages.

        Query: "is:unread is:important label:inbox"
        - Checks every 120 seconds (configurable via GMAIL_CHECK_INTERVAL)
        - Tracks processed message IDs to prevent duplicates
        - Implements exponential backoff on rate limit errors (HTTP 429)
        - Logs all detections to NDJSON audit trail

        Raises:
            No exceptions raised - errors are logged and handled gracefully
        """
        # Initialize service on first check
        if not self.service:
            if not self._initialize_gmail_service():
                self.logger.error(
                    "Gmail service not initialized. Skipping check cycle."
                )
                return

        # Check for emergency stop
        emergency_stop_path = self.vault_path / "EMERGENCY_STOP.md"
        if emergency_stop_path.exists():
            self.logger.warning(
                "EMERGENCY STOP active - skipping Gmail check (Constitution Section XIII)"
            )
            return

        try:
            # Query Gmail API for unread important messages in inbox.
            # Query syntax:
            #   is:unread - Only messages marked unread by Gmail's system
            #   is:important - Only starred/marked-important by Gmail ML (not user starred)
            #   label:inbox - Only in main inbox (excludes archive, spam, trash)
            # This combination filters to actionable emails that Gmail considers important.
            query = "is:unread is:important label:inbox"
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=50)
                .execute()
            )

            messages = results.get("messages", [])

            if not messages:
                self.logger.debug("No unread important messages found")
                self._reset_backoff()  # Successful API call, reset backoff
                return

            self.logger.info(f"Found {len(messages)} unread important message(s)")

            # Process each message
            for message_summary in messages:
                message_id = message_summary["id"]

                # Duplicate prevention (Constitution Section XII: idempotency)
                # Gmail returns multiple copies of same message during development/testing,
                # and rapid reruns might catch same unread messages.
                # Store all processed IDs in memory for this watcher session.
                # Note: Persists across checks but resets on watcher restart (acceptable for MVP).
                if message_id in self._processed_message_ids:
                    self.logger.debug(f"Skipping duplicate message {message_id[:8]}...")
                    continue

                # Fetch full message details from Gmail API
                # Note: Gmail returns message summaries first, then require full get() for headers/payload
                message = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message_id, format="full")
                    .execute()
                )

                # Create action file for this email
                self.create_action_file(message)

                # Mark as processed to prevent creating duplicate action files
                self._processed_message_ids.add(message_id)

            # Successful API call, reset backoff if needed
            self._reset_backoff()

        except HttpError as e:
            if e.resp.status == 429:
                # Rate limit error (HTTP 429) - Gmail API throttling
                # Strategy: Exponential backoff (Constitution Section VIII: graceful degradation)
                # - First backoff: 120s → 240s (2x multiplier)
                # - Second backoff: 240s → 480s (4x multiplier)
                # - Max backoff: 3600s (1 hour) to avoid service stall
                # Rate limits typically reset after ~1 minute, but we back off longer to be safe
                self.logger.warning("Gmail API rate limit exceeded (HTTP 429)")
                self._handle_rate_limit_error()
            elif e.resp.status == 401 or e.resp.status == 403:
                # Authentication error - token may be expired or revoked
                # Solution: User must re-authenticate via setup_gmail_oauth.py
                self.logger.error(
                    "Gmail authentication failed. "
                    "Run scripts/setup_gmail_oauth.py to re-authenticate."
                )
                self._log_audit_event(
                    "gmail_auth_error", {"http_status": e.resp.status}, "error"
                )
            else:
                self.logger.error(f"Gmail API error: {e}", exc_info=True)
                self._log_audit_event("gmail_api_error", {"error": str(e)}, "error")

        except Exception as e:
            self.logger.error(f"Unexpected error in Gmail check: {e}", exc_info=True)
            self._log_audit_event("gmail_check_error", {"error": str(e)}, "error")

    def create_action_file(self, message: Dict[str, Any]) -> None:
        """
        Generate email action file in Needs_Action/ folder.

        Args:
            message: Gmail API message object with headers and payload

        Creates:
            Markdown file with YAML frontmatter per data-model.md:
            - type: email
            - gmail_message_id: message ID
            - sender: from email address
            - sender_name: parsed name (if available)
            - subject: email subject
            - received_timestamp: ISO 8601 UTC
            - status: pending
            - priority: high (default for Phase 1 MVP)
            - has_attachments: boolean
            - attachment_count: integer
            - category: email
            - suggested_actions: list of actions

        Constitution Section XII: All emails require human approval via status field editing.
        """
        try:
            # Extract message metadata
            message_id = message["id"]
            headers = {
                h["name"].lower(): h["value"] for h in message["payload"]["headers"]
            }

            sender = headers.get("from", "unknown@example.com")
            subject = headers.get("subject", "(No subject)")
            received_timestamp = get_iso8601_timestamp()

            # Parse sender name if available (format: "Name <email@example.com>")
            sender_name = None
            if "<" in sender and ">" in sender:
                sender_name = sender.split("<")[0].strip()
                sender_email = sender.split("<")[1].split(">")[0].strip()
            else:
                sender_email = sender

            # Check for attachments (T040)
            has_attachments = self._check_attachments(message)
            attachment_count = self._count_attachments(message)

            # Get email snippet for categorization
            snippet = message.get("snippet", "")

            # Determine priority and category using email categorizer (T039, T041, T042)
            priority, category, suggested_actions = self.categorizer.determine_priority(
                sender_email=sender_email,
                subject=subject,
                snippet=snippet,
                has_attachments=has_attachments,
            )

            # Generate YAML frontmatter
            frontmatter_fields = {
                "type": "email",
                "gmail_message_id": message_id,
                "sender": sender_email,
                "sender_name": sender_name or sender_email,
                "subject": subject,
                "received_timestamp": received_timestamp,
                "status": "pending",
                "priority": priority,  # Determined by categorizer
                "has_attachments": has_attachments,
                "attachment_count": attachment_count,
                "category": category,  # Determined by categorizer
                "suggested_actions": suggested_actions,  # Generated by categorizer
            }

            yaml_section = create_yaml_frontmatter(frontmatter_fields)

            # Get email snippet (first 200 chars)
            snippet = message.get("snippet", "(No preview available)")[:200]

            # Generate markdown body
            body = f"""
## Email Details

**From**: {sender}
**Subject**: {subject}
**Received**: {received_timestamp}

## Email Snippet

> {snippet}

## Attachments

{'- ' + str(attachment_count) + ' attachment(s) present' if has_attachments else '- No attachments'}

## Suggested Actions

Based on Gmail Integration rules (Company_Handbook.md):
- **High priority**: Requires human approval before any action
- Review email in Gmail: https://mail.google.com/mail/u/0/#inbox/{message_id}
- Edit YAML status field to "approved" to archive this email
- Edit YAML status field to "rejected" to keep in inbox without action

## Audit Context

- Detection timestamp: {received_timestamp}
- Created by: gmail_watcher
- Message ID: {message_id}
"""

            # Generate action filename
            sanitized_subject = sanitize_filename(subject)[:50]  # Limit length
            action_filename = f"FILE_{sender_email}_{sanitized_subject}.md"

            # Write action file to Needs_Action/
            action_filepath = self.needs_action / action_filename
            action_filepath.write_text(yaml_section + "\n" + body, encoding="utf-8")

            self.logger.info(f"Created email action file: {action_filename}")

            # Log detection event to audit trail
            self._log_audit_event(
                "email_detected",
                {
                    "message_id": message_id,
                    "sender": sender_email,
                    "subject": subject,
                    "priority": "high",
                    "has_attachments": has_attachments,
                    "action_file": action_filename,
                },
                "success",
            )

        except Exception as e:
            self.logger.error(
                f"Failed to create action file for message {message.get('id', 'unknown')}: {e}",
                exc_info=True,
            )
            self._log_audit_event(
                "email_action_file_creation_failed",
                {"message_id": message.get("id"), "error": str(e)},
                "error",
            )

    def _check_attachments(self, message: Dict[str, Any]) -> bool:
        """
        Check if message has attachments.

        Gmail API payload structure for multipart messages:
        - payload.parts[] contains message parts (body text, HTML, attachments)
        - Each part has: mimeType, partId, headers[], body{}
        - Attachments identified by: filename + body.attachmentId (not data blob)
        - Non-attachment parts have: body.size but no attachmentId

        Returns True only if at least one part has both filename and attachmentId.
        """
        payload = message.get("payload", {})
        parts = payload.get("parts", [])

        for part in parts:
            # Check for both filename and attachmentId to distinguish from inline images
            if part.get("filename") and part.get("body", {}).get("attachmentId"):
                return True

        return False

    def _count_attachments(self, message: Dict[str, Any]) -> int:
        """
        Count number of attachments in message.

        Same Gmail API structure as _check_attachments, but returns count instead
        of boolean. Used for informational purposes in action file frontmatter.
        """
        payload = message.get("payload", {})
        parts = payload.get("parts", [])

        count = 0
        for part in parts:
            # Count only parts with both filename and attachmentId
            if part.get("filename") and part.get("body", {}).get("attachmentId"):
                count += 1

        return count

    def _log_audit_event(
        self, event_type: str, context: Dict[str, Any], status: str
    ) -> None:
        """
        Log event to NDJSON audit trail.

        Args:
            event_type: Event type identifier
            context: Event-specific context data
            status: success | warning | error

        Constitution Section VII: All email detections logged to audit trail.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = self.vault_path / "Logs" / f"{today}.json"

        entry = {
            "timestamp": get_iso8601_timestamp(),
            "event_type": event_type,
            "actor": "gmail_watcher",
            "status": status,
            **context,
        }

        write_ndjson_log(log_path, entry)
