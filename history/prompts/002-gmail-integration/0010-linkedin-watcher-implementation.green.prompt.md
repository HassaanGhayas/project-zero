---
id: "0010"
title: LinkedIn Watcher Implementation
stage: green
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: 002-gmail-integration
branch: 002-gmail-integration
user: hasss
command: implement Task 3 LinkedIn Watcher
labels: ["linkedin", "watcher", "tdd", "audit-log", "emergency-stop"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - src/watchers/linkedin_watcher.py
  - tests/test_linkedin_watcher.py
tests:
  - tests/test_linkedin_watcher.py::test_processes_approved_post
  - tests/test_linkedin_watcher.py::test_skips_pending_post
  - tests/test_linkedin_watcher.py::test_skips_non_linkedin_files
  - tests/test_linkedin_watcher.py::test_emergency_stop_blocks_posting
  - tests/test_linkedin_watcher.py::test_no_duplicate_post_if_in_done
  - tests/test_linkedin_watcher.py::test_api_error_leaves_file_in_pending
  - tests/test_linkedin_watcher.py::test_audit_log_written_on_success
---

## Prompt

You are implementing Task 3: LinkedIn Watcher

Files:
- Create: `src/watchers/linkedin_watcher.py`
- Test: `tests/test_linkedin_watcher.py`

Step 1: Write the failing tests (already present in repo)
Step 2: Run test to verify it fails
Step 3: Check the BaseWatcher signature first
Step 4: Write implementation
Step 5: Run tests (expected: 7 PASSED)
Step 6: Commit

## Response snapshot

Implemented `LinkedInWatcher` extending `BaseWatcher`. Key discovery: `BaseWatcher` has two abstract methods (`check_for_updates` and `create_action_file`) — added a no-op stub for `create_action_file` since the LinkedIn watcher only processes existing action files, not creates new inbox ones. All 7 tests pass. Committed as cd2e84a.

## Outcome

- Impact: LinkedIn watcher polls Pending_Approval/ for FILE_linkedin-*.md files with type=linkedin_post and status=approved, publishes via LinkedInServer, moves to Done/, and writes audit log entry to Logs/audit.json. Emergency stop, duplicate prevention, and API error resilience all implemented.
- Tests: 7/7 PASSED (test_processes_approved_post, test_skips_pending_post, test_skips_non_linkedin_files, test_emergency_stop_blocks_posting, test_no_duplicate_post_if_in_done, test_api_error_leaves_file_in_pending, test_audit_log_written_on_success)
- Files: src/watchers/linkedin_watcher.py (created), tests/test_linkedin_watcher.py (pre-existing, now passes)
- Next prompts: Task 4 (Complexity Scorer), Task 5 (Generate-Plan Skill), Task 6 (Wire LinkedIn Watcher into Orchestrator)
- Reflection: The BaseWatcher abstract method `create_action_file` was not mentioned in the task description — required a read of the base class to discover and add the stub. Always check abstract methods when subclassing.

## Evaluation notes (flywheel)

- Failure modes observed: First run failed with TypeError (abstract method not implemented); discovered by reading base class
- Graders run and results (PASS/FAIL): uv run pytest tests/test_linkedin_watcher.py -v → 7 PASSED
- Prompt variant (if applicable): none
- Next experiment: Wire watcher into run_all_watchers.py orchestrator (Task 6)
