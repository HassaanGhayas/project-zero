"""
Base watcher abstract class for all watcher implementations.

This module provides the foundational BaseWatcher abstract class that defines
the interface all watchers must implement. It handles common concerns like
logging, configuration, and the main run loop.
"""

import logging
import signal
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.

    Attributes:
        check_interval (int): Seconds between checks (for polling watchers)
        vault_path (Path): Path to the AI Employee vault root
        needs_action (Path): Path to Needs_Action/ folder
        logger (logging.Logger): Logger instance for this watcher
        _running (bool): Internal flag to control the main loop
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 5,
        logger: logging.Logger | None = None
    ):
        """
        Initialize the base watcher.

        Args:
            vault_path: Absolute path to the vault root directory
            check_interval: Seconds between checks (default: 5)
            logger: Optional logger instance (creates default if None)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle shutdown signals gracefully.

        Args:
            signum: Signal number received
            frame: Current stack frame
        """
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        self.logger.info(f"Received {signal_name}, shutting down gracefully...")
        self._running = False

    @abstractmethod
    def check_for_updates(self) -> None:
        """
        Check for new items requiring action.

        This method must be implemented by subclasses to define how the watcher
        detects new events (polling, event-driven, API calls, etc.).

        Raises:
            NotImplementedError: If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement check_for_updates()")

    @abstractmethod
    def create_action_file(self, **kwargs: Dict[str, Any]) -> None:
        """
        Create a structured action file in Needs_Action/.

        Args:
            **kwargs: Parameters needed to create the action file
                     (varies by watcher type)

        Raises:
            NotImplementedError: If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement create_action_file()")

    def run(self) -> None:
        """
        Main run loop with error handling.

        Starts the watcher, calls check_for_updates() repeatedly,
        and handles errors gracefully. For event-driven watchers,
        this method may be overridden to use Observer pattern instead.
        """
        self._running = True
        self.logger.info(f"Starting {self.__class__.__name__}")

        try:
            while self._running:
                try:
                    self.check_for_updates()
                except Exception as e:
                    self.logger.error(f"Error in check cycle: {e}", exc_info=True)
                    # Continue running despite errors (constitution Section VIII)

                # For polling watchers, sleep between checks
                # Event-driven watchers should override run() entirely
                if self.check_interval > 0:
                    import time
                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")

        finally:
            self.logger.info(f"Stopped {self.__class__.__name__}")

    def _ensure_directories_exist(self) -> None:
        """
        Auto-create required vault directories if missing (FR-014).

        Creates: Inbox/, Needs_Action/, Logs/
        """
        required_dirs = [
            self.vault_path / "Inbox",
            self.vault_path / "Needs_Action",
            self.vault_path / "Logs"
        ]

        for directory in required_dirs:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created missing directory: {directory}")
