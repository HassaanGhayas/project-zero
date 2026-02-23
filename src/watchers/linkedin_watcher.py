"""
LinkedIn post watcher.

Polls Pending_Approval/ for action files of type 'linkedin_post' with
status 'approved', publishes them via LinkedInServer, moves to Done/,
and appends an audit log entry to Logs/audit.json.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from src.watchers.base_watcher import BaseWatcher

logger = logging.getLogger(__name__)


class LinkedInWatcher(BaseWatcher):
    def __init__(
        self,
        vault_path: str,
        linkedin_server: "LinkedInServer",
        check_interval: int = 60,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(vault_path=vault_path, check_interval=check_interval, logger=logger)
        self.linkedin_server = linkedin_server
        self.pending_dir = self.vault_path / "Pending_Approval"
        self.done_dir = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"

    def create_action_file(self, **kwargs) -> None:
        """Not used by LinkedInWatcher; posts are created externally."""
        pass

    def _is_emergency_stop(self) -> bool:
        return (self.vault_path / "EMERGENCY_STOP.md").exists()

    def check_for_updates(self) -> None:
        if self._is_emergency_stop():
            self.logger.warning("Emergency stop active — LinkedIn watcher halted")
            return
        for action_file in self.pending_dir.glob("FILE_linkedin-*.md"):
            if (self.done_dir / action_file.name).exists():
                self.logger.debug(f"Skipping duplicate: {action_file.name}")
                continue
            self._process_post(action_file)

    def _process_post(self, action_file: Path) -> None:
        try:
            frontmatter, _ = self._parse_action_file(action_file)
        except Exception as e:
            self.logger.error(f"Failed to parse {action_file.name}: {e}")
            return
        if frontmatter.get("type") != "linkedin_post":
            return
        if frontmatter.get("status") != "approved":
            return
        post_text = frontmatter.get("post_text", "")
        self.logger.info(f"Publishing LinkedIn post from {action_file.name}")
        try:
            result = self.linkedin_server.post_text(post_text)
        except Exception as e:
            self.logger.error(f"Failed to publish {action_file.name}: {e}")
            self._log_audit(action_file.name, "linkedin_post_failed", str(e))
            return
        self.logger.info(f"Published: {result.get('id')}")
        action_file.rename(self.done_dir / action_file.name)
        self._log_audit(action_file.name, "linkedin_post_published", result.get("id", ""))

    def _parse_action_file(self, path: Path) -> tuple[dict, str]:
        text = path.read_text()
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}, text
        frontmatter = yaml.safe_load(parts[1]) or {}
        return frontmatter, parts[2]

    def _log_audit(self, filename: str, action: str, detail: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "file": filename,
            "detail": detail,
        }
        log_file = self.logs_dir / "audit.json"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
