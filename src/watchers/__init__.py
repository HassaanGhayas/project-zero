"""
Watchers package for AI FTE Foundation.

This package contains watcher implementations for detecting events that
require AI processing:
- BaseWatcher: Abstract base class for all watchers
- FileSystemWatcher: Monitors Inbox/ for file drops
- Utils: Helper functions for YAML, logging, config
"""

from .base_watcher import BaseWatcher
from .logger_config import get_logger, setup_logging
from .utils import (
    create_yaml_frontmatter,
    ensure_directory_exists,
    get_iso8601_timestamp,
    load_env_config,
    sanitize_filename,
    write_ndjson_log,
)

__all__ = [
    "BaseWatcher",
    "get_logger",
    "setup_logging",
    "create_yaml_frontmatter",
    "write_ndjson_log",
    "load_env_config",
    "ensure_directory_exists",
    "get_iso8601_timestamp",
    "sanitize_filename",
]