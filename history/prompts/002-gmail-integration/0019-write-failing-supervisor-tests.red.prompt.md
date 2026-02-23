---
id: "0019"
title: Write failing supervisor tests
stage: red
date: 2026-02-22
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: task-impl
labels: ["tdd", "supervisor", "phase4", "red-phase", "tests"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - tests/test_supervisor.py
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

You are implementing Task 2: Write failing supervisor tests

## Task Description

**Files:**
- Create: `tests/test_supervisor.py`

**Step 1: Write the tests** — create `tests/test_supervisor.py` with this exact content: [8 tests covering Supervisor class]

**Step 2: Run tests to confirm they all fail**

Expected: ImportError or ModuleNotFoundError because `src/monitors/supervisor.py` doesn't exist yet.

**Step 3: Commit**

## Context

Project: project-zero, branch 002-gmail-integration.
Phase 4, Task 2. TDD red phase — write tests FIRST before implementation.
`src/monitors/__init__.py` already exists (from Task 1, commit 2db723a).
`src/monitors/supervisor.py` does NOT exist yet — tests MUST fail at this point.

## Response snapshot

Created `tests/test_supervisor.py` with 8 tests covering:
- `test_clean_exit_stops_supervisor` — exit code 0 → no restart
- `test_crash_triggers_restart` — exit code 1 → one restart
- `test_backoff_increases_on_repeated_crashes` — sleeps follow BACKOFF_SEQUENCE[0..2]
- `test_backoff_caps_at_max` — 5 crashes → last sleep = BACKOFF_SEQUENCE[-1]
- `test_backoff_resets_after_long_uptime` — pre-set backoff_index=3, long uptime → first sleep resets to BACKOFF_SEQUENCE[0]
- `test_emergency_stop_prevents_restart` — EMERGENCY_STOP.md present → Popen never called
- `test_state_file_written_on_start` — supervisor_state.json written with restart_count=0, status=stopped
- `test_state_restart_count_increments` — 2 crashes → state file shows restart_count=2

Test run confirmed failure mode:
```
ModuleNotFoundError: No module named 'src.monitors.supervisor'
```

Committed as: `8cd1007 test: add failing supervisor tests`

## Outcome

- Impact: TDD red phase complete — 8 failing tests define the Supervisor contract before any implementation exists
- Tests: All 8 fail with ModuleNotFoundError (expected; src/monitors/supervisor.py does not exist)
- Files: tests/test_supervisor.py created (156 lines)
- Next prompts: Task 3 — implement `src/monitors/supervisor.py` to make tests pass (green phase)
- Reflection: Tests cover the full Supervisor surface: happy path, crash recovery, exponential backoff with cap, backoff reset, emergency stop guard, and state persistence. The patch.object approach for `_start_time` cleanly simulates long uptime without real sleeps.

## Evaluation notes (flywheel)

- Failure modes observed: none — file written exactly as specified, tests fail with correct error
- Graders run and results (PASS/FAIL): pytest collection error = PASS (red phase confirmed)
- Prompt variant (if applicable): task-impl v1
- Next experiment: implement Supervisor class and run green phase
