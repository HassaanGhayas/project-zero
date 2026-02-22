# Phase 4: Scheduling & Orchestration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Python subprocess supervisor that keeps watchers alive across crashes, cron-based scheduling for recurring vault tasks, and a health status section in Dashboard.md.

**Architecture:** A `Supervisor` class spawns `run_all_watchers.py` as a subprocess, monitors its exit code, and restarts it with exponential backoff on crash. Scheduled tasks (daily vault report, weekly dashboard reset) are installed as crontab entries via `scripts/install_cron.sh`, which reads `config/schedule.yaml`. Health data is written to `AI_Employee_Vault/supervisor_state.json` and surfaced in Dashboard.md.

**Tech Stack:** Python 3.12+, subprocess, signal, pathlib, PyYAML (already in deps), uv, bash cron.

---

## Task 1: Create monitors package

**Files:**
- Create: `src/monitors/__init__.py`

**Step 1: Create the package init**

```python
# src/monitors/__init__.py
```

(Empty file — just makes `src/monitors` a Python package.)

**Step 2: Verify import works**

```bash
uv run python -c "import src.monitors; print('ok')"
```

Expected: `ok`

**Step 3: Commit**

```bash
git add src/monitors/__init__.py
git commit -m "feat: add monitors package"
```

---

## Task 2: Write failing supervisor tests

**Files:**
- Create: `tests/test_supervisor.py`
- Test: `tests/test_supervisor.py`

**Step 1: Write the tests**

```python
# tests/test_supervisor.py
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.monitors.supervisor import BACKOFF_RESET_UPTIME, BACKOFF_SEQUENCE, Supervisor


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    v.mkdir()
    return v


@pytest.fixture
def sup(vault: Path) -> Supervisor:
    return Supervisor(vault_path=vault, watcher_cmd=["echo", "hello"])


def _proc(exit_code: int) -> MagicMock:
    p = MagicMock()
    p.returncode = exit_code
    p.wait.return_value = exit_code
    p.poll.return_value = None
    return p


# --- clean exit ---

def test_clean_exit_stops_supervisor(sup: Supervisor) -> None:
    with patch("subprocess.Popen", return_value=_proc(0)):
        sup.run()
    assert sup.restart_count == 0


# --- crash + restart ---

def test_crash_triggers_restart(sup: Supervisor) -> None:
    procs = [_proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[idx["n"]]
        idx["n"] += 1
        return p

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep"):
            sup.run()

    assert sup.restart_count == 1


def test_backoff_increases_on_repeated_crashes(sup: Supervisor) -> None:
    procs = [_proc(1), _proc(1), _proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    sleeps: list[float] = []

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep", side_effect=lambda s: sleeps.append(s)):
            sup.run()

    assert sleeps == [BACKOFF_SEQUENCE[0], BACKOFF_SEQUENCE[1], BACKOFF_SEQUENCE[2]]


def test_backoff_caps_at_max(sup: Supervisor) -> None:
    # 5 crashes → backoff should cap at BACKOFF_SEQUENCE[-1]
    procs = [_proc(1)] * 5 + [_proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    sleeps: list[float] = []

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep", side_effect=lambda s: sleeps.append(s)):
            sup.run()

    assert sleeps[-1] == BACKOFF_SEQUENCE[-1]


def test_backoff_resets_after_long_uptime(sup: Supervisor) -> None:
    # After a long-running process, backoff_index resets → first sleep = BACKOFF_SEQUENCE[0]
    sup.backoff_index = 3  # pre-set to max
    procs = [_proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    sleeps: list[float] = []
    # Fake start_time so uptime > BACKOFF_RESET_UPTIME
    long_ago = time.monotonic() - (BACKOFF_RESET_UPTIME + 10)

    def fake_monotonic():
        return time.monotonic()

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep", side_effect=lambda s: sleeps.append(s)):
            with patch.object(sup, "_start_time", long_ago):
                sup.run()

    assert sleeps[0] == BACKOFF_SEQUENCE[0]


# --- emergency stop ---

def test_emergency_stop_prevents_restart(vault: Path, sup: Supervisor) -> None:
    (vault / "EMERGENCY_STOP.md").touch()
    with patch("subprocess.Popen") as mock_popen:
        sup.run()
    mock_popen.assert_not_called()


# --- state file ---

def test_state_file_written_on_start(vault: Path, sup: Supervisor) -> None:
    with patch("subprocess.Popen", return_value=_proc(0)):
        sup.run()
    state_file = vault / "supervisor_state.json"
    assert state_file.exists()
    state = json.loads(state_file.read_text())
    assert state["restart_count"] == 0
    assert state["status"] == "stopped"


def test_state_restart_count_increments(vault: Path, sup: Supervisor) -> None:
    procs = [_proc(1), _proc(1), _proc(0)]
    idx = {"n": 0}

    def side(*a, **kw):
        p = procs[min(idx["n"], len(procs) - 1)]
        idx["n"] += 1
        return p

    with patch("subprocess.Popen", side_effect=side):
        with patch("time.sleep"):
            sup.run()

    state = json.loads((vault / "supervisor_state.json").read_text())
    assert state["restart_count"] == 2
```

