---
id: "0024"
title: Fix backoff_seconds and uninstall cron empty crontab
stage: green
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: fix two bugs in supervisor.py and uninstall_cron.sh
labels: ["fix","supervisor","cron","backoff"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/monitors/supervisor.py
  - scripts/uninstall_cron.sh
tests:
  - tests/test_supervisor.py (8/8 pass)
---

## Prompt

You are fixing two issues in project-zero.

Working directory: /home/hasss/projects/project-zero

---

## Fix 1: `backoff_seconds` emits when status == "running"

File: `src/monitors/supervisor.py`, in `_write_state()` method.

Current line:
```python
"backoff_seconds": self._compute_backoff() if status in ("running", "restarting") else None,
```

Problem: When `status == "running"`, the process just started and no backoff was applied. Emitting `backoff_seconds: 5` when the supervisor is running normally misleads dashboard consumers.

Fix: Only emit `backoff_seconds` when status is `"restarting"`:
```python
"backoff_seconds": self._compute_backoff() if status == "restarting" else None,
```

After this fix, run tests to make sure all 8 still pass:
```bash
uv run pytest tests/test_supervisor.py -v
```

---

## Fix 2: `uninstall_cron.sh` empty-crontab edge case

File: `scripts/uninstall_cron.sh`

Current:
```bash
echo "$FILTERED" | crontab -
REMOVED=$(echo "$CURRENT_CRON" | grep -c "$MARKER" || true)
echo "Removed $REMOVED cron entry/entries."
```

Problem: If `FILTERED` is empty (the crontab ONLY contained project-zero entries), `echo "" | crontab -` installs a blank crontab line rather than removing the crontab entirely.

Fix: After computing `FILTERED`, check if it's empty (after stripping) and if so call `crontab -r` instead.

---

## Response snapshot

Applied Fix 1: changed `status in ("running", "restarting")` to `status == "restarting"` in `_write_state()`.
All 8 supervisor tests passed after the change.

Applied Fix 2: replaced the `else` branch in `uninstall_cron.sh` to compute STRIPPED, and if empty call `crontab -r`; otherwise pipe FILTERED into `crontab -` as before.
Bash syntax check: ok.

Committed both fixes as: `fix: emit backoff_seconds only on restarting, fix uninstall cron empty crontab`
Commit SHA: 5b273ad

## Outcome

- Impact: Prevents misleading `backoff_seconds` value in supervisor state during normal "running" status; prevents a blank crontab line being written when all project-zero entries are removed.
- Tests: 8/8 supervisor tests pass.
- Files: src/monitors/supervisor.py, scripts/uninstall_cron.sh.
- Next prompts: none required; both bugs are resolved.
- Reflection: Both were small, targeted, single-line/branch fixes with zero unrelated changes.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): test_supervisor.py 8/8 PASS; bash -n syntax check PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
