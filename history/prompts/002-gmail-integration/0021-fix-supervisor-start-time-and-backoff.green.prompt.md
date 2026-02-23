---
id: "0021"
title: Fix Supervisor Start Time and Null Backoff on Clean Exit
stage: green
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: fix two code quality issues in src/monitors/supervisor.py
labels: ["bugfix", "supervisor", "state-file", "backoff"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/monitors/supervisor.py
tests:
  - tests/test_supervisor.py
---

## Prompt

You are fixing two code quality issues in `src/monitors/supervisor.py` in project /home/hasss/projects/project-zero.

## Issues to Fix

**Issue 1 (Important): `started_at` field semantics**

In `_write_state()`, `started_at` is set to `datetime.now(timezone.utc).isoformat()` on every call. This means the state file shows when the state was WRITTEN, not when the supervisor STARTED. The Dashboard health section (coming in Task 7) will display this as "Last Updated" which will confuse operators.

**Fix:** Capture supervisor start time once in `__init__` and use it in `_write_state()`.

In `__init__`, after the other instance variables, add:
```python
self._supervisor_started_at: str = datetime.now(timezone.utc).isoformat()
```

In `_write_state()`, change:
```python
"started_at": datetime.now(timezone.utc).isoformat(),
```
to:
```python
"started_at": self._supervisor_started_at,
```

**Issue 2 (Minor): `backoff_seconds` shows 5 on clean exit**

When status is `"stopped"` (clean exit, no crashes), `backoff_seconds` is written as `BACKOFF_SEQUENCE[0]` (5 seconds), which was never actually used. It's misleading.

**Fix:** In `_write_state()`, change:
```python
"backoff_seconds": self._compute_backoff(),
```
to:
```python
"backoff_seconds": self._compute_backoff() if status in ("running", "restarting") else None,
```

## Steps

1. Read `src/monitors/supervisor.py` to see current content
2. Apply both fixes
3. Run `uv run pytest tests/test_supervisor.py -v` — all 8 must still pass
4. Also update the state file assertions in tests if needed (check if `test_state_file_written_on_start` asserts on `backoff_seconds`)
5. Commit: `fix: use fixed supervisor start time and null backoff on clean exit`
6. Report back with test results and git SHA

## Response snapshot

Both fixes applied to `src/monitors/supervisor.py`:

1. Added `self._supervisor_started_at: str = datetime.now(timezone.utc).isoformat()` in `__init__` after `self._start_time`.
2. Changed `_write_state()` to use `self._supervisor_started_at` for `started_at`.
3. Changed `backoff_seconds` to be `None` when `status` is not `"running"` or `"restarting"`.

No test changes were needed — `test_state_file_written_on_start` did not assert on `backoff_seconds`.

All 8 tests passed. Commit SHA: `7717cc5`.

## Outcome

- Impact: State file now accurately reflects when the supervisor process started (not last write time); backoff_seconds is null on clean exit / emergency stop, eliminating misleading data for the upcoming Dashboard health section.
- Tests: 8/8 passed — no regressions.
- Files: src/monitors/supervisor.py (3 insertions, 2 deletions).
- Next prompts: Task 7 — update update-dashboard skill to use supervisor_state.json fields including started_at.
- Reflection: Both fixes were low-risk, surgically minimal, and required no test changes. The guard `status in ("running", "restarting")` correctly covers the halted case as well.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): pytest tests/test_supervisor.py — 8 PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): add a test that explicitly asserts `backoff_seconds is None` in the stopped/halted state for regression coverage
