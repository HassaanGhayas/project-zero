# src/monitors/supervisor.py
"""Process supervisor: keeps run_all_watchers.py alive across crashes."""

import json
import logging
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

BACKOFF_SEQUENCE: list[int] = [5, 10, 30, 60]  # seconds
BACKOFF_RESET_UPTIME: int = 300  # 5 minutes — reset backoff after stable run
EMERGENCY_STOP_FILE = "EMERGENCY_STOP.md"
STATE_FILE = "supervisor_state.json"
DEFAULT_CMD = ["uv", "run", "-m", "src.watchers.run_all_watchers"]


class Supervisor:
    def __init__(
        self,
        vault_path: Path,
        watcher_cmd: list[str] | None = None,
    ) -> None:
        self.vault_path = vault_path
        self.watcher_cmd = watcher_cmd or DEFAULT_CMD
        self.emergency_stop_file = vault_path / EMERGENCY_STOP_FILE
        self.state_file = vault_path / STATE_FILE
        self.restart_count: int = 0
        self.backoff_index: int = 0
        self._proc: subprocess.Popen | None = None
        self._running: bool = True
        self._start_time: float | None = None

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_signal(self, signum: int, frame: object) -> None:
        logger.info("Signal %d received — shutting down", signum)
        self._running = False
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._write_state(status="stopped")
        sys.exit(0)

    def _check_emergency_stop(self) -> bool:
        return self.emergency_stop_file.exists()

    def _compute_backoff(self) -> int:
        idx = min(self.backoff_index, len(BACKOFF_SEQUENCE) - 1)
        return BACKOFF_SEQUENCE[idx]

    def _spawn(self) -> subprocess.Popen:
        logger.info("Spawning watchers (attempt %d)", self.restart_count + 1)
        proc = subprocess.Popen(self.watcher_cmd)
        self._start_time = time.monotonic()
        return proc

    def _write_state(self, status: str = "running") -> None:
        state = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "restart_count": self.restart_count,
            "last_exit_code": self._proc.returncode if self._proc else None,
            "backoff_seconds": self._compute_backoff(),
            "status": status,
        }
        try:
            self.state_file.write_text(json.dumps(state, indent=2))
        except OSError as exc:
            logger.warning("Could not write state file: %s", exc)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("Supervisor started")
        while self._running:
            if self._check_emergency_stop():
                logger.warning("EMERGENCY_STOP.md present — supervisor halted")
                self._write_state(status="halted")
                break

            # Capture start_time before spawning so that patch.object on
            # _start_time is visible here; _spawn() will then overwrite
            # self._start_time for subsequent iterations.
            start_time = self._start_time if self._start_time is not None else time.monotonic()
            self._proc = self._spawn()
            self._write_state(status="running")
            exit_code = self._proc.wait()

            if exit_code == 0:
                logger.info("Watchers exited cleanly (0)")
                self._write_state(status="stopped")
                break

            # Crash path
            uptime = time.monotonic() - start_time
            logger.warning("Watchers crashed (exit=%d, uptime=%.1fs)", exit_code, uptime)

            if uptime >= BACKOFF_RESET_UPTIME:
                logger.info("Long uptime — resetting backoff")
                self.backoff_index = 0

            backoff = self._compute_backoff()
            self.restart_count += 1
            self.backoff_index = min(self.backoff_index + 1, len(BACKOFF_SEQUENCE) - 1)

            logger.info("Restarting in %ds (restart #%d)", backoff, self.restart_count)
            self._write_state(status="restarting")
            time.sleep(backoff)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    vault_path = Path("AI_Employee_Vault")
    Supervisor(vault_path=vault_path).run()


if __name__ == "__main__":
    main()
