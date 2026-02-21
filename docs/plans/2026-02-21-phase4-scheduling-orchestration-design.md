# Phase 4 Design: Scheduling & Orchestration

**Date:** 2026-02-21
**Branch:** 002-gmail-integration
**Status:** Approved

---

## Overview

Phase 4 adds process supervision and cron-based scheduling to the Silver Tier AI FTE. The goal is to keep watchers alive across crashes and run scheduled vault tasks (daily reports, weekly dashboard resets) without manual intervention.

**Approach chosen:** Python subprocess manager + OS cron (no new Python deps).

---

## Architecture

```
Terminal / shell script
  └─► python -m src.monitors.supervisor
           │
           │ subprocess.Popen()
           ▼
      run_all_watchers.py   (6 watchers in daemon threads)
      [FileSystem | Gmail | WhatsApp | StatusField | Approved | LinkedIn]
           │
           │ crash → exit code ≠ 0
           ▼
      supervisor: log crash → exponential backoff → restart

cron (independent):
  0 8 * * *    scripts/cron_vault_report.sh      (daily 8am)
  0 9 * * 1    scripts/cron_dashboard_reset.sh   (weekly Monday 9am)
```

---

## Components

### 1. `src/monitors/__init__.py`

Empty init to make `monitors` a package.

### 2. `src/monitors/supervisor.py` (~120 lines)

Process supervisor that keeps `run_all_watchers.py` alive.

**Responsibilities:**
- Spawns `run_all_watchers.py` via `subprocess.Popen(["uv", "run", "-m", "src.watchers.run_all_watchers"])`
- Monitors exit code:
  - Exit 0 = clean shutdown → supervisor exits
  - Exit ≠ 0 = crash → log + backoff + restart
- Exponential backoff: 5s → 10s → 30s → 60s (cap), resets after 5 min uptime
- **Emergency stop check** before each restart: if `EMERGENCY_STOP.md` exists, abort restart
- Writes `AI_Employee_Vault/supervisor_state.json` on start/restart:
  ```json
  {
    "started_at": "2026-02-21T08:00:00Z",
    "restart_count": 0,
    "last_exit_code": null,
    "backoff_seconds": 5,
    "status": "running"
  }
  ```
- Handles SIGINT/SIGTERM: gracefully terminates child process, cleans up state file, exits

**Backoff table:**

| Restart # | Wait |
|-----------|------|
| 1         | 5s   |
| 2         | 10s  |
| 3         | 30s  |
| 4+        | 60s  |
| After 5min uptime | reset to 5s |

### 3. `config/schedule.yaml` (~20 lines)

Declarative schedule config read by `install_cron.sh`:

```yaml
# Project Zero cron schedule
jobs:
  - name: daily_vault_report
    cron: "0 8 * * *"
    script: scripts/cron_vault_report.sh
    description: "Daily vault status report"

  - name: weekly_dashboard_reset
    cron: "0 9 * * 1"
    script: scripts/cron_dashboard_reset.sh
    description: "Weekly Dashboard.md regeneration"
```

### 4. `scripts/install_cron.sh` (~30 lines)

Idempotent cron installer:
- Reads `config/schedule.yaml` (via Python helper or yq)
- For each job, checks if entry already in `crontab -l`
- Adds missing entries via `(crontab -l; echo "<entry>") | crontab -`
- Prints confirmation per job

### 5. `scripts/uninstall_cron.sh` (~15 lines)

Removes all project cron entries (identified by `# project-zero` comment suffix).

### 6. `scripts/cron_vault_report.sh` (~10 lines)

```bash
#!/bin/bash
cd /path/to/project-zero
source .venv/bin/activate
uv run python -m src.skills.vault_report >> Logs/cron.log 2>&1
```

### 7. `scripts/cron_dashboard_reset.sh` (~10 lines)

Same pattern, calls `update_dashboard` skill module.

### 8. Dashboard health section

Update `update-dashboard` skill to append a "🤖 Process Health" table to `Dashboard.md`:

```markdown
## 🤖 Process Health

| Component     | Status   | Since       | Restarts |
|---------------|----------|-------------|----------|
| Supervisor    | ✅ Up   | 08:02:14    | 0        |
| All watchers  | ✅ Up   | 08:02:15    | 0        |
```

Data source: `AI_Employee_Vault/supervisor_state.json`.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Clean SIGINT/SIGTERM | Propagate to child, exit 0 |
| Child crashes (exit ≠ 0) | Log crash, apply backoff, restart |
| Emergency stop file present | Log halt, do NOT restart |
| Max backoff (60s) reached | Stay at 60s, keep retrying |
| State file write fails | Log warning, continue (non-fatal) |

---

## Testing (`tests/test_supervisor.py`, ~8 tests)

| Test | Description |
|------|-------------|
| `test_clean_exit_stops_supervisor` | Exit 0 → no restart |
| `test_crash_triggers_restart` | Exit 1 → restart after backoff |
| `test_backoff_increases_on_repeated_crashes` | Backoff doubles each crash up to 60s |
| `test_backoff_resets_after_uptime` | 5+ min uptime → backoff resets to 5s |
| `test_emergency_stop_prevents_restart` | EMERGENCY_STOP.md present → no restart |
| `test_state_file_written_on_start` | supervisor_state.json created |
| `test_state_file_restart_count_increments` | restart_count increments on crash |
| `test_sigterm_graceful_shutdown` | SIGTERM → child terminated → supervisor exits |

---

## Files Summary

| Action | File | ~Lines |
|--------|------|--------|
| Create | `src/monitors/__init__.py` | 1 |
| Create | `src/monitors/supervisor.py` | 120 |
| Create | `config/schedule.yaml` | 20 |
| Create | `scripts/install_cron.sh` | 30 |
| Create | `scripts/uninstall_cron.sh` | 15 |
| Create | `scripts/cron_vault_report.sh` | 10 |
| Create | `scripts/cron_dashboard_reset.sh` | 10 |
| Create | `tests/test_supervisor.py` | 120 |
| Modify | `.claude/skills/update-dashboard/SKILL.md` | +10 |
| Create | `docs/SILVER_TIER_SETUP.md` | 80 |

**Total:** 10 files, ~416 lines. No new Python dependencies.

---

## Non-Goals

- HTTP health endpoint (no web framework)
- Process metrics (CPU/memory monitoring)
- Multi-machine coordination
- Alerting via email/Slack (future phase)
