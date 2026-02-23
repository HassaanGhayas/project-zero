"""
WhatsApp Watcher - Monitor WhatsApp Business API for priority messages

Polls a local message queue (populated by src/api/whatsapp_webhook.py) to detect
incoming WhatsApp messages containing priority keywords. Generates action files for
human approval.

Architecture:
  Meta Cloud API → POST /webhook → whatsapp_webhook.py → message_queue.json
  WhatsAppWatcher (this file) ←── polls queue every 30s ──────────────────────

Constitution Compliance:
- Section V:   API credentials in .env, never logged or committed
- Section VII: Comprehensive audit logging to NDJSON
- Section VIII: Graceful error handling with recovery
- Section XII: Human-in-the-loop approval via status field
- Section XIII: Emergency stop mechanism
"""

import json
import os
import threading
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
        queue_file: Optional[Path] = None,
        check_interval: int = 30,
        logger=None,
    ):
        """
        Initialize WhatsApp watcher.

        Args:
            vault_path: Path to AI_Employee_Vault directory
            queue_file: Path to local message queue JSON file written by webhook server.
                        Defaults to ~/.whatsapp/message_queue.json
            check_interval: Polling interval in seconds (default: 30)
            logger: Optional logger instance
        """
        super().__init__(vault_path, check_interval, logger)

        self.queue_file = queue_file or Path(
            os.getenv(
                "WHATSAPP_QUEUE_FILE",
                str(Path.home() / ".whatsapp" / "message_queue.json"),
            )
        )

        # Load keywords from config file
        self.keywords = self._load_keywords()

        # Duplicate prevention (session-scoped)
        self._processed_message_ids: Set[str] = set()

        # Threading state (pattern from GmailWatcher)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self.logger.info(
            f"WhatsAppWatcher initialized (check_interval={check_interval}s, "
            f"keywords={len(self.keywords)}, queue={self.queue_file})"
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

            messages = self._read_message_queue()

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

    def _read_message_queue(self) -> List[Dict]:
        """
        Read unprocessed messages from the local WhatsApp message queue.

        The queue file is written by the webhook server (src/api/whatsapp_webhook.py)
        which receives real-time POST events from Meta's Cloud API.

        Returns:
            List of message dicts that (a) are unprocessed and (b) contain a keyword.
        """
        if not self.queue_file.exists():
            self.logger.debug("Queue file not found — webhook server may not be running")
            return []

        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                all_messages: List[Dict] = json.loads(f.read())
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(f"Failed to read queue file {self.queue_file}: {e}")
            return []

        unprocessed = [m for m in all_messages if not m.get("processed", False)]

        if not unprocessed:
            return []

        # Mark all as processed so we don't re-deliver them
        for msg in all_messages:
            msg["processed"] = True
        try:
            with open(self.queue_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(all_messages, indent=2))
        except OSError as e:
            self.logger.error(f"Failed to update queue file: {e}")

        # Filter by priority keywords (case-insensitive)
        matching: List[Dict] = []
        for msg in unprocessed:
            text = msg.get("text", "").lower()
            if any(kw.lower() in text for kw in self.keywords):
                matching.append(msg)
            else:
                self.logger.debug(
                    f"No keyword match for message from {msg.get('sender')!r} — skipping"
                )

        self.logger.debug(
            f"Queue: {len(unprocessed)} unprocessed, "
            f"{len(matching)} keyword match(es)"
        )
        return matching

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
