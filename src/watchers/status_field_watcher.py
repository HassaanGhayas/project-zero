"""
Status field watcher for monitoring action file approval/rejection.

This watcher monitors Needs_Action/ folder for YAML status field changes.
When a user edits a file and changes status from 'pending' to 'approved' or 'rejected',
this watcher immediately detects the change and moves the file accordingly:
- status: approved → Move to Approved/
- status: rejected → Move to Rejected/

Real-time response: 1-2 second latency after file save.
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


class StatusFieldWatcher(FileSystemEventHandler):
    """
    Real-time watcher for action file status changes.

    Monitors Needs_Action/ folder and detects when users edit the YAML
    frontmatter status field. Immediately moves files based on new status.

    Attributes:
        vault_path (Path): Root path to the vault
        needs_action_path (Path): Path to Needs_Action/ folder being watched
        approved_path (Path): Path to Approved/ folder
        rejected_path (Path): Path to Rejected/ folder
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
        Initialize the status field watcher.

        Args:
            vault_path: Path to vault root
            logger: Optional logger (creates default if None)
        """
        super().__init__()

        self.vault_path = Path(vault_path)
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.approved_path = self.vault_path / "Approved"
        self.rejected_path = self.vault_path / "Rejected"
        self.logs_path = self.vault_path / "Logs"
        self.logger = logger or setup_logging("status_field_watcher", self.vault_path)

        self.observer: Optional[Observer] = None
        self._action_counter = 0
        self._running = False

        # Track processed files to avoid duplicate processing
        self._processed_files: dict[str, float] = {}  # {filepath: last_mtime}

        # Auto-create directories
        self._ensure_directories_exist()

    def _ensure_directories_exist(self) -> None:
        """Create required directories if they don't exist."""
        required_dirs = [
            self.needs_action_path,
            self.approved_path,
            self.rejected_path,
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
        return f"status_watcher_{self._action_counter:04d}"

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
            action_type: Type of action (status_changed, file_moved, etc.)
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
            "actor": "status_field_watcher",
            "target": target,
            "parameters": parameters or {},
            "approval_status": parameters.get("new_status") if parameters else None,
            "approved_by": "human" if parameters and parameters.get("new_status") == "approved" else None,
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

    def _get_file_mtime(self, file_path: Path) -> float:
        """Get file modification time."""
        return file_path.stat().st_mtime

    def _has_file_changed(self, file_path: Path) -> bool:
        """
        Check if file has been modified since last processing.

        Args:
            file_path: Path to check

        Returns:
            True if file changed, False if already processed
        """
        current_mtime = self._get_file_mtime(file_path)
        file_key = str(file_path)

        # Check if we've seen this file before
        if file_key in self._processed_files:
            last_mtime = self._processed_files[file_key]
            # Only process if modified time is newer
            if current_mtime <= last_mtime:
                return False

        # Update tracking
        self._processed_files[file_key] = current_mtime
        return True

    def _move_file_with_status_update(
        self,
        source_path: Path,
        destination_folder: Path,
        new_status: str
    ) -> None:
        """
        Move file and update its status in YAML frontmatter.

        Args:
            source_path: Source file path
            destination_folder: Target folder (Approved/ or Rejected/)
            new_status: New status value (approved, rejected)
        """
        start_time = time.time()

        try:
            # Read file content
            content = source_path.read_text(encoding="utf-8")

            # Update status in YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml_content = parts[1].strip()
                    frontmatter = yaml.safe_load(yaml_content)

                    # Update status
                    frontmatter["status"] = new_status

                    # Reconstruct file
                    updated_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
                    updated_content = f"---\n{updated_yaml}---\n{parts[2]}"

                    # Write to destination
                    destination_path = destination_folder / source_path.name
                    destination_path.write_text(updated_content, encoding="utf-8")

                    # Delete source
                    source_path.unlink()

                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log successful move
                    self._log_action(
                        action_type="file_moved",
                        target=str(destination_path),
                        parameters={
                            "source": str(source_path),
                            "destination": str(destination_folder),
                            "old_status": "pending",
                            "new_status": new_status,
                        },
                        duration=duration_ms
                    )

                    self.logger.info(
                        f"Moved {source_path.name} → {destination_folder.name}/ "
                        f"(status: {new_status})"
                    )

        except Exception as e:
            self.logger.error(f"Error moving file {source_path.name}: {e}", exc_info=True)
            self._log_action(
                action_type="error_occurred",
                target=str(source_path),
                result="error",
                error=str(e)
            )

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification events (watchdog callback).

        Args:
            event: FileSystemEvent from watchdog

        Process:
            1. Check for emergency stop
            2. Ignore directories
            3. Only process .md files in Needs_Action/
            4. Read YAML frontmatter
            5. Check status field
            6. Move file if status changed to 'approved' or 'rejected'
        """
        # Ignore directory modification events
        if event.is_directory:
            return

        source_path = Path(event.src_path)

        # Only process .md files
        if source_path.suffix != ".md":
            return

        # Only process files in Needs_Action/ folder
        if source_path.parent != self.needs_action_path:
            return

        # Check emergency stop
        if self._check_emergency_stop():
            return

        # Check if file actually changed (avoid duplicate processing)
        if not self._has_file_changed(source_path):
            return

        try:
            # Read YAML frontmatter
            frontmatter = self._read_yaml_frontmatter(source_path)

            if not frontmatter:
                self.logger.debug(f"No valid YAML frontmatter in {source_path.name}")
                return

            # Check status field
            status = frontmatter.get("status")

            if not status:
                return

            # Handle status changes
            if status == "approved":
                self.logger.info(f"Status changed to 'approved': {source_path.name}")
                self._move_file_with_status_update(
                    source_path,
                    self.approved_path,
                    "approved"
                )

            elif status == "rejected":
                self.logger.info(f"Status changed to 'rejected': {source_path.name}")
                self._move_file_with_status_update(
                    source_path,
                    self.rejected_path,
                    "rejected"
                )

        except Exception as e:
            self.logger.error(
                f"Error processing status change for {source_path.name}: {e}",
                exc_info=True
            )
            self._log_action(
                action_type="error_occurred",
                target=str(source_path),
                result="error",
                error=str(e)
            )

    def start(self) -> None:
        """
        Start the status field watcher Observer.

        Sets up watchdog Observer to monitor Needs_Action/ for file modifications.
        """
        if self._running:
            self.logger.warning("Status field watcher is already running")
            return

        self._ensure_directories_exist()

        # Log watcher startup
        self._log_action(
            action_type="watcher_started",
            target=str(self.needs_action_path),
            parameters={"vault_path": str(self.vault_path)}
        )

        # Setup Observer
        self.observer = Observer()
        self.observer.schedule(self, str(self.needs_action_path), recursive=False)
        self.observer.start()

        self._running = True
        self.logger.info(f"Status field watcher started - monitoring: {self.needs_action_path}")

    def stop(self) -> None:
        """
        Stop the status field watcher Observer.

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
            target=str(self.needs_action_path),
            parameters={}
        )

        self.logger.info("Status field watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._running
