---
id: "0020"
title: Implement supervisor process monitor
stage: green
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: implement supervisor.py (Task 3, Phase 4)
labels: ["supervisor","phase4","tdd","green","exponential-backoff","process-management"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/monitors/supervisor.py
tests:
  - tests/test_supervisor.py::test_clean_exit_stops_supervisor
  - tests/test_supervisor.py::test_crash_triggers_restart
  - tests/test_supervisor.py::test_backoff_increases_on_repeated_crashes
  - tests/test_supervisor.py::test_backoff_caps_at_max
  - tests/test_supervisor.py::test_backoff_resets_after_long_uptime
  - tests/test_supervisor.py::test_emergency_stop_prevents_restart
  - tests/test_supervisor.py::test_state_file_written_on_start
  - tests/test_supervisor.py::test_state_restart_count_increments
---

## Prompt

You are implementing Task 3: Implement supervisor.py

**Files:**
- Create: `src/monitors/supervisor.py`
- Test: `tests/test_supervisor.py` (already written — must all pass)

**Step 1: Write the implementation**

Create `src/monitors/supervisor.py` with the Supervisor class that:
- Keeps run_all_watchers.py alive across crashes using exponential backoff
- Checks EMERGENCY_STOP.md before every spawn
- Writes supervisor_state.json after each state transition
- Handles SIGINT/SIGTERM gracefully
- Resets backoff after long uptime (>=300s)
- Caps backoff at 60s maximum

**Step 2: Run tests — expect all 8 to pass**

```bash
uv run pytest tests/test_supervisor.py -v
```

**Step 3: Commit**

```bash
git add src/monitors/supervisor.py
git commit -m "feat: add process supervisor with exponential backoff"
```

## Response snapshot

Created `src/monitors/supervisor.py` with the Supervisor class implementing:
- BACKOFF_SEQUENCE = [5, 10, 30, 60] seconds
- BACKOFF_RESET_UPTIME = 300 seconds
- Emergency stop check before every Popen call
- State file writes on running/restarting/stopped/halted transitions
- Signal handler for SIGINT/SIGTERM with graceful subprocess termination

A bug was identified during the TDD green phase: the initial implementation set
`self._start_time` inside `_spawn()`, which overwrote any `patch.object` value
set on the instance before `run()` was called. The fix captures the current
`_start_time` into a local variable at the top of the loop iteration (before
`_spawn()` overwrites it), so the uptime calculation after process exit uses the
correct pre-spawn value that the test controls via `patch.object`.

All 8 tests pass. Commit SHA: cea2f24.

## Outcome

- Impact: Phase 4 Task 3 complete — Supervisor process manager implemented and tested; 8/8 tests passing.
- Tests: 8 passed, 0 failed — uv run pytest tests/test_supervisor.py -v
- Files: src/monitors/supervisor.py created (135 lines)
- Next prompts: Task 4 (schedule config), Task 5 (cron wrapper scripts), Task 6 (install/uninstall scripts)
- Reflection: The `patch.object` interaction with instance attribute assignment in `_spawn()` required capturing `_start_time` before spawn rather than reading it after — a subtle TDD learning about how unittest.mock patches interact with reassigned instance attributes.

## Evaluation notes (flywheel)

- Failure modes observed: Initial implementation set _start_time in _spawn(), which overwrote the patch.object value — uptime was always ~0 instead of the mocked long_ago value.
- Graders run and results (PASS/FAIL): uv run pytest tests/test_supervisor.py -v → 8 PASSED after fix
- Prompt variant (if applicable): null
- Next experiment: Consider using a property or explicit setter for _start_time to make patching more predictable in future supervisor-like classes.
