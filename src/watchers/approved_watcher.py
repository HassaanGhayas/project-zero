"""
Approved folder watcher for immediate action execution.

This watcher monitors Approved/ folder for newly approved action files.
When a file appears (moved by status_field_watcher), it immediately:
1. Reads the action file metadata
2. Executes the appropriate action based on type
3. Creates a confirmation sub-action file
4. Moves original to In_Progress/ (awaiting user confirmation)

Real-time response: 1-2 second latency after file appears in Approved/.

Two-stage confirmation workflow:
  Approved/ → Execute → Create confirmation file → In_Progress/
  User reviews confirmation → Moves to Done/
"""

import logging
import time
from pathlib import Path
from typing import Optional

import yaml
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .logger_config import setup_logging
from .utils import get_iso8601_timestamp, write_ndjson_log


class ApprovedWatcher(FileSystemEventHandler):
    """
    Real-time watcher for approved action files.

    Monitors Approved/ folder and executes actions immediately when
    files appear. Creates confirmation sub-actions for user final approval.

    Attributes:
        vault_path (Path): Root path to the vault
        approved_path (Path): Path to Approved/ folder being watched
        in_progress_path (Path): Path to In_Progress/ folder
        done_path (Path): Path to Done/ folder
        logs_path (Path): Path to Logs/ folder
        logger (logging.Logger): Logger instance
        observer (Observer): Watchdog Observer instance
        _action_counter (int): Counter for generating unique action IDs
    """

    def __init__(
        self,
        vault_path: str | Path,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the approved watcher.

        Args:
            vault_path: Path to vault root
            logger: Optional logger (creates default if None)
        """
        super().__init__()

        self.vault_path = Path(vault_path)
        self.approved_path = self.vault_path / "Approved"
        self.in_progress_path = self.vault_path / "In_Progress"
        self.done_path = self.vault_path / "Done"
        self.logs_path = self.vault_path / "Logs"
        self.logger = logger or setup_logging("approved_watcher", self.vault_path)

        self.observer: Optional[Observer] = None
        self._action_counter = 0
        self._running = False

        # Track processed files to avoid duplicates
        self._processed_files: set[str] = set()

        # Auto-create directories
        self._ensure_directories_exist()

    def _ensure_directories_exist(self) -> None:
        """Create required directories if they don't exist."""
        required_dirs = [
            self.approved_path,
            self.in_progress_path,
            self.done_path,
            self.logs_path
        ]

        for directory in required_dirs:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created missing directory: {directory}")

    def _check_emergency_stop(self) -> bool:
        """
        Check if EMERGENCY_STOP.md exists.

        Returns:
            True if emergency stop is active, False otherwise
        """
        emergency_stop_file = self.vault_path / "EMERGENCY_STOP.md"

        if emergency_stop_file.exists():
            self.logger.warning("🛑 EMERGENCY_STOP.md detected - operations halted")
            self._log_action(
                action_type="emergency_stop",
                target=str(emergency_stop_file),
                result="warning",
                parameters={"message": "Emergency stop file detected"}
            )
            return True

        return False

    def _generate_action_id(self) -> str:
        """Generate unique action ID for logging."""
        self._action_counter += 1
        return f"approved_watcher_{self._action_counter:04d}"

    def _log_action(
        self,
        action_type: str,
        target: str,
        result: str = "success",
        parameters: Optional[dict] = None,
        error: Optional[str] = None,
        duration: Optional[int] = None
    ) -> None:
        """
        Log action to daily NDJSON audit log.

        Args:
            action_type: Type of action (action_executed, confirmation_created, etc.)
            target: What was acted upon (file path)
            result: success | error | warning
            parameters: Action-specific data
            error: Error message if result = error
            duration: Execution time in milliseconds
        """
        from datetime import date

        today = date.today().isoformat()
        log_file = self.logs_path / f"{today}.json"

        entry = {
            "timestamp": get_iso8601_timestamp(),
            "action_id": self._generate_action_id(),
            "action_type": action_type,
            "actor": "approved_watcher",
            "target": target,
            "parameters": parameters or {},
            "approval_status": "approved",
            "approved_by": "human",
            "result": result,
            "error": error,
            "duration": duration,
        }

        write_ndjson_log(log_file, entry)

    def _read_yaml_frontmatter(self, file_path: Path) -> Optional[dict]:
        """
        Extract YAML frontmatter from markdown file.

        Args:
            file_path: Path to action file

        Returns:
            Dict of YAML frontmatter, or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Find YAML frontmatter between --- delimiters
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            yaml_content = parts[1].strip()
            frontmatter = yaml.safe_load(yaml_content)

            return frontmatter

        except Exception as e:
            self.logger.error(f"Error reading YAML from {file_path.name}: {e}")
            return None

    def _create_confirmation_file(
        self,
        original_file: Path,
        frontmatter: dict,
        execution_result: str
    ) -> Path:
        """
        Create confirmation sub-action file for user final approval.

        Args:
            original_file: Original action file path
            frontmatter: YAML frontmatter from original file
            execution_result: Result of execution (simulated for Bronze tier)

        Returns:
            Path to created confirmation file
        """
        timestamp = get_iso8601_timestamp()
        confirmation_filename = f"CONFIRM_{original_file.stem}.md"
        confirmation_path = self.in_progress_path / confirmation_filename

        # Build confirmation content
        confirmation_content = f"""---
type: confirmation
original_file: {original_file.name}
original_type: {frontmatter.get('type', 'unknown')}
category: {frontmatter.get('category', 'unknown')}
executed: {timestamp}
status: awaiting_confirmation
priority: {frontmatter.get('priority', 'medium')}
---

## Action Executed

The following action has been completed and is awaiting your confirmation:

**Original File**: {frontmatter.get('original_name', 'Unknown')}
**Type**: {frontmatter.get('type', 'unknown')}
**Category**: {frontmatter.get('category', 'unknown')}
**Size**: {frontmatter.get('size', 'unknown')} bytes
**Executed**: {timestamp}

## Execution Result

{execution_result}

## Confirmation Required

To complete this action, please review and confirm:

- [ ] Review execution result above
- [ ] Verify action was performed correctly
- [ ] Move this file to `Done/` to confirm completion
- [ ] Or move to `Rejected/` if action failed or needs revision

## Notes

This is a Bronze Tier simulated execution. In Silver/Gold tiers, real external actions
(email sends, payments, etc.) would be executed here before requesting confirmation.
"""

        # Write confirmation file
        confirmation_path.write_text(confirmation_content, encoding="utf-8")

        self.logger.info(f"Created confirmation file: {confirmation_filename}")

        return confirmation_path

    def _execute_action(
        self,
        action_file: Path,
        frontmatter: dict
    ) -> str:
        """
        Execute the action based on file type and category.

        For Bronze Tier, this is simulated. In Silver/Gold tiers,
        this would call actual MCP servers for email, payments, etc.

        Args:
            action_file: Path to action file
            frontmatter: YAML frontmatter from action file

        Returns:
            Execution result message
        """
        file_type = frontmatter.get("type", "unknown")
        category = frontmatter.get("category", "unknown")
        original_name = frontmatter.get("original_name", "unknown")

        # Bronze Tier: Simulated execution
        result_messages = {
            "text": f"✅ Text file '{original_name}' processed and archived.",
            "data": f"✅ Data file '{original_name}' validated and stored.",
            "image": f"✅ Image file '{original_name}' processed and cataloged.",
            "document": f"✅ Document '{original_name}' reviewed and filed.",
            "email": f"✅ [SIMULATED] Email regarding '{original_name}' would be sent here.",
            "payment": f"✅ [SIMULATED] Payment for '{original_name}' would be processed here.",
            "unknown": f"⚠️  File '{original_name}' marked for manual review."
        }

        result = result_messages.get(file_type, result_messages["unknown"])

        self.logger.info(f"Executed action for {action_file.name}: {result}")

        return result

    def _process_approved_file(self, file_path: Path) -> None:
        """
        Process an approved action file.

        Workflow:
          1. Read action file metadata
          2. Execute action (simulated for Bronze tier)
          3. Create confirmation sub-action
          4. Move original to In_Progress/
          5. Log execution

        Args:
            file_path: Path to approved action file
        """
        start_time = time.time()

        try:
            # Read YAML frontmatter
            frontmatter = self._read_yaml_frontmatter(file_path)

            if not frontmatter:
                self.logger.error(f"Invalid YAML frontmatter in {file_path.name}")
                self._log_action(
                    action_type="error_occurred",
                    target=str(file_path),
                    result="error",
                    error="Invalid YAML frontmatter"
                )
                return

            # Execute action (simulated for Bronze tier)
            execution_result = self._execute_action(file_path, frontmatter)

            # Create confirmation file in In_Progress/
            confirmation_path = self._create_confirmation_file(
                file_path,
                frontmatter,
                execution_result
            )

            # Move original file to In_Progress/ (renamed with timestamp)
            timestamp_suffix = get_iso8601_timestamp().replace(":", "-").replace(".", "-")
            new_filename = f"EXECUTED_{file_path.stem}_{timestamp_suffix}.md"
            in_progress_path = self.in_progress_path / new_filename

            # Read original content and update status
            content = file_path.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml_content = parts[1].strip()
                    fm = yaml.safe_load(yaml_content)
                    fm["status"] = "executed"
                    fm["executed"] = get_iso8601_timestamp()
                    updated_yaml = yaml.dump(fm, default_flow_style=False, sort_keys=False)
                    updated_content = f"---\n{updated_yaml}---\n{parts[2]}"
                    in_progress_path.write_text(updated_content, encoding="utf-8")

            # Delete original from Approved/
            file_path.unlink()

            duration_ms = int((time.time() - start_time) * 1000)

            # Log execution
            self._log_action(
                action_type="action_executed",
                target=str(file_path),
                parameters={
                    "confirmation_file": str(confirmation_path),
                    "executed_file": str(in_progress_path),
                    "file_type": frontmatter.get("type", "unknown"),
                    "category": frontmatter.get("category", "unknown"),
                },
                duration=duration_ms
            )

            self.logger.info(
                f"✅ Executed {file_path.name} → confirmation created → "
                f"awaiting user final approval"
            )

        except Exception as e:
            self.logger.error(
                f"Error processing approved file {file_path.name}: {e}",
                exc_info=True
            )
            self._log_action(
                action_type="error_occurred",
                target=str(file_path),
                result="error",
                error=str(e)
            )

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events (watchdog callback).

        Args:
            event: FileSystemEvent from watchdog

        Process:
            1. Check for emergency stop
            2. Ignore directories
            3. Only process .md files not already processed
            4. Execute action immediately (1-2 second response)
            5. Create confirmation sub-action
            6. Move to In_Progress/
        """
        # Ignore directory creation events
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process .md files
        if file_path.suffix != ".md":
            return

        # Check emergency stop
        if self._check_emergency_stop():
            return

        # Avoid duplicate processing
        file_key = str(file_path)
        if file_key in self._processed_files:
            return
        self._processed_files.add(file_key)

        # Wait briefly to ensure file write is complete
        time.sleep(0.1)

        # Process the approved file
        self.logger.info(f"New approved file detected: {file_path.name}")
        self._process_approved_file(file_path)

    def start(self) -> None:
        """
        Start the approved watcher Observer.

        Sets up watchdog Observer to monitor Approved/ for new files.
        """
        if self._running:
            self.logger.warning("Approved watcher is already running")
            return

        self._ensure_directories_exist()

        # Log watcher startup
        self._log_action(
            action_type="watcher_started",
            target=str(self.approved_path),
            parameters={"vault_path": str(self.vault_path)}
        )

        # Setup Observer
        self.observer = Observer()
        self.observer.schedule(self, str(self.approved_path), recursive=False)
        self.observer.start()

        self._running = True
        self.logger.info(f"Approved watcher started - monitoring: {self.approved_path}")

    def stop(self) -> None:
        """
        Stop the approved watcher Observer.

        Stops the watchdog Observer and logs the shutdown event.
        """
        if not self._running:
            return

        if self.observer:
            self.observer.stop()
            self.observer.join()

        self._running = False

        # Log watcher shutdown
        self._log_action(
            action_type="watcher_stopped",
            target=str(self.approved_path),
            parameters={}
        )

        self.logger.info("Approved watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._running