**Step 2: Run tests to confirm they all fail**

```bash
uv run pytest tests/test_supervisor.py -v
```

Expected: `ImportError: cannot import name 'Supervisor' from 'src.monitors.supervisor'` (module doesn't exist yet).

**Step 3: Commit**

```bash
git add tests/test_supervisor.py
git commit -m "test: add failing supervisor tests"
```

---

## Task 3: Implement supervisor.py

**Files:**
- Create: `src/monitors/supervisor.py`
- Test: `tests/test_supervisor.py`

**Step 1: Write the implementation**

```python
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

            self._proc = self._spawn()
            self._write_state(status="running")
            exit_code = self._proc.wait()

            if exit_code == 0:
                logger.info("Watchers exited cleanly (0)")
                self._write_state(status="stopped")
                break

            # Crash path
            uptime = time.monotonic() - (self._start_time or 0)
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
```

**Step 2: Run tests — expect all pass**

```bash
uv run pytest tests/test_supervisor.py -v
```

Expected: All 8 tests `PASSED`.

**Step 3: Commit**

```bash
git add src/monitors/supervisor.py
git commit -m "feat: add process supervisor with exponential backoff"
```

---

## Task 4: Create schedule config

**Files:**
- Create: `config/schedule.yaml`

**Step 1: Write the config**

```yaml
# config/schedule.yaml
# Project Zero cron schedule.
# Read by scripts/install_cron.sh to generate crontab entries.

jobs:
  - name: daily_vault_report
    cron: "0 8 * * *"
    script: scripts/cron_vault_report.sh
    description: "Daily vault status report (8am)"

  - name: weekly_dashboard_reset
    cron: "0 9 * * 1"
    script: scripts/cron_dashboard_reset.sh
    description: "Weekly Dashboard.md regeneration (Monday 9am)"
```

**Step 2: Verify YAML parses**

```bash
uv run python -c "import yaml; d=yaml.safe_load(open('config/schedule.yaml')); print([j['name'] for j in d['jobs']])"
```

Expected: `['daily_vault_report', 'weekly_dashboard_reset']`

**Step 3: Commit**

```bash
git add config/schedule.yaml
git commit -m "feat: add cron schedule config"
```

---

## Task 5: Create cron wrapper scripts

**Files:**
- Create: `scripts/cron_vault_report.sh`
- Create: `scripts/cron_dashboard_reset.sh`

**Step 1: Create vault report wrapper**

```bash
#!/usr/bin/env bash
# scripts/cron_vault_report.sh
# Runs daily vault report via cron. Logs output to Logs/cron.log.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/AI_Employee_Vault/Logs/cron.log"

mkdir -p "$(dirname "$LOG_FILE")"

{
  echo "--- $(date -u +%Y-%m-%dT%H:%M:%SZ) vault_report ---"
  cd "$PROJECT_ROOT"
  uv run python -m src.skills.vault_report
} >> "$LOG_FILE" 2>&1
```

**Step 2: Create dashboard reset wrapper**

```bash
#!/usr/bin/env bash
# scripts/cron_dashboard_reset.sh
# Runs weekly dashboard regeneration via cron. Logs output to Logs/cron.log.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/AI_Employee_Vault/Logs/cron.log"

mkdir -p "$(dirname "$LOG_FILE")"

{
  echo "--- $(date -u +%Y-%m-%dT%H:%M:%SZ) dashboard_reset ---"
  cd "$PROJECT_ROOT"
  uv run python -m src.skills.update_dashboard
} >> "$LOG_FILE" 2>&1
```

**Step 3: Make them executable**

```bash
chmod +x scripts/cron_vault_report.sh scripts/cron_dashboard_reset.sh
```

**Step 4: Verify they parse (not execute)**

```bash
bash -n scripts/cron_vault_report.sh && echo "ok"
bash -n scripts/cron_dashboard_reset.sh && echo "ok"
```

Expected: `ok` for both.

**Step 5: Commit**

```bash
git add scripts/cron_vault_report.sh scripts/cron_dashboard_reset.sh
git commit -m "feat: add cron wrapper scripts for vault report and dashboard"
```

---

## Task 6: Create install/uninstall cron scripts

**Files:**
- Create: `scripts/install_cron.sh`
- Create: `scripts/uninstall_cron.sh`

**Step 1: Write install script**

```bash
#!/usr/bin/env bash
# scripts/install_cron.sh
# Installs cron jobs from config/schedule.yaml. Idempotent.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCHEDULE_CONFIG="$PROJECT_ROOT/config/schedule.yaml"
MARKER="# project-zero"

if ! command -v python3 &>/dev/null && ! command -v uv &>/dev/null; then
  echo "ERROR: python3 or uv required" >&2
  exit 1
fi

# Parse schedule.yaml and emit cron lines using Python
CRON_LINES=$(cd "$PROJECT_ROOT" && uv run python3 - <<'PYEOF'
import yaml, sys
config = yaml.safe_load(open("config/schedule.yaml"))
for job in config["jobs"]:
    script = f"{job['script']}"
    print(f"{job['cron']} cd $PROJECT_ROOT && bash $PROJECT_ROOT/{script} # project-zero:{job['name']}")
PYEOF
)

# Replace PROJECT_ROOT placeholder
CRON_LINES="${CRON_LINES//\$PROJECT_ROOT/$PROJECT_ROOT}"

# Current crontab (ignore error if empty)
CURRENT_CRON=$(crontab -l 2>/dev/null || true)

ADDED=0
while IFS= read -r line; do
  JOB_NAME=$(echo "$line" | grep -oP '(?<=project-zero:)\S+' || true)
  if echo "$CURRENT_CRON" | grep -qF "project-zero:$JOB_NAME"; then
    echo "  [skip] $JOB_NAME already installed"
  else
    CURRENT_CRON="${CURRENT_CRON}"$'\n'"${line}"
    echo "  [add]  $JOB_NAME"
    ADDED=$((ADDED + 1))
  fi
done <<< "$CRON_LINES"

if [ "$ADDED" -gt 0 ]; then
  echo "$CURRENT_CRON" | crontab -
  echo "Installed $ADDED job(s)."
else
  echo "All jobs already installed — nothing changed."
fi
```

**Step 2: Write uninstall script**

```bash
#!/usr/bin/env bash
# scripts/uninstall_cron.sh
# Removes all project-zero cron entries. Idempotent.
set -euo pipefail

MARKER="project-zero"
CURRENT_CRON=$(crontab -l 2>/dev/null || true)
FILTERED=$(echo "$CURRENT_CRON" | grep -v "$MARKER" || true)

if [ "$CURRENT_CRON" = "$FILTERED" ]; then
  echo "No project-zero cron entries found — nothing to remove."
else
  echo "$FILTERED" | crontab -
  REMOVED=$(echo "$CURRENT_CRON" | grep -c "$MARKER" || true)
  echo "Removed $REMOVED cron entry/entries."
fi
```

**Step 3: Make executable**

```bash
chmod +x scripts/install_cron.sh scripts/uninstall_cron.sh
```

**Step 4: Verify syntax**

```bash
bash -n scripts/install_cron.sh && echo "install ok"
bash -n scripts/uninstall_cron.sh && echo "uninstall ok"
```

Expected: `install ok` and `uninstall ok`.

**Step 5: Commit**

```bash
git add scripts/install_cron.sh scripts/uninstall_cron.sh
git commit -m "feat: add install/uninstall cron scripts"
```

---

## Task 7: Update update-dashboard skill for health section

**Files:**
- Modify: `.claude/skills/update-dashboard/SKILL.md`

**Step 1: Read current skill**

Open `.claude/skills/update-dashboard/SKILL.md` and find the section where Dashboard.md sections are built.

**Step 2: Add health section instruction**

Locate the section describing what to include in Dashboard.md and add after the existing sections:

```markdown
## 🤖 Process Health

Read `AI_Employee_Vault/supervisor_state.json` if it exists.
If it exists, append this table to Dashboard.md:

```markdown
## 🤖 Process Health

| Component    | Status           | Restarts | Last Updated        |
|--------------|------------------|----------|---------------------|
| Supervisor   | {status emoji}   | {restart_count} | {started_at} |
```

Status emoji mapping:
- `running` → ✅ Running
- `restarting` → 🔄 Restarting
- `halted` → 🚨 HALTED (emergency stop)
- `stopped` → ⏹ Stopped

If `supervisor_state.json` does not exist, skip this section entirely.
```

**Step 3: Run tests to confirm no regressions**

```bash
uv run pytest tests/ -v -k "dashboard" 2>/dev/null || echo "no dashboard tests"
```

**Step 4: Commit**

```bash
git add .claude/skills/update-dashboard/SKILL.md
git commit -m "feat: add process health section to update-dashboard skill"
```

---

## Task 8: Create Silver Tier setup docs

**Files:**
- Create: `docs/SILVER_TIER_SETUP.md`

**Step 1: Write the doc**

```markdown
# Silver Tier Setup Guide

This guide covers setting up the Silver Tier AI FTE: Gmail integration, LinkedIn integration,
plan generation, and scheduling & orchestration.

## Prerequisites

- Bronze Tier complete (see `docs/SETUP.md`)
- `.env` configured with all required keys (see `.env.example`)
- `uv sync --all-extras` completed

## 1. Gmail Integration

1. Run OAuth flow: `uv run python src/api/gmail_oauth.py`
2. Token saved to `config/gmail_token.json`
3. Set `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in `.env`

## 2. LinkedIn Integration

See `docs/LINKEDIN_SETUP.md` for full OAuth2 flow.

Quick start:
```bash
uv run python src/api/linkedin_oauth.py
```

## 3. Starting Watchers

**With supervisor (recommended — auto-restarts on crash):**
```bash
uv run python -m src.monitors.supervisor
```

**Without supervisor (manual restart):**
```bash
uv run python -m src.watchers.run_all_watchers
```

## 4. Installing Scheduled Tasks

Install cron jobs for daily vault reports and weekly dashboard resets:

```bash
bash scripts/install_cron.sh
```

Verify installation:
```bash
crontab -l | grep project-zero
```

Remove all scheduled tasks:
```bash
bash scripts/uninstall_cron.sh
```

## 5. Schedule Configuration

Edit `config/schedule.yaml` to change timing or add jobs, then re-run `install_cron.sh`.

## 6. Emergency Stop

Touch the emergency stop file to halt all watchers and the supervisor:

```bash
touch AI_Employee_Vault/EMERGENCY_STOP.md
```

Remove it to allow restart:

```bash
rm AI_Employee_Vault/EMERGENCY_STOP.md
uv run python -m src.monitors.supervisor
```

## 7. Health Monitoring

The supervisor writes `AI_Employee_Vault/supervisor_state.json` continuously.
The Dashboard.md includes a "🤖 Process Health" section when this file exists.

Refresh the dashboard:

```bash
# Run the update-dashboard skill via Claude Code
```

## 8. Running Tests

```bash
uv run pytest tests/ -v
```
```

**Step 2: Commit**

```bash
git add docs/SILVER_TIER_SETUP.md
git commit -m "docs: add Silver Tier setup guide"
```

---

## Final Verification

**Step 1: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: All tests pass including the 8 new supervisor tests.

**Step 2: Smoke test supervisor import**

```bash
uv run python -c "from src.monitors.supervisor import Supervisor; print('Supervisor ok')"
```

Expected: `Supervisor ok`

**Step 3: Verify cron script syntax**

```bash
bash -n scripts/install_cron.sh && bash -n scripts/uninstall_cron.sh && echo "scripts ok"
```

Expected: `scripts ok`

**Step 4: Verify schedule config**

```bash
uv run python -c "import yaml; d=yaml.safe_load(open('config/schedule.yaml')); print(len(d['jobs']), 'jobs')"
```

Expected: `2 jobs`
