#!/usr/bin/env python3
"""
CLI entry point for running the file system watcher.

Usage:
    python src/watchers/run_watcher.py
    python src/watchers/run_watcher.py --vault-path /path/to/vault
    python src/watchers/run_watcher.py --config /path/to/.env

The watcher monitors Inbox/ for file drops and creates action files in Needs_Action/.
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

from .filesystem_watcher import FileSystemWatcher
from .logger_config import setup_logging
from .utils import load_env_config


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI FTE File System Watcher - monitors Inbox/ for file drops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default .env configuration
  python src/watchers/run_watcher.py

  # Run with custom vault path
  python src/watchers/run_watcher.py --vault-path /home/user/AI_Employee_Vault

  # Run with custom config file
  python src/watchers/run_watcher.py --config /path/to/.env

  # Enable debug logging
  python src/watchers/run_watcher.py --debug

Environment Variables (from .env):
  VAULT_PATH            - Path to vault root (required)
  INBOX_WATCH_PATH      - Path to Inbox/ folder (default: VAULT_PATH/Inbox)
  DEV_MODE              - Enable development mode logging (default: false)
        """
    )

    parser.add_argument(
        "--vault-path",
        type=str,
        help="Path to vault root (overrides VAULT_PATH in .env)"
    )

    parser.add_argument(
        "--inbox-path",
        type=str,
        help="Path to Inbox/ folder (overrides INBOX_WATCH_PATH in .env)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="Path to .env configuration file (default: .env)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    return parser.parse_args()


def main() -> int:
    """
    Main entry point for watcher CLI.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    args = parse_args()

    # Load configuration from .env
    try:
        config = load_env_config()
    except Exception as e:
        print(f"❌ Error loading configuration: {e}", file=sys.stderr)
        print("Ensure .env file exists and contains VAULT_PATH", file=sys.stderr)
        return 1

    # Override with command line arguments
    vault_path = args.vault_path or config["vault_path"]
    inbox_path = args.inbox_path or config["inbox_watch_path"]

    if not vault_path:
        print("❌ VAULT_PATH is required (set in .env or use --vault-path)", file=sys.stderr)
        return 1

    # Setup logging
    log_level = logging.DEBUG if (args.debug or config["dev_mode"]) else logging.INFO
    logger = setup_logging(
        "filesystem_watcher",
        vault_path=Path(vault_path),
        level=log_level,
        console_output=True,
        file_output=True
    )

    logger.info("=" * 60)
    logger.info("AI FTE File System Watcher")
    logger.info("=" * 60)
    logger.info(f"Vault path: {vault_path}")
    logger.info(f"Inbox path: {inbox_path}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info("=" * 60)

    # Create and start watcher
    try:
        watcher = FileSystemWatcher(
            vault_path=vault_path,
            inbox_path=inbox_path,
            logger=logger
        )

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
            logger.info(f"Received {signal_name}, shutting down gracefully...")
            watcher.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start watcher
        watcher.start()

        # Keep main thread alive
        try:
            signal.pause()
        except AttributeError:
            # signal.pause() not available on Windows
            import time
            while watcher.is_running():
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        if 'watcher' in locals():
            watcher.stop()
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
