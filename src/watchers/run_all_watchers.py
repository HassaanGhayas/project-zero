"""
Master orchestrator for all AI Employee watchers.

This script runs three watchers simultaneously:
1. Filesystem Watcher - Monitors Inbox/ for new file drops
2. Status Field Watcher - Monitors Needs_Action/ for user approvals/rejections
3. Approved Watcher - Monitors Approved/ for immediate execution

Complete workflow:
  File drops in Inbox/ → Action file created in Needs_Action/ →
  User edits status to 'approved' → File moves to Approved/ →
  Action executed immediately → Confirmation created in In_Progress/ →
  User reviews confirmation → Moves to Done/

Usage:
    uv run -m src.watchers.run_all_watchers

Press Ctrl+C to stop all watchers.
"""

import logging
import signal
import sys
from pathlib import Path

from .approved_watcher import ApprovedWatcher
from .filesystem_watcher import FileSystemWatcher
from .logger_config import setup_logging
from .status_field_watcher import StatusFieldWatcher


def main():
    """
    Start all three watchers and run until interrupted.

    Watchers run in parallel:
    - Filesystem watcher (Inbox/ → Needs_Action/)
    - Status field watcher (Needs_Action/ → Approved/Rejected/)
    - Approved watcher (Approved/ → execute → In_Progress/)
    """
    # Determine vault path (relative to this script)
    # Assuming script is in src/watchers/, vault is at project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    vault_path = project_root / "AI_Employee_Vault"

    # Setup master logger
    logger = setup_logging("orchestrator", vault_path)

    logger.info("=" * 60)
    logger.info("AI Employee Vault - Master Orchestrator")
    logger.info("=" * 60)
    logger.info(f"Vault path: {vault_path}")
    logger.info("")

    # Check vault exists
    if not vault_path.exists():
        logger.error(f"❌ Vault not found at: {vault_path}")
        logger.error("Please ensure AI_Employee_Vault/ directory exists")
        sys.exit(1)

    # Initialize all watchers
    logger.info("Initializing watchers...")

    inbox_path = vault_path / "Inbox"
    needs_action_path = vault_path / "Needs_Action"
    approved_path = vault_path / "Approved"

    # 1. Filesystem Watcher (Inbox → Needs_Action)
    fs_watcher = FileSystemWatcher(
        vault_path=vault_path,
        inbox_path=inbox_path,
        logger=setup_logging("filesystem_watcher", vault_path)
    )

    # 2. Status Field Watcher (Needs_Action → Approved/Rejected)
    status_watcher = StatusFieldWatcher(
        vault_path=vault_path,
        logger=setup_logging("status_field_watcher", vault_path)
    )

    # 3. Approved Watcher (Approved → execute → In_Progress)
    approved_watcher = ApprovedWatcher(
        vault_path=vault_path,
        logger=setup_logging("approved_watcher", vault_path)
    )

    # Setup graceful shutdown
    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""
        logger.info("")
        logger.info("🛑 Shutdown signal received - stopping all watchers...")

        fs_watcher.stop()
        status_watcher.stop()
        approved_watcher.stop()

        logger.info("✅ All watchers stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start all watchers
    try:
        logger.info("")
        logger.info("Starting watchers...")
        logger.info("")

        fs_watcher.start()
        logger.info("✅ Filesystem watcher started (Inbox/ → Needs_Action/)")

        status_watcher.start()
        logger.info("✅ Status field watcher started (Needs_Action/ → Approved/Rejected/)")

        approved_watcher.start()
        logger.info("✅ Approved watcher started (Approved/ → execute → In_Progress/)")

        logger.info("")
        logger.info("=" * 60)
        logger.info("🚀 All watchers running - Real-time AI Employee active")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Workflow:")
        logger.info("  1. Drop file in Inbox/ → Action file created in Needs_Action/")
        logger.info("  2. Edit status: pending → approved → Moves to Approved/")
        logger.info("  3. Action executes immediately → Confirmation in In_Progress/")
        logger.info("  4. Review confirmation → Move to Done/")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("")

        # Keep script running
        signal.pause()

    except Exception as e:
        logger.error(f"❌ Error starting watchers: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
