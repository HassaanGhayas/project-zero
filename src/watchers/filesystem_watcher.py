"""
File system watcher for Inbox/ monitoring.

This watcher uses the watchdog library's Observer pattern for event-driven
file detection. When a file is dropped in Inbox/, it:
1. Categorizes the file by extension (FR-003)
2. Creates a structured action file in Needs_Action/ (FR-002)
3. Logs the action to the daily NDJSON audit log (FR-004)
4. Checks for EMERGENCY_STOP.md before each operation (FR-005)
"""

import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .action_file_generator import generate_action_file_content, generate_action_filename
from .categorizer import should_ignore_file
from .logger_config import setup_logging
from .utils import get_iso8601_timestamp, write_ndjson_log


class FileSystemWatcher(FileSystemEventHandler):
    """
    Event-driven file system watcher for Inbox/ folder.

    Extends watchdog's FileSystemEventHandler to detect file creation events
    and create structured action files with YAML frontmatter.

    Attributes:
        vault_path (Path): Root path to the vault
        inbox_path (Path): Path to Inbox/ folder being watched
        needs_action_path (Path): Path to Needs_Action/ folder
        logs_path (Path): Path to Logs/ folder
        logger (logging.Logger): Logger instance
        observer (Observer): Watchdog Observer instance
        _action_counter (int): Counter for generating unique action IDs
    """

    def __init__(
        self,
        vault_path: str | Path,
        inbox_path: str | Path,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the file system watcher.

        Args:
            vault_path: Path to vault root
            inbox_path: Path to Inbox/ folder to monitor
            logger: Optional logger (creates default if None)
        """
        super().__init__()

        self.vault_path = Path(vault_path)
        self.inbox_path = Path(inbox_path)
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.logs_path = self.vault_path / "Logs"
        self.logger = logger or setup_logging("filesystem_watcher", self.vault_path)

        self.observer: Optional[Observer] = None
        self._action_counter = 0
        self._running = False

        # Auto-create directories (FR-014)
        self._ensure_directories_exist()

    def _ensure_directories_exist(self) -> None:
        """Create required directories if they don't exist (FR-014)."""
        required_dirs = [self.inbox_path, self.needs_action_path, self.logs_path]

        for directory in required_dirs:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created missing directory: {directory}")

    def _check_emergency_stop(self) -> bool:
        """
        Check if EMERGENCY_STOP.md exists (FR-005).

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
        return f"watcher_{self._action_counter:04d}"

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
        Log action to daily NDJSON audit log (FR-004).

        Args:
            action_type: Type of action (file_detected, action_file_created, etc.)
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
            "actor": "filesystem_watcher",
            "target": target,
            "parameters": parameters or {},
            "approval_status": None,
            "approved_by": None,
            "result": result,
            "error": error,
            "duration": duration,
        }

        write_ndjson_log(log_file, entry)

    def _check_duplicate(self, action_filename: str) -> bool:
        """
        Check if action file already exists (FR-012: prevent duplicates).

        Args:
            action_filename: Name of the action file

        Returns:
            True if duplicate exists, False otherwise
        """
        action_file_path = self.needs_action_path / action_filename

        if action_file_path.exists():
            self.logger.warning(f"Duplicate action file detected: {action_filename}")
            return True

        return False

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events (watchdog callback).

        Args:
            event: FileSystemEvent from watchdog

        Process:
            1. Check for emergency stop (FR-005)
            2. Ignore directories and hidden/temp files (FR-011)
            3. Generate action file content
            4. Write action file to Needs_Action/ (FR-012: prevent duplicates)
            5. Log to audit trail (FR-004)
        """
        # Ignore directory creation events
        if event.is_directory:
            return

        source_path = Path(event.src_path)

        # Check emergency stop before processing
        if self._check_emergency_stop():
            return

        # Ignore hidden files and temp files (FR-011)
        if should_ignore_file(source_path):
            self.logger.debug(f"Ignoring file: {source_path.name}")
            return

        try:
            import time
            start_time = time.time()

            # Log file detection
            self._log_action(
                action_type="file_detected",
                target=str(source_path),
                parameters={
                    "size": source_path.stat().st_size,
                    "file_type": source_path.suffix.lower()
                }
            )

            self.logger.info(f"File detected: {source_path.name}")

            # Generate action filename (FR-015)
            action_filename = generate_action_filename(source_path.name)

            # Check for duplicates (FR-012)
            if self._check_duplicate(action_filename):
                self._log_action(
                    action_type="error_occurred",
                    target=str(source_path),
                    result="error",
                    error="Duplicate action file detected",
                    parameters={"action_filename": action_filename}
                )
                return

            # Generate action file content
            action_content = generate_action_file_content(source_path)

            # Write action file
            action_file_path = self.needs_action_path / action_filename
            action_file_path.write_text(action_content, encoding="utf-8")

            duration_ms = int((time.time() - start_time) * 1000)

            # Log action file creation
            self._log_action(
                action_type="action_file_created",
                target=str(action_file_path),
                parameters={
                    "source": str(source_path),
                    "category": source_path.suffix.lower()
                },
                duration=duration_ms
            )

            self.logger.info(f"Action file created: {action_filename}")

        except Exception as e:
            self.logger.error(f"Error processing file {source_path.name}: {e}", exc_info=True)
            self._log_action(
                action_type="error_occurred",
                target=str(source_path),
                result="error",
                error=str(e)
            )

    def start(self) -> None:
        """
        Start the watcher Observer (FR-013: graceful start).

        Sets up watchdog Observer to monitor Inbox/ for file creation events.
        """
        if self._running:
            self.logger.warning("Watcher is already running")
            return

        self._ensure_directories_exist()

        # Log watcher startup
        self._log_action(
            action_type="watcher_started",
            target=str(self.inbox_path),
            parameters={"vault_path": str(self.vault_path)}
        )

        # Setup Observer
        self.observer = Observer()
        self.observer.schedule(self, str(self.inbox_path), recursive=False)
        self.observer.start()

        self._running = True
        self.logger.info(f"Watcher started - monitoring: {self.inbox_path}")
        self.logger.info("Press Ctrl+C to stop")

    def stop(self) -> None:
        """
        Stop the watcher Observer (FR-013: graceful shutdown).

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
            target=str(self.inbox_path),
            parameters={}
        )

        self.logger.info("Watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._running
