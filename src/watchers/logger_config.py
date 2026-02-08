"""
Logging configuration for watcher components.

This module provides structured logging setup with both console and file handlers.
All watchers and skills should use this configuration for consistent log formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    name: str,
    vault_path: Optional[Path] = None,
    level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = False
) -> logging.Logger:
    """
    Configure logging with console and optional file handlers.

    Args:
        name: Logger name (typically __name__ or watcher class name)
        vault_path: Path to vault root (for file logging)
        level: Logging level (default: INFO)
        console_output: Enable console handler (default: True)
        file_output: Enable file handler (default: False)

    Returns:
        Configured logger instance

    Example:
        >>> from pathlib import Path
        >>> logger = setup_logging(
        ...     "filesystem_watcher",
        ...     vault_path=Path("/home/user/vault"),
        ...     level=logging.DEBUG
        ... )
        >>> logger.info("Watcher started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stdout)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler (optional, for watcher process logs)
    if file_output and vault_path:
        log_dir = vault_path / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{name}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a pre-configured logger (simpler interface).

    Args:
        name: Logger name
        level: Logging level (default: INFO)

    Returns:
        Logger instance with console output only

    Example:
        >>> logger = get_logger("my_module")
        >>> logger.info("Starting operation")
    """
    return setup_logging(name, level=level, console_output=True, file_output=False)
