"""
WhatsApp Watcher - Monitor WhatsApp Web for priority messages

Polls WhatsApp Web using Playwright browser automation to detect unread messages
containing priority keywords. Generates action files for human approval.

Constitution Compliance:
- Section V: Browser session stored in ~/.whatsapp/session (not in repo)
- Section VII: Comprehensive audit logging to NDJSON
- Section VIII: Graceful error handling with recovery
- Section XII: Human-in-the-loop approval via status field
- Section XIII: Emergency stop mechanism
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

from src.watchers.base_watcher import BaseWatcher
from src.watchers.utils import sanitize_filename


class WhatsAppWatcher(BaseWatcher):
    """
    Monitor WhatsApp Web for unread messages with priority keywords.

    Uses Playwright browser automation to poll WhatsApp Web every 30 seconds.
    Maintains browser session persistence to avoid repeated QR code scans.
    """

    def __init__(
        self,
        vault_path: Path,
        session_path: Path,
        check_interval: int = 30,
        logger=None,
    ):
        """
        Initialize WhatsApp watcher.

        Args:
            vault_path: Path to AI_Employee_Vault directory
            session_path: Path to browser session storage directory
            check_interval: Polling interval in seconds (default: 30)
            logger: Optional logger instance
        """
        super().__init__(vault_path, check_interval, logger)
        self.session_path = Path(session_path)
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Load keywords from config file
        self.keywords = self._load_keywords()

        # Duplicate prevention (session-scoped)
        self._processed_message_ids: Set[str] = set()

        # Threading state (pattern from GmailWatcher)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Browser automation will use Playwright MCP
        self._browser_initialized = False

        self.logger.info(
            f"WhatsAppWatcher initialized (check_interval={check_interval}s, "
            f"keywords={len(self.keywords)})"
        )

    def _load_keywords(self) -> List[str]:
        """Load priority keywords from config file."""
        config_path = Path("config/whatsapp_keywords.yaml")

        # Default keywords if config doesn't exist
        default_keywords = ["urgent", "asap", "invoice", "payment", "help"]

        if not config_path.exists():
            self.logger.warning(
                f"Keywords config not found at {config_path}, using defaults"
            )
            return default_keywords

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                keywords = config.get("keywords", default_keywords)
                self.logger.info(f"Loaded {len(keywords)} keywords from {config_path}")
                return keywords
        except Exception as e:
            self.logger.error(f"Error loading keywords config: {e}, using defaults")
            return default_keywords

    def start(self) -> None:
        """Start the WhatsApp watcher in a background thread."""
        if self._running:
            self.logger.warning("WhatsApp watcher is already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.logger.info("WhatsApp watcher thread started")

    def stop(self) -> None:
        """Stop the WhatsApp watcher gracefully."""
        if not self._running:
            return

        self.logger.info("Stopping WhatsApp watcher...")
        self._running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        self.logger.info("WhatsApp watcher stopped")

    def _run_loop(self) -> None:
        """Background thread loop that polls WhatsApp Web periodically."""
        while self._running and not self._stop_event.is_set():
            try:
                self.check_for_updates()
            except Exception as e:
                self.logger.error(f"Error in WhatsApp watcher loop: {e}", exc_info=True)
                self._log_action(
                    action_type="whatsapp_watcher_error",
                    target="background_loop",
                    status="error",
                    parameters={"error": str(e)},
                )

            # Sleep until next check (interruptible)
            self._stop_event.wait(timeout=self.check_interval)

    def check_for_updates(self) -> None:
        """
        Poll WhatsApp Web for new unread messages.

        Constitution compliance:
        - Section XIII: Check EMERGENCY_STOP.md before polling
        - Section VII: Log all detections to audit trail
        - Section VIII: Graceful error handling
        """
        # Emergency stop check (Constitution Section XIII)
        emergency_stop_path = self.vault_path / "EMERGENCY_STOP.md"
        if emergency_stop_path.exists():
            self.logger.warning("🛑 EMERGENCY STOP active - skipping WhatsApp polling")
            return

        try:
            # Import Playwright tools (lazy import to avoid startup overhead)
            # Note: In production, this would use Playwright MCP server
            # For now, we'll implement the core logic structure

            messages = self._scan_whatsapp_web()

            if messages:
                self.logger.info(
                    f"Found {len(messages)} unread message(s) with keywords"
                )

                for message in messages:
                    msg_id = message["id"]

                    # Duplicate prevention
                    if msg_id in self._processed_message_ids:
                        self.logger.debug(f"Skipping duplicate message: {msg_id}")
                        continue

                    # Create action file
                    action_file = self.create_action_file(message)
                    self._processed_message_ids.add(msg_id)

                    # Log to audit trail
                    self._log_action(
                        action_type="whatsapp_message_detected",
                        target=str(action_file),
                        status="success",
                        parameters={
                            "message_id": msg_id,
                            "sender": message["sender"],
                            "has_keyword": True,
                        },
                    )

                    self.logger.info(f"Created action file: {action_file.name}")
            else:
                self.logger.debug("No new priority messages found")

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp updates: {e}", exc_info=True)
            self._log_action(
                action_type="whatsapp_check_error",
                target="whatsapp_web",
                status="error",
                parameters={"error": str(e)},
            )

    def _scan_whatsapp_web(self) -> List[Dict]:
        """
        Scan WhatsApp Web for unread messages using Playwright.

        This is a placeholder implementation. In production, this would:
        1. Launch persistent browser context (session_path)
        2. Navigate to web.whatsapp.com
        3. Wait for page load (handle QR code on first run)
        4. Query for unread chats [aria-label*="unread"]
        5. Extract sender, message preview, timestamp
        6. Filter by keywords
        7. Return list of matching messages

        Returns:
            List of message dictionaries with id, sender, text, timestamp
        """
        # TODO: Implement Playwright browser automation
        # For now, return empty list (no messages)
        # This will be implemented using Playwright MCP server calls

        messages = []

        # Placeholder structure for what would be returned:
        # messages = [
        #     {
        #         "id": f"{sender}_{hash(preview)}",
        #         "sender": "Contact Name",
        #         "text": "Message preview text...",
        #         "timestamp": datetime.now().isoformat(),
        #     }
        # ]

        return messages

    def create_action_file(self, message: Dict) -> Path:
        """
        Create action file from WhatsApp message.

        Args:
            message: Dictionary with id, sender, text, timestamp

        Returns:
            Path to created action file
        """
        # Generate unique filename
        safe_sender = sanitize_filename(message["sender"])
        msg_id_short = message["id"][:8] if len(message["id"]) > 8 else message["id"]
        filename = f"FILE_{safe_sender}_{msg_id_short}.md"
        filepath = self.needs_action / filename

        # Prepare YAML frontmatter (10 required fields)
        frontmatter = {
            "type": "message",
            "whatsapp_message_id": message["id"],
            "sender": message["sender"],
            "received_timestamp": message["timestamp"],
            "status": "pending",
            "priority": "high",  # All keyword matches = high priority (v1)
            "has_attachments": False,  # Future enhancement
            "category": "whatsapp_message",
            "suggested_actions": [
                "Read full message in WhatsApp",
                "Reply to sender",
                "Mark as handled",
            ],
        }

        # Build markdown content
        content_parts = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip(),
            "---",
            "",
            "## Message Details",
            "",
            f"**From:** {message['sender']}",
            f"**Received:** {message['timestamp']}",
            "",
            "**Message:**",
            message["text"],
            "",
            "## Suggested Actions",
            "",
            "- [ ] Read full message in WhatsApp",
            "- [ ] Reply to sender via WhatsApp MCP",
            "- [ ] Forward to relevant party",
            "- [ ] Mark as handled",
            "",
            "## Audit Context",
            "",
            f"- **Detection Time:** {datetime.now().isoformat()}",
            f"- **Detected By:** whatsapp_watcher",
            f"- **Message ID:** {message['id']}",
            "",
        ]

        content = "\n".join(content_parts)

        # Write to file
        filepath.write_text(content, encoding="utf-8")

        # Log action file creation
        self._log_action(
            action_type="action_file_created",
            target=str(filepath),
            status="success",
            parameters={
                "source": "whatsapp",
                "sender": message["sender"],
                "message_id": message["id"],
            },
        )

        return filepath

    def _log_action(
        self,
        action_type: str,
        target: str,
        status: str = "success",
        parameters: Optional[Dict] = None,
    ) -> None:
        """
        Log action to NDJSON audit trail.

        Constitution Section VII: Comprehensive audit logging.

        Args:
            action_type: Type of action (e.g., "whatsapp_message_detected")
            target: Target of action (e.g., file path)
            status: Action status (success/error/warning)
            parameters: Additional metadata (no secrets!)
        """
        from datetime import date

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "whatsapp_watcher",
            "target": target,
            "status": status,
            "parameters": parameters or {},
        }

        # Write to daily log file (NDJSON format)
        log_dir = self.vault_path / "Logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"{date.today().isoformat()}.json"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
