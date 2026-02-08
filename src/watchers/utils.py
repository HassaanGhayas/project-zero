"""
Utility functions for watcher implementations.

This module provides helper functions for common tasks:
- YAML frontmatter generation
- NDJSON log file writing
- Environment configuration loading
- Directory management
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


def create_yaml_frontmatter(fields: Dict[str, Any]) -> str:
    """
    Generate YAML frontmatter for markdown files.

    Args:
        fields: Dictionary of field names and values

    Returns:
        YAML frontmatter as string with triple-dash delimiters

    Example:
        >>> fields = {"type": "document", "status": "pending"}
        >>> print(create_yaml_frontmatter(fields))
        ---
        type: document
        status: pending
        ---
    """
    lines = ["---"]
    for key, value in fields.items():
        # Handle different value types
        if isinstance(value, str):
            lines.append(f"{key}: {value}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def write_ndjson_log(log_path: Path, entry: Dict[str, Any]) -> None:
    """
    Append a log entry to an NDJSON file (append-only).

    Args:
        log_path: Path to the log file (will be created if missing)
        entry: Dictionary to serialize as JSON

    Note:
        Uses append mode ('a') to maintain append-only log structure.
        Each entry is written as a single line.
    """
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Append entry as single line
    with open(log_path, "a", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
        f.write("\n")


def load_env_config() -> Dict[str, Any]:
    """
    Load configuration from .env file.

    Returns:
        Dictionary with configuration values

    Environment Variables:
        VAULT_PATH: Absolute path to vault root
        INBOX_WATCH_PATH: Path to Inbox folder
        WATCHER_CHECK_INTERVAL: Seconds between checks (default: 5)
        DRY_RUN: Enable dry-run mode (default: false)
        DEV_MODE: Enable development mode logging (default: false)
    """
    load_dotenv()

    config = {
        "vault_path": os.getenv("VAULT_PATH"),
        "inbox_watch_path": os.getenv("INBOX_WATCH_PATH"),
        "check_interval": int(os.getenv("WATCHER_CHECK_INTERVAL", "5")),
        "dry_run": os.getenv("DRY_RUN", "false").lower() == "true",
        "dev_mode": os.getenv("DEV_MODE", "false").lower() == "true",
    }

    # Validate required fields
    if not config["vault_path"]:
        raise ValueError("VAULT_PATH environment variable is required")

    if not config["inbox_watch_path"]:
        # Default to vault_path/Inbox if not specified
        config["inbox_watch_path"] = str(Path(config["vault_path"]) / "Inbox")

    return config


def ensure_directory_exists(path: Path) -> None:
    """
    Create directory if it doesn't exist (FR-014 auto-create).

    Args:
        path: Directory path to create

    Note:
        Uses parents=True to create intermediate directories.
        Uses exist_ok=True to avoid errors if directory exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def get_iso8601_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format with UTC timezone.

    Returns:
        Timestamp string (e.g., "2026-02-07T15:30:00Z")

    Note:
        Always uses UTC timezone (Z suffix) for consistency.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for use in action file names.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem use

    Example:
        >>> sanitize_filename("My Document (2024).pdf")
        'My_Document_2024.pdf'
    """
    # Replace problematic characters with underscores
    for char in [" ", "(", ")", "[", "]", "{", "}", "'", '"']:
        filename = filename.replace(char, "_")

    # Remove consecutive underscores
    while "__" in filename:
        filename = filename.replace("__", "_")

    return filename
